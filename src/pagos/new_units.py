from __future__ import annotations

import json
from numbers import Number, Real
from queue import Queue
import re
from collections.abc import Callable
from dataclasses import dataclass
from functools import reduce
from operator import add
from typing import Any, TypeAlias

import pint
from pint import Context, Quantity, UnitRegistry
from pint.converters import Converter
from pint.facets.plain.definitions import Magnitude, ScaleConverter, UnitDefinition
from pint.util import UnitsContainer, find_shortest_path

from pagos._constants import (
    _MOLAR_MASSES_G_G_PER_MOL_G,
    _MOLAR_VOLUMES_CCSTP_G_PER_MOL_G,
)

# gases json file
with open("src/pagos/gases.json", "r") as gases_file:
    gases_info = json.load(gases_file)["gases"]


# Converters
# NOTE: the __setattr__ syntax here is a bit ugly, would be nicer to set gas and scale like regular dataclass fields,
# but this is the only way I could get it to work while still inheriting from ScaleConverter
@dataclass(frozen=True)
class GramGasConverter(ScaleConverter):
    def __init__(self, gas):
        super().__init__(scale=None)
        object.__setattr__(self, "gas", gas)
        object.__setattr__(self, "scale", 1 / _MOLAR_MASSES_G_G_PER_MOL_G[gas])


@dataclass(frozen=True)
class CcSTPGasConverter(ScaleConverter):
    def __init__(self, gas):
        super().__init__(scale=None)
        object.__setattr__(self, "gas", gas)
        object.__setattr__(self, "scale", 1 / _MOLAR_VOLUMES_CCSTP_G_PER_MOL_G[gas])


@dataclass(frozen=True)
class GenericGramGasConverter(Converter):
    @property
    def is_multiplicative(self):
        return False

    # TODO NEXT this fails because allowing multiplicative to return True means pint looks for .scale property, not there
    # Giving a scale property causes the scale to be taken and the to_reference and from_reference values to never be called :(
    # Setting to False changes the units automatically to delta-units and this fails too.

    def to_reference(self, value, inplace=False):
        def mass_to_amount(x, gas):
            mm = _MOLAR_MASSES_G_G_PER_MOL_G[gas]
            return x / mm

        return value.add_generic_transform(
            value, mass_to_amount, x.units * x._REGISTRY.Unit("mol_g/g_g")
        )

    def from_reference(self, value, inplace=False):
        def amount_to_mass(x, gas):
            mm = _MOLAR_MASSES_G_G_PER_MOL_G[gas]
            return x * mm

        return value.add_generic_transform(
            value, amount_to_mass, x.units * x._REGISTRY.Unit("g_g/mol_g")
        )


