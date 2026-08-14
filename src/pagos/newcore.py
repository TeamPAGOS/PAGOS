"""
Core functions for the PAGOS package. The Quantity shorthand `pQ` is included here, as well as
some internal functions/decorators and the framework for regular and fast unit processing.
"""

import pint
from typing import TypeAlias
from collections.abc import Callable
from functools import wraps
from enum import Enum, auto
from numpy.random import normal
import operator


#    ┏━┓╻ ╻┏━┓┏┓╻╺┳╸╻╺┳╸╻ ╻         ┏━┓┏━╸┏━╸╻┏━┓╺┳╸┏━┓╻ ╻   ┏━┓╻ ╻┏━┓╺┳╸┏━╸┏┳┓
#    ┃┓┃┃ ┃┣━┫┃┗┫ ┃ ┃ ┃ ┗┳┛   ╺╋╸   ┣┳┛┣╸ ┃╺┓┃┗━┓ ┃ ┣┳┛┗┳┛   ┗━┓┗┳┛┗━┓ ┃ ┣╸ ┃┃┃
#    ┗┻┛┗━┛╹ ╹╹ ╹ ╹ ╹ ╹  ╹          ╹┗╸┗━╸┗━┛╹┗━┛ ╹ ╹┗╸ ╹    ┗━┛ ╹ ┗━┛ ╹ ┗━╸╹ ╹

