"""
Functions for calculating the properties of water.
- `calc_dens()`: density
- `calc_vappres()`: vapour pressure
- `calc_kinvisc()`: kinematic viscosity
"""
from pint import Quantity, Unit
from collections.abc import Iterable
import numpy as np

from pagos.core import u as _u, sto as _sto, wraptpint
from pagos.constants import GILL_82_COEFFS
from pagos.units import *

@wraptpint(('degC', 'permille', None, None), strict=False)
def calc_dens(T:float|Quantity, S:float|Quantity, units='kg_water/m3_water', magnitude=False) -> Quantity:
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
    # NOTE: THIS FUNCTION IS DUPLICATED IN UNITS.PY TO AVOID CIRCULAR IMPORT; IF YOU CHANGE IT HERE, CHANGE IT THERE TOO
    a0, a1, a2, a3, a4, a5, b0, b1, b2, b3, b4, c0, c1, c2, d0 = GILL_82_COEFFS.values()

    rho0 = a0 + a1*T + a2*T**2 + a3*T**3 + a4*T**4 + a5*T**5
    rho = rho0 + S*(b0 + b1*T + b2*T**2 + b3*T**3 + b4*T**4) + \
          (S**(3/2))*(c0 + c1*T + c2*T**2) + \
          d0*S**2
    
    global DENSUNIT_CACHE
    id = hash(units)
    if cache_hit := DENSUNIT_CACHE.get(id): # if the hashed unit is in our cache...
        compat_unit, unconverted_unit, unit_change = cache_hit # access the relevant values in the cache
    else:
        if not isinstance(units, Unit):  # create pint.Unit object from unit string argument
            units = _u.Unit(units)
        
        dmly = units.dimensionality
        if dmly == uww_kg_m3.dimensionality:
            compat_unit = UEnum.WW_KG_M3
            unconverted_unit = uww_kg_m3
        else:
            raise ValueError(f"Invalid/unimplemented value for unit ({units}). Try something like \'kg_w/m3_w\'.")
        
        unit_change = unconverted_unit != units
        DENSUNIT_CACHE[id] = (compat_unit, unconverted_unit, unit_change) # add the units to the cache if it's not already there
    
    # return density with desired units
    if compat_unit == UEnum.WW_KG_M3:
        ret = rho
    else:
        raise ValueError(f"Invalid/unimplemented value for unit ({units}). Try something like \'kg_w/m3_w\'.")

    # return, after conversion if necessary - written like this to avoid _sto() for speed reasons
    if magnitude and not unit_change:
        return ret
    elif magnitude:
        return _sto(ret * unconverted_unit, units).magnitude
    elif not unit_change:
        return ret * unconverted_unit
    else:
        return _sto(ret * unconverted_unit, units)
    

@wraptpint(('degC', None, None), strict=False)
def calc_vappres(T:float|Quantity, units='mbar', magnitude=False) -> Quantity:
    """Calculate water vapour pressure over seawater at given temperature, according to Dyck and Peschke 1995.\\
    **Default input units** --- `T`:°C\\
    **Output units** --- mbar

    :param T: Temperature
    :type T: float | Quantity
    :return: Calculated water vapour pressure
    :rtype: Quantity
    """
    pv = 6.1078 * 10 ** ((7.567 * T) / (T + 239.7))

    global VPUNIT_CACHE
    id = hash(units)
    if cache_hit := VPUNIT_CACHE.get(id): # if the hashed unit is in our cache...
        compat_unit, unconverted_unit, unit_change = cache_hit # access the relevant values in the cache
    else:
        if not isinstance(units, Unit):  # create pint.Unit object from unit string argument
            units = _u.Unit(units)
        
        dmly = units.dimensionality
        if dmly == u_mbar.dimensionality:
            compat_unit = UEnum.MBAR
            unconverted_unit = u_mbar
        else:
            raise ValueError(f"Invalid/unimplemented value for unit ({units}). Try something like \'mbar\'.")
        
        unit_change = unconverted_unit != units
        VPUNIT_CACHE[id] = (compat_unit, unconverted_unit, unit_change) # add the units to the cache if it's not already there
    
    # return vapour pressure with desired units
    if compat_unit == UEnum.MBAR:
        ret = pv
    else:
        raise ValueError(f"Invalid/unimplemented value for unit ({units}). Try something like \'mbar\'.")

    # return, after conversion if necessary - written like this to avoid _sto() for speed reasons
    if magnitude and not unit_change:
        return ret
    elif magnitude:
        return _sto(ret * unconverted_unit, units).magnitude
    elif not unit_change:
        return ret * unconverted_unit
    else:
        return _sto(ret * unconverted_unit, units)


