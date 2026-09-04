"""
Core functions for the PAGOS package. The Quantity shorthand `pQ` is included here, as well as
some internal functions/decorators and the framework for regular and fast unit processing.
"""

from collections.abc import Callable
from enum import Enum, auto
from functools import wraps, reduce
from typing import TypeAlias
from operator import mul as opmul, truediv as opdiv

import pint
from numpy.random import normal

from pagos.newunits import PAGOSDimPatterns, PAGOSDims, PAGOSTransformations, PAGOSUnits

#    ┏━┓╻ ╻┏━┓┏┓╻╺┳╸╻╺┳╸╻ ╻         ┏━┓┏━╸┏━╸╻┏━┓╺┳╸┏━┓╻ ╻   ┏━┓╻ ╻┏━┓╺┳╸┏━╸┏┳┓
#    ┃┓┃┃ ┃┣━┫┃┗┫ ┃ ┃ ┃ ┗┳┛   ╺╋╸   ┣┳┛┣╸ ┃╺┓┃┗━┓ ┃ ┣┳┛┗┳┛   ┗━┓┗┳┛┗━┓ ┃ ┣╸ ┃┃┃
#    ┗┻┛┗━┛╹ ╹╹ ╹ ╹ ╹ ╹  ╹          ╹┗╸┗━╸┗━┛╹┗━┛ ╹ ╹┗╸ ╹    ┗━┛ ╹ ┗━┛ ╹ ┗━╸╹ ╹

"""
General way this works:
When we are not in fast mode, creating a PAGOS quantity with pQ(...) will create a more-or-less regular Pint quantity.
However, every time a mathematical operator is called, the conversions (in the case of ADD operators) or combinations
(in the case of MULTIPLY operators) of the units are *cached*.

When we are in fast mode, the cached conversions/combinations are recalled.
"""


# Enum for different kinds of operation - required for conversion/arithmetic caching (see wrappers and classes below)
class OperationKind(Enum):
    """
    Enum for operation kinds.
    """

    ADD = auto()
    SUBTRACT = auto()
    MULTIPLY = auto()
    LDIVIDE = auto()
    RDIVIDE = auto()
    EXPONENTIAL = auto()
    COMPARATIVE = auto()


# some resources for warning messages when nonmultiplicative arithmetic is detected
def op_as_str(opname):
    op_str_dict = {
        "__add__": "+",
        "__sub__": "-",
        "__mul__": "*",
        "__truediv__": "/",
        "__pow__": "^",
    }
    try:
        return op_str_dict[opname]
    except KeyError:
        return opname


warn_nonmult = True


def set_warn_nonmult(value):
    global warn_nonmult
    warn_nonmult = value


# TODO rename CatchConvert - it does catch and handle conversions but also acts as the generic class to construct Pint Quantity objects,
# so its functionality is not totally captured by this name.
class CatchConvert(pint.UnitRegistry.Quantity):
    # pairs of
    #   HASH(a units, b units, operation kind) : (conversion function, result units)
    # or, for comparison operators:
    #   HASH(a units, b units, operation kind) : conversion function
    conversions = {}

    # pairs of
    #   HASH(a units, b units, operation kind) : result units
    mult_combis = {}

    # pairs of
    #   HASH(a units, b units, operation kind) : delta-a units
    # for when non-multiplicative units are exponentiated
    exp_transforms = {}

    # pairs of
    # HASH(a units, b units, *contexts) : conversion function
    conversions_on_to_call = {}

    # pairs of
    # HASH(a units, b units, gas) : pre-transforms for PAGOSUnits
    pre_transforms = {}

    # single register to hold the details of the last conversion that happened in
    # _convert_magnitude_not_inplace
    current_conversion_register = None

    # conversions that happen explicitly through _finally_convert_to()
    final_conversions = {}

    def _convert_magnitude_not_inplace(self, other, *contexts, **ctx_kwargs):
        # can potentially get automatically called when operations are performed, not necessarily only when the user calls .to()!
        convfac = self._REGISTRY._get_conversion_factor(self._units, other)

        def conv_func(x):
            return x * convfac
            # TODO THIS WILL NOT WORK WITH NON-MULTIPLICATIVE UNITS!

        # store the unit to be converted, the unit to convert to, and the conversion function in a temporary register
        CatchConvert.current_conversion_register = conv_func

        return super()._convert_magnitude_not_inplace(other, *contexts, **ctx_kwargs)

    def to(self, other, *contexts, **ctx_kwargs):
        return super().to(other, *contexts, **ctx_kwargs)


