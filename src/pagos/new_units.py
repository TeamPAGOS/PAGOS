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


def initialise_PAGOS_units(ureg: UnitRegistry):

    # Generic gas units. These cannot be converted between each other because context about the specific gas is
    # required for a successful conversion.
    ureg.define("mole_gas = [amount_gas] = mol_g = mol_gas = mole_g")
    ureg.define(
        "cubic_centimeter_STP_gas = [STPvolume_gas] = ccSTP_g = cm3STP_gas = cm3STP_g = cubic_centimeter_STP_g"
    )
    ureg.define("gram_gas = [gram_gas] = g_g = g_gas = gram_g")

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
                CcSTPGasConverter(gas="He"),  # converter
                UnitsContainer(**{f"mol_{gasname}": 1}),  # reference unit
            )
        )
