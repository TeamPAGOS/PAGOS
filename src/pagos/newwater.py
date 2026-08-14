"""
Functions for calculating the properties of water
"""

from pagos.newconstants import GILL_82_COEFFS
from pagos.newcore import pCalc as pC


@pC.unit_aware(("delta_degC", "permille"), "kg/m^3")
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


calc_dens = pC.make_mcmethod(calc_dens, 0.0)