class PAGOSQuantity:
    """
    Regular Pint Quantity wrapper which stores conversions and unit combinations in a cache.
    """

    units_cache = {}

    def __new__(cls, value, units=None, gas=None):
        inst = object.__new__(cls)

        # cache system to make sure strings are not redundantly parsed into UnitsContainer objects
        id = hash((units, gas))
        if isinstance(units, str):
            if id in PAGOSQuantity.units_cache:
                inst.units = PAGOSQuantity.units_cache[id]
            else:
                inst.units = ureg._parse_units_as_container(units)
                PAGOSQuantity.units_cache[id] = inst.units
        elif isinstance(units, pint.util.UnitsContainer):
            inst.units = units
        else:
            raise NotImplementedError("Type of units passed in is not implemented")

        # if there are PAGOS units yet to be assigned to a gas, we do that here
        # e.g. if we called PAGOSQuantity(5, 'mol_gas', 'He'), we get out PAGOSQuantity(5, 'mol_He')
        if gas:
            for u in inst.units:
                if str(ureg.Unit(u).dimensionality) in PAGOSDims:
                    # replace "_g" or "_gas" with "_<actual gas string", e.g. "_He"
                    stripped_unit = u.replace("_gas", "_" + gas).replace(
                        "_g", "_" + gas
                    )
                    inst.units = inst.units * ureg._parse_units_as_container(
                        "(" + stripped_unit + "/" + u + f")^{inst.units[u]}"
                    )
            PAGOSQuantity.units_cache[id] = inst.units

        if isinstance(value, PAGOSQuantity):
            selfQ = value
            pint_representation = ccreg.Quantity(selfQ.value, selfQ.units)
            converted_pint_repr = pint_representation.to(inst.units)
            value = converted_pint_repr.magnitude
        inst.value = value
        return inst

    # wrapper to convert binary arithmetic operators __add__ (+), __mul__ (*), etc. into ones that can access cached conversions
    def fastpagosbinop(operation_kind: OperationKind):
        """
        Decorator which takes in a binary arithmetic operation (e.g. __add__, __mul__ etc.) and returns the same function which
        can access cached conversions from the `CatchConvert` class.
        """

        def _fastpagosbinop(func):
            @wraps(func)
            def wrapper(self, operand):
                # get operand units and value, or None for units if the operand is a float/int
                if isinstance(operand, PAGOSQuantity):
                    operand_value = operand.value
                    operand_units = operand.units
                else:
                    operand_value = operand
                    operand_units = None

                # hash the operation - this will be used as a key for caching
                id = hash((self.units, operand_units, operation_kind))

                # if we are in fast mode, use the hash key to obtain an already cached conversion, apply to operand
                # and return the value
                if _are_calculations_fast():
                    try:
                        # case for addition and subtraction
                        if operation_kind in {
                            OperationKind.ADD,
                            OperationKind.SUBTRACT,
                        }:
                            conversion_func, result_units = CatchConvert.conversions[id]
                            converted_operand_value = conversion_func(operand_value)

                            return PAGOSQuantity(
                                func(self.value, converted_operand_value), result_units
                            )
                        # case for multiplication
                        elif operation_kind in {
                            OperationKind.MULTIPLY,
                            OperationKind.LDIVIDE,
                            OperationKind.RDIVIDE,
                        }:
                            combined_units = CatchConvert.mult_combis[id]
                            return PAGOSQuantity(
                                func(self.value, operand_value), combined_units
                            )
                        # case for exponentiation:
                        elif operation_kind == OperationKind.EXPONENTIAL:
                            # transform any non-multiplicative units into delta-units
                            transformed_self_units = CatchConvert.exp_transforms[id]
                            # no conversion necessary as exponent must be dimensionless
                            return PAGOSQuantity(
                                func(self.value, operand_value),
                                transformed_self_units**operand_value,
                            )
                        # case for comparison:
                        elif operation_kind == OperationKind.COMPARATIVE:
                            # in Pint, __eq__ converts the FIRST operand if necessary, unlike __add__/__sub__, which
                            # convert the SECOND operand. This can get a bit tricky to keep track of, so be careful!
                            conversion_func = CatchConvert.conversions[id]
                            converted_self_value = conversion_func(self.value)
                            return func(converted_self_value, operand_value)
                    except KeyError:
                        print(
                            f"Conversion {(self.units, operand_units, operation_kind)} not found in cache"
                        )
                        raise

                # if we are not in fast mode, store the conversion in a cache uder the hash key
                else:
                    # create Pint Quantity objects out of the values and units
                    selfQ = ccreg.Quantity(self.value, self.units)
                    operandQ = ccreg.Quantity(operand_value, operand_units)

                    # if there are non-multiplicative units (e.g. degC), we automatically convert these
                    # to their delta-equivalents (NOTE: here by subtracting zero, perhaps not the most
                    # efficient thing to do), and warning the user
                    unchanged_selfQ = selfQ
                    unchanged_operandQ = operandQ
                    warn_about_nm_units = False
                    if unchanged_selfQ._get_non_multiplicative_units():
                        warn_about_nm_units = True
                        selfQ = unchanged_selfQ - ccreg.Quantity(0, selfQ._units)
                    if unchanged_operandQ._get_non_multiplicative_units():
                        warn_about_nm_units = True
                        operandQ = unchanged_operandQ - ccreg.Quantity(
                            0, operandQ._units
                        )

                    # case for addition and subtraction
                    if operation_kind in {OperationKind.ADD, OperationKind.SUBTRACT}:
                        # perform pre-conversion of PAGOSUnits
                        # NOTE: this is kind of dumb because we have to convert BACK into a PAGOSQuantity first - perhaps there
                        # is some way we can do this before selecting the operation kind - on the other hand, this may cause problems
                        # in the operations that do not require pre-conversion!
                        preconverted_operand = PAGOSQuantity(
                            operandQ.magnitude, operandQ._units
                        ).to(self.units)
                        preconverted_operandQ = ccreg.Quantity(
                            preconverted_operand.value, preconverted_operand.units
                        )
                        # perform Pint addition/subtraction, which does conversions automatically
                        # with ccreg.context("pc"):
                        resultQ = func(selfQ, preconverted_operandQ)
                        # if a conversion didn't happen, store identity function
                        if not (cf := CatchConvert.current_conversion_register):
                            cf = lambda x: x
                        # otherwise store the conversion
                        CatchConvert.conversions[id] = (
                            cf,
                            resultQ._units,
                        )
                        CatchConvert.current_conversion_register = None
                        ret = PAGOSQuantity(resultQ._magnitude, resultQ._units)
                    # case for multiplication
                    elif operation_kind in {
                        OperationKind.MULTIPLY,
                        OperationKind.LDIVIDE,
                        OperationKind.RDIVIDE,
                    }:
                        # perform Pint multiplication/division, which does unit combination automatically
                        resultQ = func(selfQ, operandQ)
                        # store the unit combination
                        CatchConvert.mult_combis[id] = resultQ._units
                        ret = PAGOSQuantity(resultQ._magnitude, resultQ._units)
                    # case for exponentiation:
                    elif operation_kind == OperationKind.EXPONENTIAL:
                        # need to store any transformations of non-multiplicative units to deltas
                        # e.g. degC^2 -> delta_degC^2
                        CatchConvert.exp_transforms[id] = selfQ._units
                        # no conversion necessary as exponent must be dimensionless
                        resultQ = func(selfQ, operandQ)
                        ret = PAGOSQuantity(resultQ._magnitude, resultQ._units)
                    # case for comparison:
                    elif operation_kind == OperationKind.COMPARATIVE:
                        # perform Pint comparison, which does conversions automatically
                        resultbool = func(selfQ, operandQ)
                        # if a conversion didn't happen, store identity function
                        if not (cf := CatchConvert.current_conversion_register):
                            cf = lambda x: x
                        # otherwise store the conversion (of selfQ to operandQ's units)
                        CatchConvert.conversions[id] = cf
                        CatchConvert.current_conversion_register = None
                        ret = resultbool

                    # a bit confusing: warn_about_nm_units means "is there anything to warn about?" and warn_nonmult
                    # means "does the user want to be warned at all?"!
                    if warn_about_nm_units and warn_nonmult:
                        print(
                            f"\nWARNING: While running your function, arithmetic involving non-multiplicative units came up:\n\t{unchanged_selfQ:~P} {op_as_str(func.__name__)} {unchanged_operandQ:~P}.\nThis is technically ambiguous, and PAGOS will convert the offending units to their delta-counterparts:\n\t{selfQ:~P} {op_as_str(func.__name__)} {operandQ:~P} = {resultQ:~P}.\nPlease check that this is the intended behaviour of your function!\nTo disable this warning, run: `set_warn_nonmult(False)` before your code.\n"
                        )

                    return ret

            return wrapper

        return _fastpagosbinop

    # arithmetic operators
    @fastpagosbinop(OperationKind.ADD)
    def __add__(self, other):
        return self + other

    @fastpagosbinop(OperationKind.ADD)
    def __radd__(self, other):
        return self + other

    @fastpagosbinop(OperationKind.SUBTRACT)
    def __sub__(self, other):
        return self - other

    @fastpagosbinop(OperationKind.SUBTRACT)
    def __rsub__(self, other):
        return other - self

    @fastpagosbinop(OperationKind.MULTIPLY)
    def __mul__(self, other):
        return self * other

    @fastpagosbinop(OperationKind.MULTIPLY)
    def __rmul__(self, other):
        return self * other

    @fastpagosbinop(OperationKind.LDIVIDE)
    def __truediv__(self, other):
        return self / other

    @fastpagosbinop(OperationKind.RDIVIDE)
    def __rtruediv__(self, other):
        # there is a separate OperationKind for right divide, because the unit order matters
        # for example, 3 m / 2 s with right divide should cache
        #       (s, m) : m/s
        # and not
        #       (m, s) : m/s
        # because the latter, in right divide, corresponds to 2 s / 3 m -> ...m/s, which is wrong!
        return other / self

    @fastpagosbinop(OperationKind.EXPONENTIAL)
    def __pow__(self, other):
        # exponentiation is identical and saves no information
        # the reason we do this is because the unit transformation is dependent on the VALUE of the exponent
        # whereas +, -, *, / etc. are only UNIT-dependent! If we cached every __pow__ call, then during a fit
        # procedure or MC procedure, the value would change every time and the cache would basically never be
        # hit!
        # TODO allow for caching but warn user?
        return self**other

    @fastpagosbinop(OperationKind.EXPONENTIAL)
    def __rpow__(self, other):
        return other**self  # noqa # IF AN EXCEPTION IS THROWN HERE, NEED TO LOOK INTO HOW TO IMPLEMENT RPOW!

    # comparison operators
    @fastpagosbinop(OperationKind.COMPARATIVE)
    def __eq__(self, value):
        return self == value

    @fastpagosbinop(OperationKind.COMPARATIVE)
    def __gt__(self, value):
        return self > value

    @fastpagosbinop(OperationKind.COMPARATIVE)
    def __lt__(self, value):
        return self < value

    @fastpagosbinop(OperationKind.COMPARATIVE)
    def __ge__(self, value):
        return self >= value

    @fastpagosbinop(OperationKind.COMPARATIVE)
    def __le__(self, value):
        return self <= value

    def _finally_convert_to(self, other):
        """
        Wrapper around to(), only to be called at the end of @unit_aware, instead of every time a Pint operation calls Pint().
        Units and converted units are cached.
        Otherwise, functions exactly the same as to().
        """
        id = hash((self.units, other))
        if _are_calculations_fast():
            conversion_func = CatchConvert.final_conversions[id]
            converted_self_value = conversion_func(self.value)
            return PAGOSQuantity(converted_self_value, other)
        else:
            selfQ = ccreg.Quantity(self.value, self.units)
            resultQ = selfQ.to(other)
            conversion_func = CatchConvert.current_conversion_register

            CatchConvert.final_conversions[id] = conversion_func
            return PAGOSQuantity(resultQ._magnitude, resultQ._units)

    # string and representation
    def __repr__(self):
        if isinstance(self.value, int):
            return f"<PAGOSQuantity({self.value}, '{self.units})>"
        elif isinstance(self.value, float):
            return f"<PAGOSQuantity({self.value:.9}, '{self.units}')>"

    def __str__(self):
        if isinstance(self.value, int):
            return f"{self.value} {self.units}"
        elif isinstance(self.value, float):
            return f"{self.value:.9} {self.units}"

    # unary operators
    def __abs__(self):
        return PAGOSQuantity(abs(self.value), self.units)

    def __neg__(self):
        return PAGOSQuantity(-self.value, self.units)

    # numpy operators
    def __array_ufunc__(self, ufunc, method, *inputs, **kwargs):
        # TODO this will be quite slow - in future numpy functions should work as well as
        # the normal arithmetic functions with caching!!!

        # convert the input PagosQuantity objects into regular Pint Quantity objects
        qs_in = tuple(ccreg.Quantity(inpq.value, inpq.units) for inpq in inputs)
        # allow Pint to perform calculation on Pint Quantity objects
        result = pint.facets.numpy.quantity.NumpyQuantity.__array_ufunc__(
            self, ufunc, method, *qs_in, **kwargs
        )
        # cache system here?
        ...
        # return PAGOSQuantity result
        return PAGOSQuantity(result._magnitude, result._units)

    # x.to(u) converts x to units u
    def to(self, other, *contexts, **ctx_kwargs):
        # cache system to make sure strings are not redundantly parsed into UnitsContainer objects
        if isinstance(other, str):
            if other in PAGOSQuantity.units_cache:
                other = PAGOSQuantity.units_cache[other]
            else:
                other = ureg._parse_units_as_container(str_other := other)
                PAGOSQuantity.units_cache[str_other] = other
        elif isinstance(other, pint.util.UnitsContainer):
            pass
        else:
            raise NotImplementedError("Type of units passed in is not implemented")

        id = hash((self.units, other, *contexts))
        if _are_calculations_fast():
            try:
                conversion_func = CatchConvert.conversions_on_to_call[id]
                return PAGOSQuantity(conversion_func(self), other)
            except KeyError:
                print(f"Conversion {(self.units, other, *contexts)} not found in cache")
                raise
        else:
            """
            pre-conversion of PAGOS-specific units; this happens if we have, for example,
            mole_gas / kg -> gram_gas / kg
            Even though regular Pint contexts would work for this, there are two issues:
            1) Context transformations work on their own, but not when in compound units
               like A / kg -> B / kg,
            2) Transformations through contexts are hard to intercept with CatchConvert.
            So we handle it here instead
            """

            if any([u in PAGOSDims for u in ccreg.get_dimensionality(self.units)]):
                # match PAGOS-specific units across own units and other units
                # expand out other into its factors

                _otherunits = list(other.copy().items())
                _otherunits_factor_sequence = [
                    [
                        ureg._parse_units_as_container(pair[0])
                        for i in range(int(pair[1]))
                    ]
                    # this bit deals with non-integer powers
                    + (
                        [
                            ureg._parse_units_as_container(
                                pair[0] + f"^{pair[1] - int(pair[1])}"
                            )
                        ]
                        if pair[1] - int(pair[1]) != 0
                        else []
                    )
                    for pair in _otherunits
                    if str(ccreg.Unit(pair[0]).dimensionality) in PAGOSDims
                ]
                # flatten and turn into Unit objects (instead of UnitsContainer)
                _otherunits_factor_sequence = [
                    ccreg.Unit(x) for xs in _otherunits_factor_sequence for x in xs
                ]

                PAGOS_transformation_chain = []
                other_units_replacements = []
                # store requisite transformations
                # quite complicated as has to search through combinations of units as well
                # as single ones on the right hand side
                for _u in [
                    __u
                    for __u in self.units.items()
                    if str(ccreg.get_dimensionality(__u[0])) in PAGOSDims
                ]:
                    u = ccreg.Unit(_u[0] + f"^{_u[1]}")

                    # extract the gas string on the unit
                    gas_str = reduce(
                        lambda acc, pat: acc.replace(pat[0], ""),
                        PAGOSDimPatterns,
                        str(u.dimensionality).removesuffix("]"),
                    )

                    # raise error if attempting to convert from one gas to another
                    if "gas" in ctx_kwargs:
                        if gas_str not in ["gas", "g"] and ctx_kwargs["gas"] != gas_str:
                            raise ValueError(
                                f"Tried to convert a quantity of one gas ({gas_str}) to another ({ctx_kwargs['gas']})."
                            )
                    else:
                        if gas_str not in ["gas", "g"] and "_" + gas_str not in str(
                            other
                        ):
                            raise ValueError(
                                f"Tried to convert a quantity of one gas ({gas_str}) to another ({ctx_kwargs['gas']})."
                            )

                    i, j, bincount = 0, 0, 1
                    l = len(_otherunits_factor_sequence)
                    while j < l:
                        max_i = sum([2 ** (l - k) for k in range(j + 1)])
                        while i < max_i:
                            binselect = [
                                i
                                for i, x in enumerate(list(bin(bincount)[2:]))
                                if int(x) == 1
                            ]
                            # to_compare = product of selected single units
                            to_compare = reduce(
                                opmul,
                                [_otherunits_factor_sequence[x] for x in binselect],
                                ccreg.Unit(""),
                            )

                            # check for "_gas" or "_g" suffixes on to_compare's units
                            # if they exist, we try to infer that the gas is the same as that provided
                            # in self.
                            try:
                                to_compare_new = reduce(
                                    opmul,
                                    (
                                        ccreg.Unit(
                                            x.replace("_gas", "_" + gas_str).replace(
                                                "_g", "_" + gas_str
                                            )
                                            + f"^{to_compare._units[str(x)]}"
                                        )
                                        for x in to_compare._units
                                    ),
                                    ccreg.Unit(""),
                                )
                            except:
                                raise  # TODO deal with exceptions here

                            if to_compare_new.is_compatible_with(u, pc):
                                # pop the factor off of the otherunit sequence
                                # if the conversion is valid, eventually the whole sequence should be popped/
                                # if something remains, a ValueError is raised (see below)
                                for popidx in binselect:
                                    _otherunits_factor_sequence.pop(popidx)
                                other_units_replacements.append(
                                    (to_compare, to_compare_new)
                                )
                                # if the dimensionalities are actually different, perform a transformation
                                if to_compare_new.dimensionality != u.dimensionality:
                                    transformation = PAGOSTransformations[
                                        hash(
                                            (
                                                str(u.dimensionality),
                                                str(to_compare_new.dimensionality),
                                            )
                                        )
                                    ][2]
                                    # store the transformation of a PAGOSUnit onto the transformation chain
                                    PAGOS_transformation_chain.append(transformation)

                                break
                            bincount += 2**i
                            i += 1
                        else:
                            bincount += 1
                            i = 0
                            j += 1
                            continue
                        break
                    else:
                        raise ValueError(
                            "There is a mismatch between PAGOS units (subscripted with _g) on either side of the conversion."
                        )
            # save the transformation chain into a cache
            try:
                pre_transform_id = hash((self.units, other, ctx_kwargs["gas"]))
            except KeyError:
                pre_transform_id = hash((self.units, other))
            CatchConvert.pre_transforms[pre_transform_id] = PAGOS_transformation_chain

            # create Pint Quantity objects out of the value and unit
            selfQ = ccreg.Quantity(self.value, self.units)
            # perform pre-transformations from PAGOSUnits
            for tr in PAGOS_transformation_chain:
                selfQ = tr(ccreg, selfQ)
            # change generic "_g" or "_gas" suffixes to specific ones determined by self
            for pair in other_units_replacements:
                other = other / pair[0]._units * pair[1]._units
            # perform rest of conversion (regular Pint conversions of normal units and prefixes)
            resultQ = selfQ.to(other, *contexts, **ctx_kwargs)
            # if a conversion didn't happen (i.e. units were equal), store identity function
            if not (cf := CatchConvert.current_conversion_register):
                cf = lambda x: x
            # otherwise store the conversion
            CatchConvert.conversions_on_to_call[id] = cf
            CatchConvert.current_conversion_register = None
            # return result
            return PAGOSQuantity(resultQ._magnitude, resultQ._units)