@wraptpint(('degC', 'permille', None, None), strict=False)
def calc_kinvisc(T:float|Quantity, S:float|Quantity, units='m^2/s', magnitude=False) -> Quantity:
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
    rho = calc_dens(T, S, magnitude=True) # kg/m3, take magnitude for speed
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
    
    global KVUNIT_CACHE
    id = hash(units)
    if cache_hit := KVUNIT_CACHE.get(id): # if the hashed unit is in our cache...
        compat_unit, unconverted_unit, unit_change = cache_hit # access the relevant values in the cache
    else:
        if not isinstance(units, Unit):  # create pint.Unit object from unit string argument
            units = _u.Unit(units)
        
        dmly = units.dimensionality
        if dmly == u_m2_s.dimensionality:
            compat_unit = UEnum.M2_S
            unconverted_unit = u_m2_s
        else:
            raise ValueError(f"Invalid/unimplemented value for unit ({units}). Try something like \'m^2/s\'.")
        
        unit_change = unconverted_unit != units
        KVUNIT_CACHE[id] = (compat_unit, unconverted_unit, unit_change) # add the units to the cache if it's not already there
    
    # return density with desired units
    if compat_unit == UEnum.M2_S:
        ret = nu_sw
    else:
        raise ValueError(f"Invalid/unimplemented value for unit ({units}). Try something like \'m^2/s\'.")

    # return, after conversion if necessary - written like this to avoid _sto() for speed reasons
    if magnitude and not unit_change:
        return ret
    elif magnitude:
        return _sto(ret * unconverted_unit, units).magnitude
    elif not unit_change:
        return ret * unconverted_unit
    else:
        return _sto(ret * unconverted_unit, units)


@wraptpint(('degC', 'permille', None, None), strict=False)
def calc_dens_Tderiv(T:float|Quantity, S:float|Quantity, units='kg_water/m3_water/K', magnitude=False) -> Quantity:
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
    
    global DT_DENSUNIT_CACHE
    id = hash(units)
    if cache_hit := DT_DENSUNIT_CACHE.get(id): # if the hashed unit is in our cache...
        compat_unit, unconverted_unit, unit_change = cache_hit # access the relevant values in the cache
    else:
        if not isinstance(units, Unit):  # create pint.Unit object from unit string argument
            units = _u.Unit(units)
        
        dmly = units.dimensionality
        if dmly == uww_kg_m3_K.dimensionality:
            compat_unit = UEnum.WW_KG_M3_K
            unconverted_unit = uww_kg_m3_K
        else:
            raise ValueError(f"Invalid/unimplemented value for unit ({units}). Try something like \'kg_w/m3_w/K\'.")
        
        unit_change = unconverted_unit != units
        DT_DENSUNIT_CACHE[id] = (compat_unit, unconverted_unit, unit_change) # add the units to the cache if it's not already there
    
    # return density with desired units
    if compat_unit == UEnum.WW_KG_M3_K:
        ret = drhodT
    else:
        raise ValueError(f"Invalid/unimplemented value for unit ({units}). Try something like \'kg_w/m3_w/K\'.")

    # return, after conversion if necessary - written like this to avoid _sto() for speed reasons
    if magnitude and not unit_change:
        return ret
    elif magnitude:
        return _sto(ret * unconverted_unit, units).magnitude
    elif not unit_change:
        return ret * unconverted_unit
    else:
        return _sto(ret * unconverted_unit, units)