"""
General way this works:
When we are not in fast mode, creating a PAGOS quantity with pQ(...) will create a more-or-less regular Pint quantity.
However, every time a mathematical operator is called, the conversions (in the case of ADD operators) or combinations
(in the case of MULTIPLY operators) of the units are *cached*.

When we are in fast mode, a different object is created by pQ(...), namely a FastPAGOSQuantity.
The cached combinations/conversions are retrieved whenever the operations which were stored by PAGOSQuantity are called!
Note that this absolutely does not work if any new operations (i.e. conversions which have not been cached) are run - in
fast mode, all operations must be repeated. This is therefore useful only for scenarios such as Monte Carlo analysis, 
where repeated operations are the only thing that can happen!

The way this works in practice is that FastPAGOSQuantity will actually extend float, but overwrite its operation methods
with decorated functions - the decorator in question is @fastpagosbinop. This wrapper handles conversions as quickly as
possible, more or less lifting code directly from the Pint source, but skipping steps like interpreting units as strings
etc., as the information about units before and after the operation are stored in the cache.
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


class CatchConvert(pint.UnitRegistry.Quantity):
    # pairs of
    #   HASH(a units, b units, operation kind) : (conversion function, result units)
    # or, for comparison operators:
    #   HASH(a units, b units, operation kind) : conversion function
    conversions = {}

    # pairs of
    #   HASH(a units, b units, operation kind) : result units
    mult_combis = {}

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


class PAGOSQuantity:
    """
    Regular Pint Quantity wrapper which stores conversions and unit combinations in a cache.
    """

    units_cache = {}

    def __new__(cls, value, units=None):
        inst = object.__new__(cls)
        inst.value = value
        # cache system to make sure strings are not redundantly parsed into UnitsContainer objects
        if isinstance(units, str):
            if units in PAGOSQuantity.units_cache:
                inst.units = PAGOSQuantity.units_cache[units]
            else:
                inst.units = ureg._parse_units_as_container(units)
                PAGOSQuantity.units_cache[units] = inst.units
        elif isinstance(units, pint.util.UnitsContainer):
            inst.units = units
        else:
            raise NotImplementedError("Type of units passed in is not implemented")
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
                    # case for addition and subtraction
                    if operation_kind in {OperationKind.ADD, OperationKind.SUBTRACT}:
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
                        # no conversion necessary as exponent must be dimensionless
                        return PAGOSQuantity(
                            func(self.value, operand_value), self.units**operand_value
                        )
                    # case for comparison:
                    elif operation_kind == OperationKind.COMPARATIVE:
                        # in Pint, __eq__ converts the FIRST operand if necessary, unlike __add__/__sub__, which
                        # convert the SECOND operand. This can get a bit tricky to keep track of, so be careful!
                        conversion_func = CatchConvert.conversions[id]
                        converted_self_value = conversion_func(self.value)
                        return func(converted_self_value, operand_value)

                # if we are not in fast mode, store the conversion in a cache uder the hash key
                else:
                    # create Pint Quantity objects out of the values and units
                    selfQ = CatchConvert(self.value, self.units)
                    operandQ = CatchConvert(operand_value, operand_units)
                    # case for addition and subtraction
                    if operation_kind in {OperationKind.ADD, OperationKind.SUBTRACT}:
                        # perform Pint addition/subtraction, which does conversions automatically
                        resultQ = func(selfQ, operandQ)
                        # if a conversion didn't happen, store identity function
                        if not (cf := CatchConvert.current_conversion_register):
                            cf = lambda x: x
                        # otherwise store the conversion
                        CatchConvert.conversions[id] = (
                            cf,
                            resultQ._units,
                        )
                        CatchConvert.current_conversion_register = None
                        return PAGOSQuantity(resultQ._magnitude, resultQ._units)
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
                        return PAGOSQuantity(resultQ._magnitude, resultQ._units)
                    # case for exponentiation:
                    elif operation_kind == OperationKind.EXPONENTIAL:
                        # no conversion necessary as exponent must be dimensionless
                        resultQ = func(selfQ, operandQ)
                        return PAGOSQuantity(resultQ._magnitude, resultQ._units)
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
                        return resultbool

                # TODO: Others such as delta-conversions (e.g. converting degC to K), modulo conversions etc.

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
            selfQ = CatchConvert(self.value, self.units)
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


# set up UnitRegistry class that will create Quantity objects from PAGOSQuantity type
class PAGOSRegistry(pint.registry.GenericUnitRegistry[PAGOSQuantity, pint.Unit]):
    """
    Default `UnitRegistry` from which all quantities dealt with by PAGOS should be derived.
    """

    Quantity: TypeAlias = PAGOSQuantity
    Unit: TypeAlias = pint.Unit


# two unit registries must exist, so that the different TypeAliases to Quantity are accessible
# (see https://pint.readthedocs.io/en/stable/advanced/custom-registry-class.html)
ureg = PAGOSRegistry()

# global variable controlling whether or not PAGOSQuantity or FastPAGOSQuantity instances will
# be created when PAGOSQuantityFactory(...) is called (see that class below)
_FAST_CALCULATIONS = False


def _set_fast(value: bool):
    global _FAST_CALCULATIONS
    _FAST_CALCULATIONS = value


def _are_calculations_fast():
    return _FAST_CALCULATIONS


# shorthand alias
def pQ(value, units):
    """
    Generates a unit-aware, MC-capable quantity.
    Usage:
    ```
    >>> my_quantity = pQ(5, 'm/s')
    <Quantity(5, 'meter / second')>
    ```
    """
    return PAGOSQuantity(value, units)


#    ┏┳┓┏━┓┏┓╻╺┳╸┏━╸   ┏━╸┏━┓┏━┓╻  ┏━┓   ┏━┓╻ ╻┏━┓╺┳╸┏━╸┏┳┓
#    ┃┃┃┃ ┃┃┗┫ ┃ ┣╸    ┃  ┣━┫┣┳┛┃  ┃ ┃   ┗━┓┗┳┛┗━┓ ┃ ┣╸ ┃┃┃
#    ╹ ╹┗━┛╹ ╹ ╹ ┗━╸   ┗━╸╹ ╹╹┗╸┗━╸┗━┛   ┗━┛ ╹ ┗━┛ ╹ ┗━╸╹ ╹
"""
TODO Better documentation of how the PAGOSCalculator.unitaware and PAGOSCalculator.mc_possible work.
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
            if self.enable_mc:
                self.enable_mc = False
                reset_tag = True

            ret = func(self, *args, **kwargs)

            if reset_tag:
                self.enable_mc = True
                reset_tag = False

            if self.enable_mc:
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

        self.enable_mc = True

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
                result = func(
                    *(pQ(arg, unit) for unit, arg in zip(default_units_in, args)),
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