# set up UnitRegistry class that will create Quantity objects from PAGOSQuantity type
class PAGOSRegistry(pint.registry.GenericUnitRegistry[PAGOSQuantity, pint.Unit]):
    """
    Default `UnitRegistry` from which all quantities dealt with by PAGOS should be derived.
    """

    Quantity: TypeAlias = PAGOSQuantity
    Unit: TypeAlias = pint.Unit


# set up UnitRegistry class that will create Quantity objects from CatchConvert type
class CatchConvertRegistry(pint.registry.GenericUnitRegistry[CatchConvert, pint.Unit]):
    """
    `UnitRegistry` for CatchConvert objects. Only to be used internally.
    """

    Quantity: TypeAlias = CatchConvert
    Unit: TypeAlias = pint.Unit


ccreg = CatchConvertRegistry()

"""
THE UNIT REGISTRY

This is the object from which ALL units within PAGOS and with which PAGOS should
interact will come from. If the user defines another UnitRegistry in their program, and then
attempts to use PAGOS, it will fail and throw: "ValueError: Cannot operate with Quantity and
Quantity of different registries."
"""
# unit registry
ureg = PAGOSRegistry()


# initialise units
for key in PAGOSUnits:
    ureg.define(PAGOSUnits[key])
    ccreg.define(PAGOSUnits[key])
