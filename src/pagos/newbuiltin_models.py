"""Builtin gas exchange models in PAGOS."""

import numpy as np

from pagos.gasobject import Gas, abn, calc_Ceq, calc_Sc
from pagos.newcore import PAGOSQuantity, set_warn_nonmult, unit_aware
from pagos.newmodelling import TracerModel
from pagos.newwater import calc_kinvisc

set_warn_nonmult(False)


@unit_aware(
    {"gas": None, "T": "degC", "S": "permille", "p": "atm", "A": "mol/kg"}, "mol_gas/kg"
)
def ua(
    gas: Gas | str,
    T: float | PAGOSQuantity,
    S: float | PAGOSQuantity,
    p: float | PAGOSQuantity,
    A: float | PAGOSQuantity,
) -> PAGOSQuantity:
    """Unfractionated excess air (UA) model, typically for groundwater studies.
    * C = Cₑ(T, S, p) + Aχ
        * Cₑ(T, S, p) = equilibrium concentration at water recharge temperature T, salinity S and air pressure p
        * A = excess air in same units as Cₑ
        * χ = atmospheric abundance of given gas

    See Jung and Aeschbach 2018 (https://doi.org/10.1016/j.envsoft.2018.02.004) for more details.

    ## Units
        **default units in** — `T`: °C, `S`: ‰, `p`: atm, `A`: mol/kg
        **default units out** — mol_gas/kg

    Args:
        gas (Gas | str): Gas whose concentration should be calculated
        T (float | PAGOSQuantity): Temperature of the water
        S (float | PAGOSQuantity): Salinity of the water
        p (float | PAGOSQuantity): Pressure over the water
        A (float | PAGOSQuantity): Excess air

    Returns:
        PAGOSQuantity: Concentration of gas calculated with the model
    """
    return calc_Ceq(gas, T, S, p) + A * abn(gas)


ua_model = TracerModel(ua)


@unit_aware(
    {
        "gas": None,
        "T": "degC",
        "S": "permille",
        "p": "atm",
        "A": "mol/kg",
        "FPR": "dimensionless",
        "beta": "dimensionless",
    },
    "mol_gas/kg",
)
def pr(
    gas: Gas | str,
    T: float | PAGOSQuantity,
    S: float | PAGOSQuantity,
    p: float | PAGOSQuantity,
    A: float | PAGOSQuantity,
    FPR: float | PAGOSQuantity,
    beta: float | PAGOSQuantity,
) -> PAGOSQuantity:
    """
    Partial re-equilibration (PR) model, typically for groundwater studies.
    * C = Cₑ(T, S, p) + Aχ·exp(−Fᴾᴿ·(D/Dᶰᵉ)ᵝ)
        * Cₑ(T, S, p) = equilibrium concentration at water recharge temperature T, salinity S and air pressure p
        * A = excess air in same units as Cₑ
        * χ = atmospheric abundance of given gas
        * Fᴾᴿ = dimensionless excess air loss parameter
        * D = diffusion coefficient of gas
        * Dᶰᵉ = diffusion coefficient of neon
        * β = exponent in relationship of gas transfer velocity to diffusivity in water

    See Jung and Aeschbach 2018 (https://doi.org/10.1016/j.envsoft.2018.02.004) for more details.

    ## Units
        **default units in** — `T`: °C, `S`: ‰, `p`: atm, `A`: mol/kg, `FPR`: dimensionless, `beta`: dimensionless
        **default units out** — mol_gas/kg

    Args:
        gas (Gas | str): Gas whose concentration should be calculated
        T (float | PAGOSQuantity): Temperature of the water
        S (float | PAGOSQuantity): Salinity of the water
        p (float | PAGOSQuantity): Pressure over the water
        A (float | PAGOSQuantity): Excess air
        FPR (float | PAGOSQuantity): Dimensionless excess air loss parameter
        beta (float | PAGOSQuantity): Dimenionless exponent in PR model

    Returns:
        PAGOSQuantity: Concentration of gas calculated with the model
    """
    kinvisc = calc_kinvisc(T, S)
    schmidt = calc_Sc(gas, T, S)
    diff = kinvisc / schmidt
    diffNe = kinvisc / calc_Sc("Ne", T, S)
    return calc_Ceq(gas, T, S, p) + A * abn(gas) * np.exp(
        -FPR * (diff / diffNe) ** beta
    )


pr_model = TracerModel(pr)


