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
from pint.facets.nonmultiplicative.definitions import (
    OffsetConverter as _PintOffsetConverter,
)
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

        # Here we deal with offset units (e.g. degC -> K).
        # This should really only happen with single units, as compound units
        # (like degC / s) should be converted automatically to delta counterparts.
        # If there are any problems here, further investigation will be necessary.
        if convfac == 1:
            try:
                converter = self._REGISTRY._units[str(self.units)].converter
                if isinstance(converter, _PintOffsetConverter):

                    def conv_func(x):
                        return converter.to_reference(x, False)
                else:

                    def conv_func(x):
                        return x
            except KeyError:

                def conv_func(x):
                    return x
        else:

            def conv_func(x):
                return x * convfac

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
                            # perform conversion of operand
                            converted_operand = self._ext_to(
                                operand_value, operand_units, self.units, id=id, pcid=id
                            )

                            return PAGOSQuantity(
                                func(self.value, converted_operand.value),
                                converted_operand.units,
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
                            # perform conversion of operand
                            # (same as in ADDITIVE)
                            converted_operand = self._ext_to(
                                operand_value, operand_units, self.units, id=id, pcid=id
                            )
                            return func(self.value, converted_operand.value)
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

                    # if there are non-multiplicative units (e.g. degC), we automatically replace these
                    # with their delta-equivalents (NOTE: here by subtracting zero, perhaps not the most
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
                        # perform conversion of operand
                        # during PAGOSQuantity.to(), CatchConvert.to() is called and the operation is cached
                        converted_operand = PAGOSQuantity(
                            operandQ.magnitude, operandQ._units
                        ).to(selfQ._units, id=id, pcid=id)
                        converted_operandQ = ccreg.Quantity(
                            converted_operand.value, converted_operand.units
                        )
                        # result requires no conversion as this has already been done
                        resultQ = func(selfQ, converted_operandQ)
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
                        # perform conversion of operand
                        # during PAGOSQuantity.to(), CatchConvert.to() is called and the operation is cached
                        # (same done here as in ADDITIVE)
                        converted_operand = PAGOSQuantity(
                            operandQ.magnitude, operandQ._units
                        ).to(selfQ._units, id=id, pcid=id)
                        converted_operandQ = ccreg.Quantity(
                            converted_operand.value, converted_operand.units
                        )
                        resultbool = func(selfQ, converted_operandQ)
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
                            f"\nWARNING: While running your function, arithmetic involving non-multiplicative units came up:\n\t{unchanged_selfQ:~P} {op_as_str(func.__name__)} {unchanged_operandQ:~P}.\nThis is technically ambiguous, and PAGOS will replace the offending units with their delta-counterparts:\n\t{selfQ:~P} {op_as_str(func.__name__)} {operandQ:~P} = {resultQ:~P}.\nPlease check that this is the intended behaviour of your function!\nTo disable this warning, run: `set_warn_nonmult(False)` before your code.\n"
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

    def _ext_to(self, a_value, a_units, b_units, id=None, pcid=None, *contexts):
        """
        External variant of to() function, only to be used in fast mode and only internally!
        Does not have ctx_kwargs argument (unlike to()), and really only exists so that we can
        use to() on non-PAGOSQuantity arguments (like 5% + 3 = 3.05, which has one unit-imbued
        argument and one float. The float has no .units attribute so we can't call
        `<5% object>.to(3.units)`. Instead, we use `_ext_to(5, UnitsContainer({'%':1}), None)`.
        """
        if not id:
            id = hash((a_units, b_units, *contexts))
        if not pcid:
            preconvert_id = hash((a_units, b_units))
        else:
            preconvert_id = pcid
        try:
            # pre-conversion of PAGOS-specific units
            pre_transformation_chain = CatchConvert.pre_transforms[preconvert_id]
            # perform pre-transformations from PAGOSUnits
            for tr in pre_transformation_chain:
                a_value = tr(ccreg, a_value)
            conversion_func, return_units = CatchConvert.conversions_on_to_call[id]
            return PAGOSQuantity(conversion_func(a_value), return_units)
        except KeyError:
            raise KeyError(
                f"Conversion {(a_units, b_units, *contexts)} not found in cache"
            )

    # x.to(u) converts x to units u
    def to(self, other, id=None, pcid=None, *contexts, **ctx_kwargs):
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

        # NOTE: the following manual-entry id and pcid statements are also basically only
        # here because of the additive fast PAGOS binary operations. Because these
        # operations have to sometimes expect non-PAGOS objects like floats as operands,
        # it means that the hashing of units etc. is not that simple. We bypass this by
        # forcing an id (the same as the id created in fastpagosbinop()) as the cache key,
        # instead of generating it inside to(). This assumes, among other things, that
        # ctx_kwargs will NOT be relevant if to() is called from inside __add__. I think
        # this is an okay assumption, as calling __add__(a, b) is actually calling a + b,
        # which by construction doesn't accept kwargs at all. Nevertheless if anything
        # goes wrong here, then *check* that this is working as intended!

        # If we need to revert back to what we had before, delete `if not id:` and
        # `if not pcid:`, but keep the code that is inside them! Delete the whole else
        # statement, though.

        if not id:
            id = hash((self.units, other, *contexts))

        if not pcid:
            try:
                preconvert_id = hash((self.units, other, ctx_kwargs["gas"]))
            except KeyError:
                preconvert_id = hash((self.units, other))
        else:
            preconvert_id = pcid

        if _are_calculations_fast():
            try:
                # pre-conversion of PAGOS-specific units
                pre_transformation_chain = CatchConvert.pre_transforms[preconvert_id]
                # perform pre-transformations from PAGOSUnits
                selfvalue = self.value
                for tr in pre_transformation_chain:
                    selfvalue = tr(ccreg, selfvalue)
                conversion_func, return_units = CatchConvert.conversions_on_to_call[id]
                return PAGOSQuantity(conversion_func(selfvalue), return_units)
            except KeyError:
                raise KeyError(
                    f"Conversion {(self.units, other, *contexts)} not found in cache"
                )
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
            PAGOS_transformation_chain = []
            bare_PAGOS_transformation_chain = []
            other_units_replacements = []
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
                        if (
                            gas_str not in ["gas", "g"]
                            and "_" + gas_str not in str(other)
                            and "_gas" not in str(other)
                        ):
                            raise ValueError(
                                f"Tried to convert a quantity of one gas ({gas_str}) to another ({str(other)})."
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
                                    transformation, bare_transformation = (
                                        PAGOSTransformations[
                                            hash(
                                                (
                                                    str(u.dimensionality),
                                                    str(to_compare_new.dimensionality),
                                                )
                                            )
                                        ][2:]
                                    )
                                    # store the transformation of a PAGOSUnit onto the transformation chain
                                    PAGOS_transformation_chain.append(transformation)
                                    bare_PAGOS_transformation_chain.append(
                                        bare_transformation
                                    )

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
            # Save the BARE transformation chain into a cache.
            # This is so that the pure functional relations between PAGOS units are saved,
            # to be recalled when we are in fast calculations mode (don't want to be dealing
            # with multiplying by expensive unit objects on calculation)
            CatchConvert.pre_transforms[preconvert_id] = bare_PAGOS_transformation_chain

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
            # otherwise store the conversion and resultant output units
            CatchConvert.conversions_on_to_call[id] = (cf, resultQ._units)
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

    def make_mcmethod(self, func: Callable | NotImplementedError, dist_std: float):
        """
        Makes a function an MC-aware method of PAGOSCalculator
        """
        if not isinstance(func, NotImplementedError):

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
                return result.to(units_out)

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