pc = pint.Context("pc")
# initialise transformations
for key in PAGOSTransformations:
    tup = PAGOSTransformations[key]
    pc.add_transformation(tup[0], tup[1], tup[2])
ccreg.add_context(pc)

# global variable controlling whether or not PAGOSQuantity or FastPAGOSQuantity instances will
# be created when PAGOSQuantityFactory(...) is called (see that class below)
_FAST_CALCULATIONS = False


def _set_fast(value: bool):
    global _FAST_CALCULATIONS
    _FAST_CALCULATIONS = value


def _are_calculations_fast():
    return _FAST_CALCULATIONS


# shorthand alias
def pQ(value, units, gas=None):
    """
    Generates a unit-aware, MC-capable quantity.
    Usage:
    ```
    >>> my_quantity = pQ(5, 'm/s')
    <Quantity(5, 'meter / second')>
    ```
    """
    return PAGOSQuantity(value, units, gas)


#    ┏┳┓┏━┓┏┓╻╺┳╸┏━╸   ┏━╸┏━┓┏━┓╻  ┏━┓   ┏━┓╻ ╻┏━┓╺┳╸┏━╸┏┳┓
#    ┃┃┃┃ ┃┃┗┫ ┃ ┣╸    ┃  ┣━┫┣┳┛┃  ┃ ┃   ┗━┓┗┳┛┗━┓ ┃ ┣╸ ┃┃┃
#    ╹ ╹┗━┛╹ ╹ ╹ ┗━╸   ┗━╸╹ ╹╹┗╸┗━╸┗━┛   ┗━┛ ╹ ┗━┛ ╹ ┗━╸╹ ╹
"""
TODO Better documentation of how the PAGOSCalculator.unitaware and mc_possible work.
"""