@unit_aware(
    {
        "gas": None,
        "T": "degC",
        "S": "permille",
        "p": "atm",
        "A": "mol/kg",
        "FPD": "dimensionless",
        "beta": "dimensionless",
    },
    "mol_gas/kg",
)
def pd(
    gas: Gas | str,
    T: float | PAGOSQuantity,
    S: float | PAGOSQuantity,
    p: float | PAGOSQuantity,
    A: float | PAGOSQuantity,
    FPD: float | PAGOSQuantity,
    beta: float | PAGOSQuantity,
) -> PAGOSQuantity:
    """Partial degassing (PD) model, typically for groundwater studies.
    * C = [Cₑ(T, S, p) + Aχ]·exp(−Fᴾᴰ·(D/Dᶰᵉ)ᵝ)
        * Cₑ(T, S, p) = equilibrium concentration at water recharge temperature T, salinity S and air pressure p
        * A = excess air in same units as Cₑ
        * χ = atmospheric abundance of given gas
        * Fᴾᴰ = dimensionless diffusive gas loss parameter
        * D = diffusion coefficient of gas
        * Dᶰᵉ = diffusion coefficient of neon
        * β = exponent in relationship of gas transfer velocity to diffusivity in water

    See Jung and Aeschbach 2018 (https://doi.org/10.1016/j.envsoft.2018.02.004) for more details.

    ## Units
        **default units in** — `T`: °C, `S`: ‰, `p`: atm, `A`: mol/kg, `FPD`: dimensionless, `beta`: dimensionless
        **default units out** — mol_gas/kg

    Args:
        gas (Gas | str): Gas whose concentration should be calculated
        T (float | PAGOSQuantity): Temperature of the water
        S (float | PAGOSQuantity): Salinity of the water
        p (float | PAGOSQuantity): Pressure over the water
        A (float | PAGOSQuantity): Excess air
        FPD (float | PAGOSQuantity): Dimensionless diffusive gas loss parameter
        beta (float | PAGOSQuantity): Dimensionless exponent in PD model

    Returns:
        PAGOSQuantity: Concentration of gas calculated with the model
    """
    kinvisc = calc_kinvisc(T, S)
    schmidt = calc_Sc(gas, T, S)
    diff = kinvisc / schmidt
    diffNe = kinvisc / calc_Sc("Ne", T, S)
    return (calc_Ceq(gas, T, S, p) + A * abn(gas)) * np.exp(
        -FPD * (diff / diffNe) ** beta
    )


pd_model = TracerModel(pd)


@unit_aware(
    {
        "gas": None,
        "T": "degC",
        "S": "permille",
        "p": "atm",
        "A": "mol/kg",
        "POD": "dimensionless",
    },
    "mol_gas/kg",
)
def od(
    gas: Gas | str,
    T: float | PAGOSQuantity,
    S: float | PAGOSQuantity,
    p: float | PAGOSQuantity,
    A: float | PAGOSQuantity,
    POD: float | PAGOSQuantity,
) -> PAGOSQuantity:
    """Oxygen depletion (OD) model, typically for groundwater studies.
    * C = Cₑ(T, S, p)·Pᴼᴰ + Aχ
        * Cₑ(T, S, p) = equilibrium concentration at water recharge temperature T, salinity S and air pressure p
        * Pᴼᴰ = dimensionless pressure increase factor
        * A = excess air in same units as Cₑ
        * χ = atmospheric abundance of given gas

    See Jung and Aeschbach 2018 (https://doi.org/10.1016/j.envsoft.2018.02.004) for more details.

    ## Units
        **default units in** — `T`: °C, `S`: ‰, `p`: atm, `A`: mol/kg, `POD`: dimensionless
        **default units out** — mol_gas/kg

    Args:
        gas (Gas | str): Gas whose concentration should be calculated
        T (float | PAGOSQuantity): Temperature of the water
        S (float | PAGOSQuantity): Salinity of the water
        p (float | PAGOSQuantity): Pressure over the water
        A (float | PAGOSQuantity): Excess air
        POD (float | PAGOSQuantity): Pressure increase factor

    Returns:
        PAGOSQuantity: Concentration of gas calculated with the model
    """
    return calc_Ceq(gas, T, S, p) * POD + A * abn(gas)


od_model = TracerModel(od)


@unit_aware(
    {
        "gas": None,
        "T": "degC",
        "S": "permille",
        "p": "atm",
        "A": "mol/kg",
        "F": "dimensionless",
    },
    "mol_gas/kg",
)
def ce(
    gas: Gas | str,
    T: float | PAGOSQuantity,
    S: float | PAGOSQuantity,
    p: float | PAGOSQuantity,
    A: float | PAGOSQuantity,
    F: float | PAGOSQuantity,
) -> PAGOSQuantity:
    """Closed-system equilibration (CE) model, typically for groundwater studies.
    * C = Cₑ(T, S, p) + (1 − F)·Aχ / (1 + FAχ / Cₑ(T, S, p))
        * Cₑ(T, S, p) = equilibrium concentration at water recharge temperature T, salinity S and air pressure p
        * F = dimensionless fractionation factor by which the size of the gas phase has changed during re-equilibration
        * A = excess air in same units as Cₑ
        * χ = atmospheric abundance of given gas

    See Jung and Aeschbach 2018 (https://doi.org/10.1016/j.envsoft.2018.02.004) for more details.

    ## Units
        **default units in** — `T`: °C, `S`: ‰, `p`: atm, `A`: mol/kg, `F`: dimensionless
        **default units out** — mol_gas/kg

    Args:
        gas (Gas | str): Gas whose concentration should be calculated
        T (float | PAGOSQuantity): Temperature of the water
        S (float | PAGOSQuantity): Salinity of the water
        p (float | PAGOSQuantity): Pressure over the water
        A (float | PAGOSQuantity): Excess air
        F (float | PAGOSQuantity): Dimensionless fractionation factor

    Returns:
        PAGOSQuantity: Concentration of gas calculated with the model
    """
    ceq = calc_Ceq(gas, T, S, p)
    z = abn(gas)
    return ceq + (1 - F) * A * z / (1 + F * A * z / ceq)


ce_model = TracerModel(ce)
