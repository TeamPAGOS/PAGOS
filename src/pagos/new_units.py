from __future__ import annotations

import json
from numbers import Number
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


# @dataclass(frozen=True)
# class GenericGramGasConverter(Converter):
#     gas: str

#     @property
#     def is_multiplicative(self):
#         return False

#     def to_reference(self, value, inplace=False):
#         def _wrapper():
#             return value / gases_info[self.gas]["mmol [g_g/mol_g]"]

#         return _wrapper()

#     def from_reference(self, value, inplace=False):
#         def _wrapper():
#             return value * gases_info[self.gas]["mmol [g_g/mol_g]"]

#         return _wrapper()


# @dataclass(frozen=True)
# class GenericCcSTPGasConverter(Converter):
#     gas: str

#     @property
#     def is_multiplicative(self):
#         return False

#     def to_reference(self, value, inplace=False):
#         return value / gases_info[self.gas]["vmol [ccSTP_g/mol_g]"]

#     def from_reference(self, value, inplace=False):
#         return value * gases_info[self.gas]["vmol [ccSTP_g/mol_g]"]


def initialise_PAGOS_units(ureg: UnitRegistry):

    # Generic gas units. These can only be converted between each other if the gas is specified
    ureg.define("mole_gas = [amount_gas] = mol_g = mol_gas = mole_g")
    ureg.define("gram_gas = [mass_gas] = g_g = g_gas = gram_g")
    ureg.define(
        "cubic_centimeter_STP_gas = [STPvolume_gas] = ccSTP_g = ccSTP_gas = cubic_centimeter_STP_g = cm3STP_g = cm3STP_gas"
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


class PAGOSQuantity(pint.UnitRegistry.Quantity):
    _generics_transform_chain: Queue

    def __new__(cls, value, units=None):
        inst = super().__new__(cls, value, units)
        inst._generics_transform_chain = Queue()
        return inst

    @classmethod
    def add_generic_transform(
        cls,
        inst: PAGOSQuantity,
        func: Callable,
        units_of_transformer: UnitRegistry.Unit,
    ):
        ret = inst._REGISTRY.Quantity(inst.magnitude, units_of_transformer)
        ret._generics_transform_chain = inst._generics_transform_chain
        ret._generics_transform_chain.put(func)
        return ret

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
    ):
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

    def of(self, gas):
        if self._generics_transform_chain.empty():
            raise TypeError(
                f"The given quantity does not have any generic gas units and therefore cannot be expressed as an amount of {gas}"
            )
        else:
            result = self
            while not result._generics_transform_chain.empty():
                transf = result._generics_transform_chain.get()
                result = transf(result)
            return result

    def __str__(self):
        if self._generics_transform_chain.empty():
            return super().__str__()
        else:
            unitstr = super().__str__().split(" ")[1]
            return f"[unknown amount of {unitstr}]"
            # TODO NEXT this does not seem to work, still prints 1 in example below - generics transform chain variable not properly updated?


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

    # def _convert(
    #     self,
    #     value: Magnitude,
    #     src: UnitsContainer,
    #     dst: UnitsContainer,
    #     inplace: bool = False,
    #     **ctx_kwargs,
    # ) -> Magnitude:
    #     """The same as pint.facets.context.GenericContextRegistry.convert, but patched to allow for generic gas transformations."""
    #     # If there is an active context, we look for a path connecting source and
    #     # destination dimensionality. If it exists, we transform the source value
    #     # by applying sequentially each transformation of the path.
    #     if self._active_ctx:
    #         src_dim = self._get_dimensionality(src)
    #         dst_dim = self._get_dimensionality(dst)

    #         path = find_shortest_path(self._active_ctx.graph, src_dim, dst_dim)
    #         if path:
    #             src = self.Quantity(value, src)
    #             for a, b in zip(path[:-1], path[1:]):
    #                 src = self._active_ctx.transform(a, b, self, src, **ctx_kwargs)

    #             if isinstance(src, GenericGasConversionFunction):
    #                 return src
    #             else:
    #                 value, src = src._magnitude, src._units

    #     return super()._convert(value, src, dst, inplace, **ctx_kwargs)


pc = pint.Context("PAGOS")


def amount_to_mass(x, gas):
    mm = _MOLAR_MASSES_G_G_PER_MOL_G[gas]
    return x * mm


pc.add_transformation(
    "[amount_gas]",
    "[mass_gas]",
    lambda ureg, x: x.add_generic_transform(
        x, amount_to_mass, x.units * ureg.Unit("g_g/mol_g")
    ),
)

if __name__ == "__main__":
    ureg = PAGOSContextRegistry()
    initialise_PAGOS_units(ureg)
    ureg.add_context(pc)
    ureg.enable_contexts("PAGOS")
    print(ureg.Quantity(1, "mol_g").to("g_g"))
    print(ureg.Quantity(1, "mol_g").to("g_g").of("He"))
    print(ureg.Quantity(1, "mol_g").of("He").to("g_g"))
    # TODO NEXT make it so that the "of" function works on a quantity that has not already passed through a "to" call
    # TODO NEXT NEXT check that stacked "to" calls can still produce correct outcomes (e.g. x.to(...).to(...))
