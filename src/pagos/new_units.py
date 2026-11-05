from __future__ import annotations

from collections.abc import Callable
import json
from dataclasses import dataclass
from functools import reduce
from operator import add
import re
from typing import Any

from pint import Context, Quantity, UnitRegistry
import pint
from pint.converters import Converter
from pint.facets.plain.definitions import Magnitude, ScaleConverter, UnitDefinition
from pint.util import UnitsContainer, find_shortest_path

import wrapt

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


@dataclass(frozen=True)
class GenericGasConversionFunction:
    func: Callable
    ureg: UnitRegistry

    def __call__(self, *args, **kwds):
        return self.func(*args, **kwds)


class PAGOSContextRegistry(pint.UnitRegistry):
    def _convert(
        self,
        value: Magnitude,
        src: UnitsContainer,
        dst: UnitsContainer,
        inplace: bool = False,
        **ctx_kwargs,
    ) -> Magnitude:
        """The same as pint.facets.context.GenericContextRegistry.convert, but patched to allow for generic gas transformations."""
        # If there is an active context, we look for a path connecting source and
        # destination dimensionality. If it exists, we transform the source value
        # by applying sequentially each transformation of the path.
        if self._active_ctx:
            src_dim = self._get_dimensionality(src)
            dst_dim = self._get_dimensionality(dst)

            path = find_shortest_path(self._active_ctx.graph, src_dim, dst_dim)
            if path:
                src = self.Quantity(value, src)
                for a, b in zip(path[:-1], path[1:]):
                    src = self._active_ctx.transform(a, b, self, src, **ctx_kwargs)

                if isinstance(src, GenericGasConversionFunction):
                    value, src = src, None
                else:
                    value, src = src._magnitude, src._units

        # TODO NEXT: problem: super() call passes down to the regular GenericContextRegistry from pint. This could be bad because we
        # then pass in nonsense values; perhaps do NOT call super()? But is that also bad because it re-passes the values into
        # GenericContextRegistry?
        return super()._convert(value, src, dst, inplace, **ctx_kwargs)


# monkey patch over GenericContextRegistry method
# pint.facets.context.registry.GenericContextRegistry = PAGOSContextRegistry

pc = pint.Context("PAGOS")
# dummy, remove me later
pc.add_transformation(
    "[amount_gas]",
    "[mass_gas]",
    lambda ureg, x: GenericGasConversionFunction(
        lambda x, gas: {"He": x, "Ne": 2 * x}[gas], ureg
    ),
)

if __name__ == "__main__":
    ureg = PAGOSContextRegistry()
    initialise_PAGOS_units(ureg)
    ureg.add_context(pc)
    ureg.enable_contexts("PAGOS")
    ureg.Quantity(1, "mol_g").to("g_g")
    pass
