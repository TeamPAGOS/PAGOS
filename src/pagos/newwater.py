"""
Functions for calculating the properties of water
"""

from pagos.newconstants import (
    DYCK_PESCHKE_95_COEFFS,
    GILL_82_COEFFS,
    SHARQAWY_10_COEFFS,
)
from pagos.newcore import pCalc as pC


@pC.unit_aware(("degC", "permille"), "kg/m^3")
def calc_dens(T: float, S: float) -> float:
    """
    Calculate density of seawater at a given temperature and salinity, according to Gill 1982.\\
    **Default input units** --- `T`:°C, `S`:‰\\
    **Output units** --- kg/m³

    :param T: Temperature
    :type T: float
    :param S: Salinity
    :type S: float
    :return: Calculated density
    :rtype: float
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


@pC.unit_aware(("degC",), "mbar")
def calc_vappres(T: float) -> float:
    """Calculate water vapour pressure over seawater at given temperature, according to Dyck and Peschke 1995.\\
    **Default input units** --- `T`:°C\\
    **Output units** --- mbar

    :param T: Temperature
    :type T: float
    :return: Calculated water vapour pressure
    :rtype: float
    """
    p0, c = DYCK_PESCHKE_95_COEFFS["p0"], DYCK_PESCHKE_95_COEFFS["c"]
    pv = p0 * 10 ** ((7.567 * T) / (T + c))
    return pv


@pC.unit_aware(("degC", "permille"), "m^2/s")
def calc_kinvisc(T: float, S: float) -> float:
    """Calculate kinematic viscosity of seawater at given temperature and salinity, according to Sharqawy 2010.\\
    **Default input units** --- `T`:°C, `S`:‰\\
    **Output units** --- m²/s

    :param T: Temperature
    :type T: float | Quantity
    :param S: Salinity
    :type S: float | Quantity
    :return: Calculated kinematic viscosity
    :rtype: Quantity
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


@pC.unit_aware(("degC", "permille"), "kg/m^3/K")
def calc_dens_Tderiv(
    T: float,
    S: float,
) -> float:
    """Calculate temperature-derivative of the density (dρ/dT) of seawater at given temperature and salinity, according to Gill 1982.\\
    **Default input units** --- `T`:°C, `S`:‰\\
    **Output units** --- kg/m³/K

    :param T: Temperature
    :type T: float | Quantity
    :param S: Salinity
    :type S: float | Quantity
    :return: Calculated dρ/dT
    :rtype: Quantity
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


@pC.unit_aware(("degC", "permille"), "kg/m^3/permille")
def calc_dens_Sderiv(
    T: float,
    S: float,
) -> float:
    """Calculate salinity-derivative of the density (dρ/dS) of seawater at given temperature and salinity, according to Gill 1982.\\
    **Default input units** --- `T`:°C, `S`:‰\\
    **Output units** --- kg/m³/permille

    :param T: Temperature
    :type T: float | Quantity
    :param S: Salinity
    :type S: float | Quantity
    :return: Calculated dρ/dS
    :rtype: Quantity
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


@pC.unit_aware(("degC",), "mbar/K")
def calc_vappres_Tderiv(T: float) -> float:
    """Calculate temperature-derivative of water vapour pressure (de/dT) over seawater at given temperature, according to Dyck and Peschke 1995.\\
    **Default input units** --- `T`:°C\\
    **Output units** --- mbar/K

    :param T: Temperature
    :type T: float | Quantity
    :return: Calculated de/dT
    :rtype: Quantity
    """

    p0, c = DYCK_PESCHKE_95_COEFFS["p0"], DYCK_PESCHKE_95_COEFFS["c"]
    pv = p0 * 10 ** ((7.567 * T) / (T + c))
    dpv_dT = 17.423661398685947 * pv * c / (T + c) ** 2
    return dpv_dT


calc_dens = pC.make_mcmethod(calc_dens, 0.0)
calc_vappres = pC.make_mcmethod(calc_vappres, 0.0)
calc_kinvisc = pC.make_mcmethod(calc_kinvisc, 0.0)
calc_dens_Tderiv = pC.make_mcmethod(calc_dens_Tderiv, 0.0)
calc_dens_Sderiv = pC.make_mcmethod(calc_dens_Sderiv, 0.0)
calc_vappres_Tderiv = pC.make_mcmethod(calc_vappres_Tderiv, 0.0)
