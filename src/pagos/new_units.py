from __future__ import annotations

import itertools
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
from math import isnan
from typing import TypeAlias

import pint
from pint import UnitRegistry
from pint._typing import Scalar
from pint.facets.plain.definitions import ScaleConverter, UnitDefinition
from pint.util import UnitsContainer, to_units_container
from sympy import Expr, Symbol, sympify

from pagos._constants import (
    _MOLAR_MASSES_G_G_PER_MOL_G,
    _MOLAR_VOLUMES_CCSTP_G_PER_MOL_G,
    m_mol,
    v_mol,
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
class GenericPAGOSConverter(ScaleConverter):
    scale: Symbol


def initialise_PAGOS_units(ureg: UnitRegistry):
    ureg.define("mole_gas = [amount_gas] = mol_gas = mol_g = mole_g")
    ureg.define(
        UnitDefinition(
            "gram_gas",
            "g_gas",
            ("g_g", "gram_g"),
            GenericPAGOSConverter(scale=1 / m_mol),
            UnitsContainer({"mol_gas": 1}),
        )
    )
    ureg.define(
        UnitDefinition(
            "cubic_centimeter_STP_gas",
            "ccSTP_gas",
            (
                "ccSTP_g",
                "cubic_centimeter_STP_g",
                "cc_STP_gas",
                "cc_STP_g",
                "cm3STP_gas",
                "cm3STP_g",
                "cm3_STP_gas",
                "cm3_STP_g",
            ),
            GenericPAGOSConverter(scale=1 / v_mol),
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
                GenericPAGOSConverter(
                    scale=1 / _MOLAR_MASSES_G_G_PER_MOL_G[gasname]
                ),  # converter
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
                GenericPAGOSConverter(
                    scale=1 / _MOLAR_VOLUMES_CCSTP_G_PER_MOL_G[gasname]
                ),  # converter
                UnitsContainer(**{f"mol_{gasname}": 1}),  # reference unit
            )
        )


class PAGOSQuantity(UnitRegistry.Quantity):
    def __new__(cls, value, units=None, gas: str = None):
        if isinstance(units, PAGOSUnit):
            units = str(units)
        inst = super().__new__(cls, value, units)
        if cls.are_units_generic_gas_units(inst):
            if gas:
                units = cls.change_generic_units_to_specific(inst.units, gas)
                expr = value
            else:
                expr = sympify(value)
            inst = super().__new__(cls, expr, units)
        return inst

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
        other = to_units_container(other, self._REGISTRY)
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

    def of(self, gas: str) -> PAGOSQuantity:
        """Calculates a specific quantity of gas, given a generic form.
        For example:
        ```python
        >>> x = pQ(4, "g_gas")
        >>> x.of("He")
        4 gram_He
        >>> y = x.to("mol_gas")
        >>> y
        4/mₘ mole_gas
        >>> y.of("He")
        0.999349922875170 mole_He
        ```

        Args:
            gas (str): Gas for which to evaluate the quantity.

        Returns:
            PAGOSQuantity: Result of substitution.
        """
        specific_mmol = _MOLAR_MASSES_G_G_PER_MOL_G[gas]
        specific_vmol = _MOLAR_VOLUMES_CCSTP_G_PER_MOL_G[gas]

        submag = self.magnitude.subs(((v_mol, specific_vmol), (m_mol, specific_mmol)))
        specific_units = self.change_generic_units_to_specific(self.units, gas)
        return self._REGISTRY.Quantity(submag, specific_units)


gas_names = [gas_info["name"] for gas_info in gases_info.values()]
gasregex = r"(?:" + "|".join(re.escape(name) for name in gas_names) + r")"


class PAGOSUnit(pint.UnitRegistry.Unit):
    """Same as regular Pint unit, but includes a gas property."""

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

    # This is a patch over the regular _get_root_units function provided by pint, to allow for symbolic magnitudes.
    # Only one line is patched
    def _get_root_units(
        self, input_units: UnitsContainer, check_nonmult: bool = True
    ) -> tuple[Scalar, UnitsContainer]:
        """Convert unit or dict of units to the root units.

        If any unit is non multiplicative and check_converter is True,
        then None is returned as the multiplicative factor.

        Parameters
        ----------
        input_units : UnitsContainer or dict
            units
        check_nonmult : bool
            if True, None will be returned as the
            multiplicative factor if a non-multiplicative
            units is found in the final Units. (Default value = True)

        Returns
        -------
        number, Unit
            multiplicative factor, plain units

        """
        if not input_units:
            return 1, self.UnitsContainer()

        cache = self._cache.root_units
        try:
            return cache[input_units]
        except KeyError:
            pass

        accumulators: dict[str | None, int] = defaultdict(int)
        fraction: dict[str, dict[Decimal | float, Decimal | int]] = dict(
            numerator=dict(), denominator=dict()
        )
        self._get_root_units_recurse(input_units, 1, accumulators, fraction)

        ### PATCH OCCURS HERE: not isinstance(k, Expr) ADDED TO PREVENT ERROR THROWN ON isnan(k) CALL ###
        if any(
            (not isinstance(k, Expr) and isnan(k))
            for k in itertools.chain(fraction["numerator"], fraction["denominator"])
        ):
            # If there is a nan factor, the result is nan
            return float("nan"), self.UnitsContainer()

        # Identify if terms appear in both numerator and denominator
        def terms_are_unique(fraction):
            for n_factor, n_exp in fraction["numerator"].items():
                if n_factor in fraction["denominator"]:
                    return False
            return True

        # Cancel out terms where factor matches
        while not terms_are_unique(fraction):
            for n_factor, n_exponent in fraction["numerator"].items():
                if n_factor in fraction["denominator"]:
                    if n_exponent >= fraction["denominator"][n_factor]:
                        fraction["numerator"][n_factor] -= fraction["denominator"][
                            n_factor
                        ]
                        del fraction["denominator"][n_factor]
                        continue
            for d_factor, d_exponent in fraction["denominator"].items():
                if d_factor in fraction["numerator"]:
                    if d_exponent >= fraction["numerator"][d_factor]:
                        fraction["denominator"][d_factor] -= fraction["numerator"][
                            d_factor
                        ]
                        del fraction["numerator"][d_factor]
                        continue

        factor = 1
        for n_factor, n_exponent in fraction["numerator"].copy().items():
            if n_exponent == 0:
                del fraction["numerator"][n_factor]
            else:
                factor *= n_factor**n_exponent
        for d_factor, d_exponent in fraction["denominator"].copy().items():
            if d_exponent == 0:
                del fraction["denominator"][d_factor]
            else:
                factor *= d_factor**-d_exponent

        units = self.UnitsContainer(
            {k: v for k, v in accumulators.items() if k is not None and v != 0}
        )

        # Check if any of the final units is non multiplicative and return None instead.
        if check_nonmult:
            if any(not self._units[unit].converter.is_multiplicative for unit in units):
                factor = None

        cache[input_units] = factor, units
        return factor, units


ureg = PAGOSContextRegistry(default_as_delta=False)
initialise_PAGOS_units(ureg)


def pQ(value, units, gas: str = None) -> PAGOSQuantity:
    return ureg.Quantity(value, units, gas=gas)


if __name__ == "__main__":
    print(pQ(1, "mol_g").to("g_g"))
    print(pQ(1, "mol_g").to("g_g").of("He"))
    print(pQ(1, "mol_g").to("mg_g", gas="Ar"))
    print(pQ(1, "mol_g").of("He").to("g_g"))

    x = pQ(1, "mol_g/m")
    print(x.to("g_g/cm").of("He"))
    print(x.to("ccSTP_g/mm").of("He"))
    print(x.to("g_g/m").to("ccSTP_g/m").of("Ar"))

    print(x.to("g_g/m"))
    print(pQ(4, "g_g").to("mol_g").of("He"))
