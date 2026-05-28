from pint import UnitRegistry
import pint
from typing import TypeAlias
from types import MethodType
from functools import wraps
from enum import Enum, auto
from tqdm import tqdm
import cProfile
from time import time


class OperationKind(Enum):
    ADDITIVE = auto()
    MULTIPLICATIVE = auto()
    DIVISIVE = auto()


# wrapper to convert binary arithmetic operators __add__ (+), __mul__ (*), etc. into ones that can access cached conversions
def fastpagosbinop(operation_kind: OperationKind):
    def _fastpagosbinop(func):
        @wraps(func)
        def wrapper(self, operand):
            if operation_kind == OperationKind.ADDITIVE:
                # additive conversions i.e.
                # an operation a @ b, where a and b have different units but equal dimensions.
                # @ = +, -
                if self.units == operand.units:
                    _sum = func(self.value, operand.value)
                    ret = self.__class__(_sum, self.units)
                else:
                    conv_id = hash((operand.units, self.units))
                    convertedvalue = PAGOSQuantity.conversions[conv_id](operand.value)
                    _sum = func(self.value, convertedvalue)
                    ret = self.__class__(_sum, self.units)
                return ret

            elif (
                operation_kind == OperationKind.MULTIPLICATIVE
                or operation_kind == OperationKind.DIVISIVE
            ):
                # multiplicative conversions i.e.
                # a * b
                conv_id = hash((self.units, operand.units, operation_kind))
                _prod = func(self.value, operand.value)
                try:
                    ret = self.__class__(_prod, PAGOSQuantity.mult_combis[conv_id])
                except KeyError as e:
                    print(
                        f"Error raised due to hash of {(self.units, operand.units, operation_kind)} = {conv_id} not found in cache:\n{PAGOSQuantity.mult_combis}"
                    )
                    raise e
                return ret
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

    def __new__(cls, value, units=None):
        return super().__new__(cls, value, units)

    def to(self, other=None, *contexts, **ctx_kwargs):
        _other = pint.util.to_units_container(other)

        def conv_func(x):
            return x * self._REGISTRY._get_conversion_factor(self._units, _other)
            # return self._REGISTRY.convert(x, self._units, _other)
            # TODO THIS WILL NOT WORK WITH NON-MULTIPLICATIVE UNITS!

        PAGOSQuantity.conversions[hash((self._units, other))] = conv_func
        # TODO this hash as two UnitsContainer objects, make sure it is this way for the FastPAGOSQuantity lookup!
        return super().to(other, *contexts, **ctx_kwargs)

    def __mul__(self, other):
        ret = super().__mul__(other)
        PAGOSQuantity.mult_combis[
            hash((self._units, other._units, OperationKind.MULTIPLICATIVE))
        ] = ret._units
        return ret

    def __truediv__(self, other):
        ret = super().__truediv__(other)
        PAGOSQuantity.mult_combis[
            hash((self._units, other._units, OperationKind.DIVISIVE))
        ] = ret._units
        return ret


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


pQ = PAGOSQuantityFactory


# an example function that a user could have written
def some_arithmetic(a, b, c):
    a_, b_ = pQ("cm")(a), pQ("m")(b)
    y = a_ + b_ - pQ("mm")(300)
    z = y / pQ("s^-1")(c)
    return z


# the example data we will use is a = 10 cm, b = 2 m, c = 3 s^-1
# step-by-step, the conversions are:
#   y = 10 cm + 2 m - 300 mm
#     =(10    + 200 - 30    ) cm
#     = 180 cm
#   z = 180 cm / (3 s^-1)
#     = 60 cm s


# TIMING
to_execute = """
t = some_arithmetic(10, 2, 3)
assert t.magnitude == 60
"""


FAST = False
print("slow")
t1 = time()
for i in tqdm(range(10000)):
    t = some_arithmetic(10, 2, 3)
    # assert to check correct answer
    assert t.magnitude == 60
slowtime = time() - t1

FAST = True
print("fast")
t1 = time()
for i in tqdm(range(10000)):
    t = some_arithmetic(10, 2, 3)
    assert t.value == 60
fasttime = time() - t1


def some_arithmetic_veryfast(a, b, c):
    a_, b_ = a, b * 100
    y = a_ + b_ - 30
    z = y / c
    return z


t1 = time()
print("extremely fast")
for i in tqdm(range(10000)):
    t = some_arithmetic_veryfast(10, 2, 3)
    assert t == 60
veryfasttime = time() - t1

print(
    f"PAGOS caching method is {slowtime / fasttime}x faster than regular Pint and {fasttime / veryfasttime}x slower than manual conversion arithmetic"
)

# %%
my_code = """
FAST = False
some_arithmetic(10, 2, 3)
FAST = True
for i in range(10000):
    some_arithmetic(10, 2, 3)
"""

cProfile.runctx(
    my_code, filename="./temp/newunitsprofile", globals=globals(), locals=locals()
)