def initialise_PAGOS_units(ureg: UnitRegistry, ctx: Context):

    # Generic gas units
    ureg.define("mole_gas = [amount_gas] = mol_g = mol_gas = mole_g")
    ureg.define("gram_gas = [mass_gas] = g_g = g_gas = gram_g")
    ureg.define(
        "cubic_centimeter_STP_gas = [STPvolume_gas] = ccSTP_g = ccSTP_gas = cubic_centimeter_STP_g = cm3STP_g = cm3STP_gas"
    )
    # Transformations between these three dimensions are defined via a Context. The graph of these relations is as follows:
    #
    # [amount]◄──────►[mass]
    #    ▲              ▲
    #    └───┐      ┌───┘
    #        ▼      ▼
    #      [STP volume]
    #
    # Pint Contexts always traverse the whole graph and finds the shortest path, so as long as the graph is strongly connected,
    # we only need to define N transformations. Here we define 2N, for symmetry and speed.

    # def amount_to_mass(x, gas):
    #     mm = _MOLAR_MASSES_G_G_PER_MOL_G[gas]
    #     return x * mm

    # def mass_to_amount(x, gas):
    #     mm = _MOLAR_MASSES_G_G_PER_MOL_G[gas]
    #     return x / mm

    # def amount_to_STP_volume(x, gas):
    #     mv = _MOLAR_VOLUMES_CCSTP_G_PER_MOL_G[gas]
    #     return x * mv

    # def STP_volume_to_amount(x, gas):
    #     mv = _MOLAR_VOLUMES_CCSTP_G_PER_MOL_G[gas]
    #     return x / mv

    # def STP_volume_to_mass(x, gas):
    #     mm = _MOLAR_MASSES_G_G_PER_MOL_G[gas]
    #     mv = _MOLAR_VOLUMES_CCSTP_G_PER_MOL_G[gas]
    #     return x / mv * mm

    # def mass_to_STP_volume(x, gas):
    #     mm = _MOLAR_MASSES_G_G_PER_MOL_G[gas]
    #     mv = _MOLAR_VOLUMES_CCSTP_G_PER_MOL_G[gas]
    #     return x * mv / mm

    # # Each transformation in the Context is actually represented by just returning the original Quantity, with an added
    # # generic transform; the magnitude of a Quantity with generic gas units is a GenericGasMagnitude instance (see below)
    # # which has a Queue of transformation functions. This Queue is appended to every time a generic transformation would
    # # occur (e.g. "gram_gas" to "mmol_gas"). The Queue's functions are executed and the Queue is cleared once a realisation
    # # of an actual gas is desired (e.g. .to("mol_gas", gas="He") or .of("He")).
    # ctx.add_transformation(
    #     "[amount_gas]",
    #     "[mass_gas]",
    #     lambda ureg, x: x.add_generic_transform(
    #         x, amount_to_mass, x.units * ureg.Unit("g_g/mol_g")
    #     ),
    # )
    # ctx.add_transformation(
    #     "[mass_gas]",
    #     "[amount_gas]",
    #     lambda ureg, x: x.add_generic_transform(
    #         x, mass_to_amount, x.units * ureg.Unit("mol_g/g_g")
    #     ),
    # )
    # ctx.add_transformation(
    #     "[amount_gas]",
    #     "[STPvolume_gas]",
    #     lambda ureg, x: x.add_generic_transform(
    #         x, amount_to_STP_volume, x.units * ureg.Unit("ccSTP_g/mol_g")
    #     ),
    # )
    # ctx.add_transformation(
    #     "[STPvolume_gas]",
    #     "[amount_gas]",
    #     lambda ureg, x: x.add_generic_transform(
    #         x, STP_volume_to_amount, x.units * ureg.Unit("mol_g/ccSTP_g")
    #     ),
    # )
    # ctx.add_transformation(
    #     "[STPvolume_gas]",
    #     "[mass_gas]",
    #     lambda ureg, x: x.add_generic_transform(
    #         x, STP_volume_to_mass, x.units * ureg.Unit("g_g/ccSTP_g")
    #     ),
    # )
    # ctx.add_transformation(
    #     "[mass_gas]",
    #     "[STPvolume_gas]",
    #     lambda ureg, x: x.add_generic_transform(
    #         x, mass_to_STP_volume, x.units * ureg.Unit("ccSTP_g/g_g")
    #     ),
    # )

    # ureg.add_context(ctx)
    # ureg.enable_contexts(ctx.name)

    # WIP: TRYING TO DEFINE THE UNITS WITHOUT CONTEXTS
    ureg.define("mole_gas = [amount_gas] = mol_gas = mol_g = mole_g")
    ureg.define(
        UnitDefinition(
            "gram_gas",
            "g_gas",
            ("g_g", "gram_g"),
            GenericGramGasConverter(),  # converter
            UnitsContainer({"mol_gas": 1}),
        )
    )

    # Specific gas units
    for gas in gases_info:
        gasname = gases_info[gas]["name"]

        # Reference units of gas quantities are moles of the gas.
        # These are defined as using the syntax UnitRegistry.define("mole_X = [amount_X] = mol_X"),
        # where X stands for the gas species.
        base_unit_definition = f"mole_{gasname} = [amount_{gasname}] = mol_{gasname}"
        ureg.define(base_unit_definition)

        # Definitions of units along with their converters
        ureg.define(
            UnitDefinition(
                f"gram_{gasname}",  # name
                f"g_{gasname}",  # symbol
                (),  # aliases
                GramGasConverter(gas=gasname),  # converter
                UnitsContainer(**{f"mol_{gasname}": 1}),  # reference unit
            )
        )

        ureg.define(
            UnitDefinition(
                f"cubic_centimeter_STP_{gasname}",  # name
                f"ccSTP_{gasname}",  # symbol
                (
                    f"cm3STP_{gasname}",
                    f"cc_STP_{gasname}",
                    f"cm3_STP_{gasname}",
                ),  # aliases
                CcSTPGasConverter(gas=gasname),  # converter
                UnitsContainer(**{f"mol_{gasname}": 1}),  # reference unit
            )
        )


