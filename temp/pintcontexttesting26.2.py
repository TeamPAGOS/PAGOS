# Has Pint implemented a powerful enough context manager to handle compound units in a context?
# Test it here

from dataclasses import dataclass
from typing import Optional

from pint import Context, UnitRegistry, DimensionalityError
from pint.converters import Converter
from pint.facets.plain.definitions import ScaleConverter, UnitDefinition
from pint.util import UnitsContainer

ureg = UnitRegistry()

pc = Context("pc")

molar_masses = {"He": 4.002602}


@dataclass(frozen=True)
class GramGasConverter(ScaleConverter):
    # NOTE: this is a bit ugly, would be nicer to set gas and scale like regular dataclass fields,
    # but this is the only way I could get it to work while still inheriting from ScaleConverter
    def __init__(self, gas):
        super().__init__(scale=None)
        object.__setattr__(self, "gas", gas)
        object.__setattr__(self, "scale", molar_masses[self.gas])


ureg.define("mole_gas = [amount_gas] = mol_gas = mol_g")

ureg.define("mole_He = [amount_He] = mol_He")
ureg.define(
    UnitDefinition(
        "gram_He",  # name
        "g_He",  # symbol
        (),  # aliases
        GramGasConverter(gas="He"),  # converter
        UnitsContainer(mole_He=1),  # reference unit
    )
)

print(ureg.Quantity(1, "mol_He / g_He").to("g_He / mol_He"))
print(ureg.Quantity(4.002602, "g_He / mol_He").to(""))

pc.add_transformation(
    "[amount_gas]",
    "[amount_He]",
    lambda ureg, x, gas: x if gas == "He" else DimensionalityError,
)
pc.add_transformation(
    "[amount_He]",
    "[amount_gas]",
    lambda ureg, x, gas: x if gas == "He" else DimensionalityError,
)

ureg.add_context(pc)
ureg.enable_contexts("pc")

print(ureg.Quantity(1, "mol_g").to("mol_He", "pc", gas="He"))
