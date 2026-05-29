from numpy.random import normal
from functools import wraps
from enum import Enum, auto
from tqdm import tqdm
import cProfile
from time import time
from timeit import timeit
from pint import UnitRegistry
import pint
from typing import TypeAlias
from collections.abc import Callable


class OperationKind(Enum):
    """
    Enum for operation kinds.
    """

    ADDITIVE = auto()
    MULTIPLICATIVE = auto()
    DIVISIVE = auto()
    EXPONENTIAL = auto()


# wrapper to convert binary arithmetic operators __add__ (+), __mul__ (*), etc. into ones that can access cached conversions
def fastpagosbinop(operation_kind: OperationKind):
    def _fastpagosbinop(func):
        @wraps(func)
        def wrapper(self, operand):
            if isinstance(operand, FastPAGOSQuantity):
                operand_value = operand.value
                operand_units = operand.units
            else:
                operand_value = operand
                operand_units = None
            if operation_kind == OperationKind.ADDITIVE:
                # additive conversions i.e.
                # an operation a @ b, where a and b have different units but equal dimensions.
                # @ = +, -
                if self.units == operand_units:
                    _sum = func(self.value, operand_value)
                    ret = self.__class__(_sum, self.units)
                else:
                    conv_id = hash((operand_units, self.units))
                    convertedvalue = PAGOSQuantity.conversions[conv_id](operand_value)
                    _sum = func(self.value, convertedvalue)
                    ret = self.__class__(_sum, self.units)
                return ret

            elif (
                operation_kind == OperationKind.MULTIPLICATIVE
                or operation_kind == OperationKind.DIVISIVE
            ):
                # multiplicative conversions i.e.
                # a * b
                conv_id = hash((self.units, operand_units, operation_kind))
                _prod = func(self.value, operand_value)
                try:
                    ret = self.__class__(_prod, PAGOSQuantity.mult_combis[conv_id])
                except KeyError as e:
                    print(
                        f"Error raised due to hash of {(self.units, operand_units, operation_kind)} = {conv_id} not found in cache:\n{PAGOSQuantity.mult_combis}"
                    )
                    raise e
                return ret
            elif operation_kind == OperationKind.EXPONENTIAL:
                # exponential operations i.e.
                # a ** b
                # No conversion necessary as b must be dimensionless
                _power = func(self.value, operand_value)
                return self.__class__(_power, self.units**operand_value)
            else:
                raise NotImplementedError(
                    "The given conversion_kind is not implemented"
                )

            # TODO: Others such as delta-conversions (e.g. converting degC to K), modulo conversions etc.

        return wrapper

    return _fastpagosbinop


class PAGOSQuantity(pint.UnitRegistry.Quantity):
    """
    Regular Pint Quantity wrapper which stores conversions and unit combinations in a cache
    """

    conversions = {}
    mult_combis = {}
    power_changes = {}

    def __new__(cls, value, units=None):
        return super().__new__(cls, value, units)

    def to(self, other=None, *contexts, **ctx_kwargs):

        def conv_func(x):
            return x * self._REGISTRY._get_conversion_factor(self._units, other)
            # return self._REGISTRY.convert(x, self._units, _other)
            # TODO THIS WILL NOT WORK WITH NON-MULTIPLICATIVE UNITS!

        PAGOSQuantity.conversions[hash((self._units, other))] = conv_func
        # TODO this hash as two UnitsContainer objects, make sure it is this way for the FastPAGOSQuantity lookup!
        return super().to(other, *contexts, **ctx_kwargs)

    def __mul__(self, other):
        ret = super().__mul__(other)
        if hasattr(other, "_units"):
            PAGOSQuantity.mult_combis[
                hash((self._units, other._units, OperationKind.MULTIPLICATIVE))
            ] = ret._units
        else:
            PAGOSQuantity.mult_combis[
                hash((self._units, None, OperationKind.MULTIPLICATIVE))
            ] = ret._units
        return ret

    def __truediv__(self, other):
        ret = super().__truediv__(other)
        if hasattr(other, "_units"):
            PAGOSQuantity.mult_combis[
                hash((self._units, other._units, OperationKind.DIVISIVE))
            ] = ret._units
        else:
            PAGOSQuantity.mult_combis[
                hash((self._units, None, OperationKind.DIVISIVE))
            ] = ret._units
        return ret

    def __pow__(self, other):
        # exponentiation is identical and saves no information
        # the reason we do this is because the unit transformation is dependent on the VALUE of the exponent
        # whereas +, -, *, / etc. are only UNIT-dependent! If we cached every __pow__ call, then during a fit
        # procedure or MC procedure, the value would change every time and the cache would basically never be
        # hit!
        return super().__pow__(other)