class GenericGasMagnitude(float):
    def __init__(self, value, *, transform_chain: Queue | None = None):
        self.value = value
        if isinstance(value, GenericGasMagnitude):
            self.value = value.value
            self.transform_chain = value.transform_chain
        else:
            self.value = value
            self.transform_chain: Queue[Callable] = Queue()

        # overwrite with given transform_chain if so desired
        if transform_chain:
            self.transform_chain = transform_chain

    def unravel_transform_chain(self, gas):
        ret = self.value
        chain = self.transform_chain
        while not chain.empty():
            func = chain.get()
            ret = func(ret, gas)
        return ret

    def wrap_arithmetic_function(func: Callable):
        def _wrapped_arith_func(self, value, /):
            return GenericGasMagnitude(
                func(self, value), transform_chain=self.transform_chain
            )

        return _wrapped_arith_func

    @wrap_arithmetic_function
    def __add__(self, value):
        return super().__add__(value)

    @wrap_arithmetic_function
    def __sub__(self, value):
        return super().__sub__(value)

    @wrap_arithmetic_function
    def __mul__(self, value):
        return super().__mul__(value)

    @wrap_arithmetic_function
    def __truediv__(self, value):
        return super().__truediv__(value)

    @wrap_arithmetic_function
    def __floordiv__(self, value):
        return super().__floordiv__(value)

    @wrap_arithmetic_function
    def __pow__(self, value):
        return super().__pow__(value)

    @wrap_arithmetic_function
    def __mod__(self, value):
        return super().__mod__(value)

    @wrap_arithmetic_function
    def __matmul__(self, value):
        return super().__matmul__(value)

    @wrap_arithmetic_function
    def __radd__(self, value):
        return value + self.value

    @wrap_arithmetic_function
    def __rsub__(self, value):
        return value - self.value

    @wrap_arithmetic_function
    def __rmul__(self, value):
        return value * self.value

    @wrap_arithmetic_function
    def __rtruediv__(self, value):
        return value / self.value

    @wrap_arithmetic_function
    def __rfloordiv__(self, value):
        return value // self.value

    @wrap_arithmetic_function
    def __rpow__(self, value):
        return value**self.value

    @wrap_arithmetic_function
    def __rmod__(self, value):
        return value % self.value

    @wrap_arithmetic_function
    def __rmatmul__(self, value):
        return value @ self.value


