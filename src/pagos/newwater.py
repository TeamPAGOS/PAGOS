"""
Functions for calculating the properties of water
"""

from pagos.newconstants import (
    DYCK_PESCHKE_95_COEFFS,
    GILL_82_COEFFS,
    SHARQAWY_10_COEFFS,
)
from pagos.newcore import PAGOSQuantity, mc_possible, unit_aware


@unit_aware({"T": "degC", "S": "permille"}, "kg/m^3")
def calc_dens(T: float | PAGOSQuantity, S: float | PAGOSQuantity) -> PAGOSQuantity:
    """Calculate density of seawater at a given temperature and salinity, according to Gill 1982.

    ## Units
        **default units in** — `T`:°C, `S`:‰
        **default units out** — kg/m³

    Args:
        T (float | PAGOSQuantity): Temperature
        S (float | PAGOSQuantity): Salinity

    Returns:
        PAGOSQuantity: Calculated density
    """

    a0, a1, a2, a3, a4, a5, b0, b1, b2, b3, b4, c0, c1, c2, d0 = GILL_82_COEFFS.values()
    rho0 = a0 + a1 * T + a2 * T**2 + a3 * T**3 + a4 * T**4 + a5 * T**5
    rho = (
        rho0
        + S * (b0 + b1 * T + b2 * T**2 + b3 * T**3 + b4 * T**4)
        + (S ** (3 / 2)) * (c0 + c1 * T + c2 * T**2)
        + d0 * S**2
    )
    return rho


@unit_aware({"T": "degC"}, "mbar")
def calc_vappres(T: float | PAGOSQuantity) -> PAGOSQuantity:
    """Calculate water vapour pressure over seawater at given temperature, according to Dyck and Peschke 1995.

    ## Units
        **default units in** — `T`:°C
        **default units out** — mbar

    Args:
        T (float | PAGOSQuantity): Temperature

    Returns:
        PAGOSQuantity: Calculated water vapour pressure
    """
    p0, c = DYCK_PESCHKE_95_COEFFS["p0"], DYCK_PESCHKE_95_COEFFS["c"]
    pv = p0 * 10 ** ((7.567 * T) / (T + c))
    return pv


@unit_aware({"T": "degC", "S": "permille"}, "m^2/s")
def calc_kinvisc(T: float | PAGOSQuantity, S: float | PAGOSQuantity) -> PAGOSQuantity:
    """Calculate kinematic viscosity of seawater at given temperature and salinity, according to Sharqawy 2010.

    ## Units
        **default units in** — `T`:°C, `S`:‰
        **default units out** — m²/s

    Args:
        T (float | PAGOSQuantity): Temperature
        S (float | PAGOSQuantity): Salinity

    Returns:
        PAGOSQuantity: Kinematic viscosity
    """
    m0, m1, m2, m3, a1, a2, b1, b2 = SHARQAWY_10_COEFFS.values()
    # Density of the water
    rho = calc_dens(T, S)  # kg/m3
    # Adapt salinity to reference composition salinity (Sharqawy 2010)
    S_R = 1.00472 * S
    # Viscosity calculated following Sharqawy 2010
    mu_fw = m0 + m1 / (m2 * (T + m3) ** 2 - 91.296)  # would need ITS-90 as temperature
    A = 1.541 + a1 * T - a2 * T**2
    B = 7.974 - b1 * T + b2 * T**2
    # saltwater dynamic viscosity
    mu_sw = mu_fw * (1 + A * S_R + B * S_R**2)  # kg/m/s
    # saltwater kinematic viscosity
    nu_sw = mu_sw / rho
    return nu_sw


@unit_aware({"T": "degC", "S": "permille"}, "kg/m^3/K")
def calc_dens_Tderiv(
    T: float | PAGOSQuantity,
    S: float | PAGOSQuantity,
) -> PAGOSQuantity:
    """Calculate temperature-derivative of the density (dρ/dT) of seawater at given temperature and salinity, according to Gill 1982.

    ## Units:
        **Default input units** — `T`:°C, `S`:‰
        **Output units** — kg/m³/K

    Args:
        T (float | PAGOSQuantity): Temperature
        S (float | PAGOSQuantity): Salinity

    Returns:
        PAGOSQuantity: Calculated dρ/dT
    """
    a0, a1, a2, a3, a4, a5, b0, b1, b2, b3, b4, c0, c1, c2, d0 = GILL_82_COEFFS.values()
    drhodT = (
        a1
        + 2 * a2 * T
        + 3 * a3 * T**2
        + 4 * a4 * T**3
        + 5 * a5 * T**4
        + S * (b1 + 2 * b2 * T + 3 * b3 * T**2 + 4 * b4 * T**3)
        + S ** (3 / 2) * (c1 + 2 * c2 * T)
    )
    return drhodT


@unit_aware({"T": "degC", "S": "permille"}, "kg/m^3/permille")
def calc_dens_Sderiv(
    T: float | PAGOSQuantity,
    S: float | PAGOSQuantity,
) -> PAGOSQuantity:
    """Calculate salinity-derivative of the density (dρ/dS) of seawater at given temperature and salinity, according to Gill 1982.

    ## Units
        **default units in** — `T`:°C, `S`:‰
        **default units out** — kg/m³/permille

    Args:
        T (float | PAGOSQuantity): Temperature
        S (float | PAGOSQuantity): Salinity

    Returns:
        PAGOSQuantity: Calculated dρ/dS
    """
    a0, a1, a2, a3, a4, a5, b0, b1, b2, b3, b4, c0, c1, c2, d0 = GILL_82_COEFFS.values()
    drhodS = (
        b0
        + b1 * T
        + b2 * T**2
        + b3 * T**3
        + b4 * T**4
        + 3 / 2 * S ** (1 / 2) * (c0 + c1 * T + c2 * T**2)
        + 2 * d0 * S
    )
    return drhodS


@unit_aware({"T": "degC"}, "mbar/K")
def calc_vappres_Tderiv(T: float | PAGOSQuantity) -> PAGOSQuantity:
    """Calculate temperature-derivative of water vapour pressure (de/dT) over seawater at given temperature, according to Dyck and Peschke 1995.

    ## Units
        **default units in** — `T`:°C
        **default units out** — mbar/K

    Args:
        T (float | PAGOSQuantity): Temperature

    Returns:
        PAGOSQuantity: Calculated de/dT
    """

    p0, c = DYCK_PESCHKE_95_COEFFS["p0"], DYCK_PESCHKE_95_COEFFS["c"]
    pv = p0 * 10 ** ((7.567 * T) / (T + c))
    dpv_dT = 17.423661398685947 * pv * c / (T + c) ** 2
    return dpv_dT


calc_dens = mc_possible(0.0)(calc_dens)
calc_vappres = mc_possible(0.0)(calc_vappres)
calc_kinvisc = mc_possible(0.0)(calc_kinvisc)
calc_dens_Tderiv = mc_possible(0.0)(calc_dens_Tderiv)
calc_dens_Sderiv = mc_possible(0.0)(calc_dens_Sderiv)
calc_vappres_Tderiv = mc_possible(0.0)(calc_vappres_Tderiv)
