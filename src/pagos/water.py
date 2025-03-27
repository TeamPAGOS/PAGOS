"""
Functions for calculating the properties of water.
- `calc_dens()`: density
- `calc_vappres()`: vapour pressure
- `calc_kinvisc()`: kinematic viscosity
"""
from pint import Quantity
from collections.abc import Iterable
import numpy as np

from pagos.core import u as _u, wraptpint
from pagos.constants import GILL_82_COEFFS

# TODO should there be some option to not return the unit?
@wraptpint('kg/m^3', ('degC', 'permille'), strict=False)
def calc_dens(T:float|Quantity, S:float|Quantity) -> Quantity:
    """Calculate density of seawater at given temperature and salinity, according to Gill 1982.\\
    **Default input units** --- `T`:°C, `S`:‰\\
    **Output units** --- kg/m³

    :param T: Temperature
    :type T: float | Quantity
    :param S: Salinity
    :type S: float | Quantity
    :return: Calculated density
    :rtype: Quantity
    """
    a0, a1, a2, a3, a4, a5, b0, b1, b2, b3, b4, c0, c1, c2, d0 = GILL_82_COEFFS.values()

    rho0 = a0 + a1*T + a2*T**2 + a3*T**3 + a4*T**4 + a5*T**5
    ret = rho0 + S*(b0 + b1*T + b2*T**2 + b3*T**3 + b4*T**4) + \
          (S**(3/2))*(c0 + c1*T + c2*T**2) + \
          d0*S**2
    return ret


@wraptpint('mbar', 'degC', strict=False)
def calc_vappres(T:float|Quantity) -> Quantity:
    """Calculate water vapour pressure over seawater at given temperature, according to Dyck and Peschke 1995.\\
    **Default input units** --- `T`:°C\\
    **Output units** --- mbar

    :param T: Temperature
    :type T: float | Quantity
    :return: Calculated water vapour pressure
    :rtype: Quantity
    """
    pv = 6.1078 * 10 ** ((7.567 * T) / (T + 239.7))
    return pv


@wraptpint('m^2/s', ('degC', 'permille'), strict=False)
def calc_kinvisc(T:float|Quantity, S:float|Quantity) -> Quantity:
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
    # Density of the water
    rho = calc_dens(T, S, magnitude=True) # kg/m3, take magnitude for speed # TODO if calc_dens() gets an option to return magnitude, use that instead of extracting it here
    # Adapt salinity to reference composition salinity in kg/kg (Sharqawy 2010)
    S_R = 1.00472*S / 1000 # permille -> kg/kg
    # Viscosity calculated following Sharqawy 2010
    mu_fw = (4.2844e-5 + 1/(0.157*(T + 64.993)**2 - 91.296)) #would need ITS-90 as temperature
    A = 1.541 + 0.01998*T - 9.52e-5*T**2
    B = 7.974 - 0.07561*T + 4.724e-4*T**2
    # saltwater dynamic viscosity
    mu_sw = mu_fw * (1 + A * S_R + B * S_R ** 2) # kg/m/s
    # saltwater kinematic viscosity
    nu_sw = mu_sw / rho # m2/s
    
    return nu_sw


@wraptpint('kg/m^3/K', ('degC', 'permille'), strict=False)
def calc_dens_Tderiv(T:float|Quantity, S:float|Quantity) -> Quantity:
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
    drhodT = a1 + 2*a2*T + 3*a3*T**2 + 4*a4*T**3 + 5*a5*T**4 + \
             S*(b1 + 2*b2*T + 3*b3*T**2 + 4*b4*T**3) + \
             S**(3/2)*(c1 + 2*c2*T)
    return drhodT


@wraptpint('kg/m^3/permille', ('degC', 'permille'), strict=False)
def calc_dens_Sderiv(T:float|Quantity, S:float|Quantity) -> Quantity:
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
    drhodS = b0 + b1*T + b2*T**2 + b3*T**3 + b4*T**4 + \
             3/2 * S**(1/2) * (c0 + c1*T + c2*T**2) + \
             2 * d0 * S
    return drhodS


@wraptpint('mbar/K', 'degC', strict=False)
def calc_vappres_Tderiv(T:float|Quantity) -> Quantity:
    """Calculate temperature-derivative of water vapour pressure (de/dT) over seawater at given temperature, according to Dyck and Peschke 1995.\\
    **Default input units** --- `T`:°C\\
    **Output units** --- mbar/K

    :param T: Temperature
    :type T: float | Quantity
    :return: Calculated de/dT
    :rtype: Quantity
    """
    pv = calc_vappres(T, magnitude=True)
    dpv_dT = pv * np.log(10) * 11078.38810722 / (1 + 239.7)**2
    return dpv_dT