def mc_possible(dist_std: str | float):
    """
    Decorator factory for Monte Carlo utility. The resultant decorator will enable its decorated function to be
    varied according to a normal distribution, corresponding to `dist_std`. If `dist_std` is a float, it
    will be the standard deviation of that normal distribution. If it is a string, it is a key of an internal
    dictionary of pre-defined distributions.\\
    [TODO explain which presets there are]

    :param dist_std: Standard deviation of the normal distribution about which the target function will be varied,
    or key corresponding to pre-defined distribution.
    :type data: str
    :return: Decorator to make a function MC-aware.
    :rtype: Callable
    """

    def _mc_possible(func):
        """
        Decorates `func` to become MC-aware. When the function is run, the normal distribution supplied by the
        `mc_possible` factory is used whenever `func` is called to vary its output.
        """

        @wraps(func)
        def wrapper(self, *args, **kwargs):
            reset_tag = False
            if self._mc_enabled:
                self._mc_enabled = False
                reset_tag = True

            ret = func(self, *args, **kwargs)

            if reset_tag:
                self._mc_enabled = True
                reset_tag = False

            if self._mc_enabled:
                if isinstance(dist_std, float):
                    ret = ret * normal(1, dist_std)
                elif isinstance(dist_std, str):
                    ret = self.errfuncs[dist_std](ret)
                else:
                    raise TypeError("Argument dist_std must be str or float")
            return ret

        return wrapper

    return _mc_possible