class PAGOSQuantity(pint.UnitRegistry.Quantity):
    def __new__(cls, value, units=None):
        inst = super().__new__(cls, value, units)
        if cls.are_units_generic_gas_units(inst):
            inst = super().__new__(cls, GenericGasMagnitude(value), units)
        return inst

    @classmethod
    def add_generic_transform(
        cls,
        inst: PAGOSQuantity,
        func: Callable,
        units_of_transformer: UnitRegistry.Unit,
    ):
        if isinstance(inst.magnitude, GenericGasMagnitude):
            ret = inst._REGISTRY.Quantity(
                GenericGasMagnitude(
                    inst.magnitude.value,
                    transform_chain=inst.magnitude.transform_chain,
                ),
                units_of_transformer,
            )
        else:
            ret = inst._REGISTRY.Quantity(
                GenericGasMagnitude(inst.magnitude), units_of_transformer
            )
        ret.magnitude.transform_chain.put(func)
        return ret

    @classmethod
    def are_units_generic_gas_units(cls, inst: PAGOSQuantity):
        unit_items = [u for u in inst.units._units.unit_items()]
        for u in unit_items:
            if u[0].endswith("_gas"):
                return True
        return False

    @classmethod
    def change_generic_units_to_specific(cls, units: pint.Unit, gas: str):
        """Replaces all instances of generic gas suffixes with specific gas"""
        unit_items = [u for u in units._units.unit_items()]
        for i, u in enumerate(unit_items):
            if u[0].endswith("_gas"):
                unit_items[i] = (u[0].replace("_gas", f"_{gas}"), u[1])
        changed_units = units._REGISTRY.Unit(UnitsContainer(unit_items))
        return changed_units

    def to(
        self, other=None, *contexts, gas: str | None = None, block=False, **ctx_kwargs
    ) -> PAGOSQuantity:
        # block argument prevents infinite recursion
        if not block and ((g := gas) or (g := self.units.gas)):
            changed_units = self.change_generic_units_to_specific(self.units, g)
            changed_other = self.change_generic_units_to_specific(
                self._REGISTRY.Unit(other), g
            )
            quant_with_changed_units = self._REGISTRY.Quantity(
                self.magnitude, changed_units
            )
            return quant_with_changed_units.to(
                changed_other, *contexts, block=True, **ctx_kwargs
            )

        return super().to(other, *contexts, **ctx_kwargs)

    def of(self, gas) -> PAGOSQuantity:
        if not self.are_units_generic_gas_units(self):
            raise TypeError(
                f"The given quantity does not have any generic gas units and therefore cannot be expressed as an amount of {gas}"
            )

        if isinstance(self.magnitude, GenericGasMagnitude):
            return self._REGISTRY.Quantity(
                self.magnitude.unravel_transform_chain(gas),
                self.change_generic_units_to_specific(self.units, gas),
            )
        else:
            return self

    def __str__(self):
        if (
            isinstance(self.magnitude, GenericGasMagnitude)
            and not self.magnitude.transform_chain.empty()
        ):
            unitstr = super().__str__().split(" ")[1]
            return f"[unknown amount of {unitstr}]"
        else:
            return super().__str__()


gas_names = [gas_info["name"] for gas_info in gases_info.values()]
gasregex = r"(?:" + "|".join(re.escape(name) for name in gas_names) + r")"


class PAGOSUnit(pint.UnitRegistry.Unit):
    def __init__(self, units):
        super().__init__(units)
        self.gas = None
        # match any specific gases in the unit and set the corresponding attribute
        for unit_name, _ in self._units.unit_items():
            match = re.search(rf"_({gasregex})$", unit_name)
            if match:
                if self.gas:
                    self.gas = "multiple"
                    break
                self.gas = match.group(1)

    @property
    def gas(self):
        return self.__gas

    @gas.setter
    def gas(self, new_gas):
        self.__gas = new_gas


class PAGOSContextRegistry(pint.registry.GenericUnitRegistry[PAGOSQuantity, PAGOSUnit]):
    """
    Default `UnitRegistry` from which all quantities dealt with by PAGOS should be derived.
    """

    Quantity: TypeAlias = PAGOSQuantity
    Unit: TypeAlias = PAGOSUnit


pc = ...
ureg = PAGOSContextRegistry()
initialise_PAGOS_units(ureg, pc)


if __name__ == "__main__":
    # print(ureg.Quantity(1, "mol_g").to("g_g"))
    # print(ureg.Quantity(1, "mol_g").to("g_g").of("He"))
    # print(ureg.Quantity(1, "mol_g").to("mg_g", gas="Ar"))
    # print(ureg.Quantity(1, "mol_g").of("He").to("g_g"))

    x = ureg.Quantity(1, "mol_g/kg")
    # print(x.to("g_g").of("He"))
    # print(x.to("ccSTP_g").of("He"))
    # print(x.to("g_g").to("ccSTP_g").of("Ar"))

    print(x.to("g_g/kg"))
    # TODO NEXT test compound units (g_g/kg, e.g.)