@wraptpint(('degC', 'permille', None, None), strict=False)
def calc_dens_Sderiv(T:float|Quantity, S:float|Quantity, units='kg_water/m3_water/permille', magnitude=False) -> Quantity:
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

    global DS_DENSUNIT_CACHE
    id = hash(units)
    if cache_hit := DS_DENSUNIT_CACHE.get(id): # if the hashed unit is in our cache...
        compat_unit, unconverted_unit, unit_change = cache_hit # access the relevant values in the cache
    else:
        if not isinstance(units, Unit):  # create pint.Unit object from unit string argument
            units = _u.Unit(units)
        
        dmly = units.dimensionality
        if dmly == uww_kg_m3_pml.dimensionality:
            compat_unit = UEnum.WW_KG_M3_PML
            unconverted_unit = uww_kg_m3_pml
        else:
            raise ValueError(f"Invalid/unimplemented value for unit ({units}). Try something like \'kg_w/m3_w/permille\'.")
        
        unit_change = unconverted_unit != units
        DS_DENSUNIT_CACHE[id] = (compat_unit, unconverted_unit, unit_change) # add the units to the cache if it's not already there
    
    # return density with desired units
    if compat_unit == UEnum.WW_KG_M3_PML:
        ret = drhodS
    else:
        raise ValueError(f"Invalid/unimplemented value for unit ({units}). Try something like \'kg_w/m3_w/permille\'.")

    # return, after conversion if necessary - written like this to avoid _sto() for speed reasons
    if magnitude and not unit_change:
        return ret
    elif magnitude:
        return _sto(ret * unconverted_unit, units).magnitude
    elif not unit_change:
        return ret * unconverted_unit
    else:
        return _sto(ret * unconverted_unit, units)


@wraptpint(('degC', None, None), strict=False)
def calc_vappres_Tderiv(T:float|Quantity, units='mbar/K', magnitude=False) -> Quantity:
    """Calculate temperature-derivative of water vapour pressure (de/dT) over seawater at given temperature, according to Dyck and Peschke 1995.\\
    **Default input units** --- `T`:°C\\
    **Output units** --- mbar/K

    :param T: Temperature
    :type T: float | Quantity
    :return: Calculated de/dT
    :rtype: Quantity
    """
    pv = calc_vappres(T, magnitude=True)
    dpv_dT = 553919405361 * np.log(10) * pv / 3053900 / (10 * T + 2397)**2
    
    global DT_VPUNIT_CACHE
    id = hash(units)
    if cache_hit := DT_VPUNIT_CACHE.get(id): # if the hashed unit is in our cache...
        compat_unit, unconverted_unit, unit_change = cache_hit # access the relevant values in the cache
    else:
        if not isinstance(units, Unit):  # create pint.Unit object from unit string argument
            units = _u.Unit(units)
        
        dmly = units.dimensionality
        if dmly == u_mbar_K.dimensionality:
            compat_unit = UEnum.MBAR_K
            unconverted_unit = u_mbar_K
        else:
            raise ValueError(f"Invalid/unimplemented value for unit ({units}). Try something like \'mbar/K\'.")
        
        unit_change = unconverted_unit != units
        DT_VPUNIT_CACHE[id] = (compat_unit, unconverted_unit, unit_change) # add the units to the cache if it's not already there
    
    # return vapour pressure with desired units
    if compat_unit == UEnum.MBAR_K:
        ret = dpv_dT
    else:
        raise ValueError(f"Invalid/unimplemented value for unit ({units}). Try something like \'mbar/K\'.")

    # return, after conversion if necessary - written like this to avoid _sto() for speed reasons
    if magnitude and not unit_change:
        return ret
    elif magnitude:
        return _sto(ret * unconverted_unit, units).magnitude
    elif not unit_change:
        return ret * unconverted_unit
    else:
        return _sto(ret * unconverted_unit, units)