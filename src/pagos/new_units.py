from __future__ import annotations

import json
from dataclasses import dataclass
from functools import reduce
from operator import add

from pint import Context, UnitRegistry
from pint.converters import Converter
from pint.facets.plain.definitions import ScaleConverter, UnitDefinition
from pint.util import UnitsContainer

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
        object.__setattr__(self, "scale", 1 / gases_info[gas]["mmol [g_g/mol_g]"])


@dataclass(frozen=True)
class CcSTPGasConverter(ScaleConverter):
    def __init__(self, gas):
        super().__init__(scale=None)
        object.__setattr__(self, "gas", gas)
        object.__setattr__(self, "scale", 1 / gases_info[gas]["vmol [ccSTP_g/mol_g]"])


@dataclass(frozen=True)
class GenericGramGasConverter(Converter):
    def __init__(self):
        gas: str

    @property
    def is_multiplicative(self):
        return False

    def to_reference(self, value, inplace=False):
        def _wrapper():
            return value / gases_info[self.gas]["mmol [g_g/mol_g]"]

        return _wrapper()

    def from_reference(self, value, inplace=False):
        def _wrapper():
            return value * gases_info[self.gas]["mmol [g_g/mol_g]"]

        return _wrapper()


@dataclass(frozen=True)
class GenericCcSTPGasConverter(Converter):
    def __init__(self):
        gas: str

    @property
    def is_multiplicative(self):
        return False

    def to_reference(self, value, inplace=False):
        return value / gases_info[self.gas]["vmol [ccSTP_g/mol_g]"]

    def from_reference(self, value, inplace=False):
        return value * gases_info[self.gas]["vmol [ccSTP_g/mol_g]"]


def initialise_PAGOS_units(ureg: UnitRegistry):

    # Generic gas units. These can only be converted between each other if the gas is specified
    ureg.define("mole_gas = [amount_gas] = mol_g = mol_gas = mole_g")
    ureg.define(
        UnitDefinition(
            "gram_gas",  # name
            "g_g",  # symbol
            ("g_gas", "gram_g"),  # aliases
            GenericGramGasConverter(),  # converter
            UnitsContainer(mole_gas=1),  # reference unit
        )
    )
    ureg.define(
        UnitDefinition(
            "cubic_centimeter_STP_gas",  # name
            "ccSTP_g",  # symbol
            (
                "cm3STP_gas",
                "cm3STP_g",
                "cubic_centimeter_STP_g",
                "ccSTP_gas",
            ),  # aliases
            GenericCcSTPGasConverter(),  # converter
            UnitsContainer(mole_gas=1),  # reference unit
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


if __name__ == "__main__":
    ureg = UnitRegistry()
    initialise_PAGOS_units(ureg)
    pass