class PAGOSCalculator:
    """
    Class holding all functions in PAGOS which are unit and MC aware.
    """

    def __init__(self):
        self.errfuncs = {
            "add": lambda base_value: base_value * normal(1, 0.01),
            "mult": lambda base_value: base_value * normal(1, base_value / 100),
            "combi": lambda base_value: base_value * normal(1, 0.001),
        }

        self._mc_enabled = False

    def set_mc(self, value: bool):
        self._mc_enabled = value

    def make_mcmethod(self, func: Callable, dist_std: float):
        """
        Makes a function an MC-aware method of PAGOSCalculator
        """

        def _add_self_argument(func):
            """
            Utility to include add the argument 'self' to the front of a function's signature. ONLY to be used in make_mcmethod.
            """

            def wrapper(self, *args, **kwargs):
                return func(*args, **kwargs)

            return wrapper

        # The func, coming from outside this class, does not have a `self` attribute and therefore must have it created here
        func_with_self = _add_self_argument(func)

        # mc_possible decorates the function, and we set it as an attribute in the class
        method_to_add = mc_possible(dist_std)(func_with_self)
        funcname = func.__name__
        setattr(self.__class__, funcname, method_to_add)
        return getattr(self, funcname)

    def unit_aware(self, default_units_in, units_out):
        """
        Decorator which makes a function unit aware, by setting default units in and units out. The default units are applied to float inputs and the resulting calculation is converted to the units out.
        """
        units_out = ureg._parse_units_as_container(units_out)

        def _unit_aware(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs) -> PAGOSQuantity:
                # if default_units_in is a single string, make sure we just read that and not each individual character of it!
                if isinstance(default_units_in, str):
                    _default_units_in = (default_units_in,)
                else:
                    _default_units_in = default_units_in
                # execute the function with pQ(...) arguments instead of floats
                result = func(
                    *(
                        pQ(arg, unit) if unit is not None else arg
                        for unit, arg in zip(_default_units_in, args)
                    ),
                    **kwargs,
                )
                return result._finally_convert_to(units_out)

            return wrapper

        return _unit_aware

    @mc_possible("add")
    def add_example(self, x1, x2):
        result = x1 + x2
        return result

    @mc_possible("mult")
    def mult_example(self, x1, x2):
        result = x1 * x2
        return result

    @mc_possible("combi")
    def combi_example(self, x1, x2, x3):
        y = self.add_example(x1, x2)
        z = self.mult_example(y, x3)
        return z

    @mc_possible(0.0001)
    def custom_combi_example(self, x1, x2, x3):
        y = self.add_example(x1, x2)
        z = self.mult_example(y, x3)
        return z


pCalc = PAGOSCalculator()