class FastPAGOSQuantity:
    """
    Special class which performs conversions stored by `PAGOSQuantity` instances.\\
    Useful in Monte Carlo situations where a the same conversion will be required many times over.\\
    Implements its own cache to actually store the units written in by the user, so that
    `pint.UnitRegistry._parse_units_as_container` is called as seldom as possible (otherwise extremely expensive).
    """

    units_cache = {}

    def __new__(cls, value, units=None):
        inst = object.__new__(cls)
        inst.value = value
        # cache system to make sure strings are not redundantly parsed into UnitsContainer objects
        if isinstance(units, str):
            if units in FastPAGOSQuantity.units_cache:
                inst.units = FastPAGOSQuantity.units_cache[units]
            else:
                inst.units = freg._parse_units_as_container(units)
                FastPAGOSQuantity.units_cache[units] = inst.units
        elif isinstance(units, pint.util.UnitsContainer):
            inst.units = units
        else:
            raise NotImplementedError("Type of units passed in is not implemented")
        return inst

    def to(self, other=None, *contexts, **ctx_kwargs):
        # cache system to make sure strings are not redundantly parsed into UnitsContainer objects
        if isinstance(other, str):
            if other in FastPAGOSQuantity.units_cache:
                _other = FastPAGOSQuantity.units_cache[other]
            else:
                _other = freg._parse_units_as_container(other)
                FastPAGOSQuantity.units_cache[other] = _other
        elif isinstance(other, pint.util.UnitsContainer):
            _other = other
        else:
            raise NotImplementedError("Type of units passed in is not implemented")

        # conversion
        if self.units == _other:
            return self
        convertedvalue = PAGOSQuantity.conversions[hash((self.units, _other))](
            self.value
        )
        return FastPAGOSQuantity(convertedvalue, _other)

    # arithmetic operations are patched to allow conversions
    # TODO complete set of operations, including modulo, abs, etc.
    @fastpagosbinop(OperationKind.ADDITIVE)
    def __add__(self, other):
        return self + other

    @fastpagosbinop(OperationKind.ADDITIVE)
    def __sub__(self, other):
        return self - other

    @fastpagosbinop(OperationKind.MULTIPLICATIVE)
    def __mul__(self, other):
        return self * other

    @fastpagosbinop(OperationKind.DIVISIVE)
    def __truediv__(self, other):
        return self / other

    @fastpagosbinop(OperationKind.EXPONENTIAL)
    def __pow__(self, other):
        return self**other

    def __repr__(self):
        return f"<FastPAGOSQuantity({self.value:.9}, '{self.units}')>"

    def __str__(self):
        return f"{self.value:.9} {self.units}"


# set up UnitRegistry class that will create Quantity objects from PAGOSQuantity type
class PAGOSRegistry(pint.registry.GenericUnitRegistry[PAGOSQuantity, pint.Unit]):
    Quantity: TypeAlias = PAGOSQuantity
    Unit: TypeAlias = pint.Unit


# set up UnitRegistry class that will create Quantity objects from FastPAGOSQuantity type
class FastPAGOSRegistry(pint.registry.GenericUnitRegistry[PAGOSQuantity, pint.Unit]):
    Quantity: TypeAlias = FastPAGOSQuantity
    Unit: TypeAlias = pint.Unit


# two unit registries must exist, so that the different TypeAliases to Quantity are accessible
# (see https://pint.readthedocs.io/en/stable/advanced/custom-registry-class.html)
ureg = PAGOSRegistry()
freg = FastPAGOSRegistry()
# temporary stand-in for some global MC switch
FAST = False


# the actual class that the user will use to write their code
class PAGOSQuantityFactory:
    def __new__(cls, units):
        if FAST:
            return lambda value: freg.Quantity(value, units=units)
        else:
            return lambda value: ureg.Quantity(value, units=units)


# shorthand alias
pQ = PAGOSQuantityFactory


################################################################################################
################################################################################################
#                                         MONTE CARLO
################################################################################################
################################################################################################


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

    def _add_self_argument(self, func):
        """
        Utility to include add the argument 'self' to the front of a function's signature. ONLY to be used in make_mcmethod.
        """

        def wrapper(self, *args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    def make_mcmethod(self, func: Callable, dist_std: float):
        # The func, coming from outside this class, does not have a `self` attribute and therefore must have it created here
        func_with_self = self._add_self_argument(func)

        # mc_possible decorates the function, and we set it as an attribute in the class
        method_to_add = mc_possible(dist_std)(func_with_self)
        funcname = func.__name__
        setattr(self.__class__, funcname, method_to_add)
        return getattr(self, funcname)

    def unit_aware(self, default_units_in, units_out):
        units_out = ureg._parse_units_as_container(units_out)

        def _unit_aware(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                result = func(
                    *(pQ(unit)(arg) for unit, arg in zip(default_units_in, args)),
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


calc = PAGOSCalculator()

# TODO NEXT IMPLEMENT THIS INTO PAGOS FUNCTIONS AND GUI

# Below code shows the following:
#
#  method                           time (s)        x slower than bare floats
#  bare floats                      0.0968          1
#  undecorated & using pQ args      8.61            89
#  decorated with unit_aware        10.2            105
#  regular pint quantities          227             2345
"""
@calc.unit_aware(("cm", "m", "s^-1"), "cm s")
def some_arithmetic_wrapped(a, b, c):
    y = a + b - pQ("mm")(300)
    z = y / c
    return z


def some_arithmetic_unwrapped(a, b, c):
    a_, b_ = pQ("cm")(a), pQ("m")(b)
    y = a_ + b_ - pQ("mm")(300)
    z = y / pQ("s^-1")(c)
    return z


def some_arithmetic_pQ_input(a, b, c):
    y = a + b - pQ("mm")(300)
    z = y / c
    return z


def some_arithmetic_floats(a, b, c):
    y = a + b * 100 - 300 / 10
    z = y / c
    return z


pintreg = UnitRegistry()


def some_arithmetic_pint(a, b, c):
    y = (
        pintreg.Quantity(a, "cm")
        + pintreg.Quantity(b, "m")
        - pintreg.Quantity(300, "mm")
    )
    z = y / pintreg.Quantity(c, "s^-1")
    return z


FAST = False
some_arithmetic_wrapped(10, 2, 3)
some_arithmetic_unwrapped(10, 2, 3)
some_arithmetic_pQ_input(pQ("cm")(10), pQ("m")(2), pQ("s^-1")(3))
some_arithmetic_floats(10, 2, 3)

FAST = True
wrappedtime = timeit("some_arithmetic_wrapped(10, 2, 3)", globals=globals())
unwrappedtime = timeit("some_arithmetic_unwrapped(10, 2, 3)", globals=globals())
pQinputtime = timeit(
    'some_arithmetic_pQ_input(pQ("cm")(10), pQ("m")(2), pQ("s^-1")(3))',
    globals=globals(),
)
floatstime = timeit("some_arithmetic_floats(10, 2, 3)", globals=globals())
pinttime = timeit("some_arithmetic_pint(10, 2, 3)", globals=globals())

print(wrappedtime)
print(unwrappedtime)
print(pQinputtime)
print(floatstime)
print(pinttime)
"""
