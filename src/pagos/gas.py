"""
Functions for calculating the properties of various gases.
"""
#TODO make a document in the README or something explaining all conventions we assume
# for example, that for us, STP = 0 degC 1 atm instead of 20 degC 1 atm.
from pint import Quantity
from pint import Unit
import numpy as np
from collections.abc import Iterable

from pagos.core import u as _u, sto as _sto, _possibly_iterable, wraptpint
from pagos.constants import NOBLEGASES, STABLETRANSIENTGASES, BIOLOGICALGASES
from pagos.constants import NG_JENKINS_19_COEFFS, WANNINKHOF_92_COEFFS, EYRING_36_COEFFS, CFC_WARNERWEISS_85_COEFFS, SF6_BULLISTER_02_COEFFS, ArNeN2_HAMMEEMERSON_04
from pagos.constants import ABUNDANCES, MOLAR_VOLUMES, MOLAR_MASSES, ICE_FRACTIONATION_COEFFS, MGC, TPW, PAT, MMW
from pagos.water import calc_dens, calc_dens_Tderiv, calc_dens_Sderiv, calc_kinvisc, calc_vappres, calc_vappres_Tderiv
from pagos.units import *

def hasgasprop(gas:str, condition:str) -> bool:
    """
    Returns True if the gas fulfils the condition specified by arguments `condition`.

    :param str gas:  Gas species to be checked.
    :param str condition:
        Condition to be checked, e.g. condition='isstabletransient' checks if the gas is a stable transient gas (e.g. SF6 or CFC12).
        possible conditions are 'spcis' (needs the species in specific), 'isnoble', 'isng', 'isstabletransient', 'isst'
    :return bool:
        Truth value of the condition.
    """
    if condition in ['isnoble', 'isng']:
        if gas in NOBLEGASES:
            return True
        else:
            return False
    if condition in ['isstabletransient', 'isst']:
        if gas in STABLETRANSIENTGASES:
            return True
        else:
            return False
    else: 
        raise ValueError("%s is not a valid condition." % (condition))
    
"""
GETTERS
"""
@_possibly_iterable
def jkc(gas:str|Iterable[str]) -> dict[float]|Iterable[dict[float]]:
    """Get a dictionary of the Jenkins 2019 solubility equation coefficients of the gas:
    {A1, A2, A3, A4, B1, B2, B3, C1}.

    :param gas: Gas whose Jenkins coefficients are to be returned.
    :type gas: str | Iterable[str]
    :raises AttributeError: If the given gas is not noble.
    :return: Dictionary of gas's Jenkins coefficients.
    :rtype: dict[float]|Iterable[dict[float]]
    """    
    try:
        return NG_JENKINS_19_COEFFS[gas]
    except:
        print("Only noble gases have Jenkins coefficients.")


@_possibly_iterable
def wkc(gas:str|Iterable[str]) -> dict[float]|Iterable[dict[float]]:
    """Get a dictionary of the Wanninkhof 1992 Schmidt number equation coefficients of the
    gas: {A, B, C, D}.
    NOTE: for xenon, the W92 formula has been estimated by fitting the Eyring diffusivity
    curve from Jähne et al. 1987 to the W92 formula and using the coefficients of best fit.

    :param gas: Gas whose Wanninkhof coefficients are to be returned.
    :type gas: str | Iterable[str]
    :return: Dictionary of gas's Wanninkhof coefficients.
    :rtype: dict[float]|Iterable[dict[float]]
    """
    try:
        return WANNINKHOF_92_COEFFS[gas]
    except:
        print("Only noble gases, CFCs, SF6 and N2 have Wanningkhof coefficients.")


@_possibly_iterable
def erc(gas:str|Iterable[str]) -> dict[float]|Iterable[dict[float]]:
    """Get a dictionary of the Eyring 1936 coeffs {A, Ea} for the diffusivity. Noble gas
    coefficients from Jähne 1987, except argon, interpolated from Wanninkhof 1992. N2 is
    from Ferrel and Himmelblau 1967.

    :param gas: Gas whose Eyring coefficients are to be returned.
    :type gas: str | Iterable[str]
    :return: Dictionary of gas's Eyring coefficients.
    :rtype: dict[float]|Iterable[dict[float]]
    """
    try:
        return EYRING_36_COEFFS[gas]
    except:
        print("Only noble gases and N2 have Eyring coefficients.")


@_possibly_iterable
def mv(gas:str|Iterable[str]) -> float|Iterable[float]:
    """Get the molar volume of the given gas at STP in cm3/mol.

    :param gas: Gas whose molar volume is to be returned.
    :type gas: str | Iterable[str]
    :return: STP molar volume of given gas in cm3/mol.
    :rtype: float|Iterable[float]
    """
    try:
        return MOLAR_VOLUMES[gas]
    except:
        print("The given gas does not have a corresponding molar volume in PAGOS.")


@_possibly_iterable
def mm(gas:str|Iterable[str]) -> float|Iterable[float]:
    """Get the molar mass of the given gas in g/mol.

    :param gas: Gas whose molar mass is to be returned.
    :type gas: str | Iterable[str]
    :return: Molar mass of given gas in g/mol.
    :rtype: float|Iterable[float]
    """
    try:
        return MOLAR_MASSES[gas]
    except:
        print("The given gas does not have a corresponding molar mass in PAGOS.")


@_possibly_iterable
def wwc(gas:str|Iterable[str]) -> dict[float]|Iterable[dict[float]]:
    """Get a dictionary of the Warner and Weiss 1985 equation coefficients of the gas:
    {a1, a2, a3, a4, b1, b2, b3}.

    :param gas: Gas whose Warner/Weiss coefficients are to be returned.
    :type gas: str | Iterable[str]
    :return: Dictionary of gas's Warner/Weiss coefficients.
    :rtype: dict[float]|Iterable[dict[float]]
    """
    try:
        return CFC_WARNERWEISS_85_COEFFS[gas]
    except:
        print("The given gas does not have corresponding Warner-Weiss-1985-coefficients in PAGOS.")


@_possibly_iterable
def abn(gas:str|Iterable[str]) -> float|Iterable[float]:
    """Get the atmospheric abundance of the given gas.

    :param gas: Gas whose abundance is to be returned.
    :type gas: str | Iterable[str]
    :return: Atmospheric abundance of given gas.
    :rtype: float|Iterable[float]
    """    
    try:
        return ABUNDANCES[gas]
    except:
        print("The given gas does not have a corresponding abundance in PAGOS.")


@_possibly_iterable
def blc(gas:str|Iterable[str]) -> dict[float]|Iterable[dict[float]]:
    """Get a dictionary of the Bullister 2002 equation coefficients of the gas:
    {a1, a2, a3, b1, b2, b3}.

    :param gas: Gas whose Bullister coefficients are to be returned.
    :type gas: str | Iterable[str]
    :return: Dictionary of gas's Bullister coefficients.
    :rtype: dict[float]|Iterable[dict[float]]
    """
    try:
        return SF6_BULLISTER_02_COEFFS[gas]
    except:
        print("The given gas does not have corresponding Bullister-2002-coefficients in PAGOS.")


@_possibly_iterable
def hec(gas:str|Iterable[str]) -> dict[float]|Iterable[dict[float]]:
    """Get a dictionary of the Hamme and Emerson 2004 equation coefficients of the gas:
    {A0, A1, A2, A3, B0, B1, B2}.

    :param gas: Gas whose Hamme/Emerson coefficients are to be returned
    :type gas: str | Iterable[str]
    :return: Dictionary of gas's Hamme/Emerson coefficients.
    :rtype: dict[float]|Iterable[dict[float]]
    """    
    try:
        return ArNeN2_HAMMEEMERSON_04[gas]
    except:
        print("The given gas does not have corresponding Hamme-Emerson-2004-coefficients in PAGOS.")


@_possibly_iterable
def ice(gas:str|Iterable[str]) -> float|Iterable[float]:
    """
    Get the ice fractionation coefficient of the given gas from Loose et al. 2020.

    :param gas: Gas whose ice fractionation coefficient is to be returned.
    :type gas: str | Iterable[str]
    :return: Ice fractionation coefficient of given gas.
    :rtype: float|Iterable[float]
    """
    try:
        return ICE_FRACTIONATION_COEFFS[gas]
    except:
        print("The given gas does not have corresponding ice fractionation coefficients in PAGOS.")


"""
PROPERTY CALCULATIONS
"""
@_possibly_iterable
@wraptpint((None, 'degC', 'permille', None, None, None), False)
def calc_Sc(gas:str|Iterable[str], T:float|Quantity, S:float|Quantity, method:str='auto', units='dimensionless', magnitude=False) -> Quantity|Iterable[Quantity]:
    """Calculates the Schmidt number Sc of given gas in seawater.\\
    **Default input units** --- `T`:°C, `S`:‰\\
    **Output units** --- dimensionless\\
    There are three methods of calculation:
        - 'HE17'
            - Hamme and Emerson 2017, combination of various methods.
            - Based off of Roberta Hamme's Matlab scripts, available at
              https://oceangaseslab.uvic.ca/download.html.
        - 'W92'
            - Wanninkhof 1992
            - Threshold between fresh and salty water chosen to be S = 5 g/kg, but isn't
              well defined, so this method is best used only for waters with salinities
              around 34 g/kg.
        - 'auto':
            - Default to HE17
            - Transient stable gases (CFCs and SF6) use W92 because required data for HE17
              with these gases are not available.

    :param gas: Gas(es) for which Sc should be calculated
    :type gas: str | Iterable[str]
    :param T: Temperature
    :type T: float | Quantity
    :param S: Salinity
    :type S: float | Quantity
    :param method: Sc calculation method, defaults to 'auto'
    :type method: str, optional
    :raises ValueError: if `S` < 0
    :raises ValueError: if invalid `method` is given
    :return: Calculated Schmidt number
    :rtype: float | Quantity | Iterable[float] | Iterable[Quantity]
    """    

    if method == 'auto':
        if hasgasprop(gas, 'isst'):
            method = 'W92'
        else:
            method = 'HE17'

    # Wanninkhof 1992 method
    if method == 'W92':
        # salt factor for if the water is salty or not. Threshold is low, therefore this method is only recommended
        # for waters with salinity approx. equal to 34 g/kg.
        if S > 5:
            saltfactor = (1.052 + 1.3e-3*T + 5e-6*T**2 - 5e-7*T**3)/0.94
        elif 0 <= S <= 5:
            saltfactor = 1
        else:
            raise ValueError("S must be a number >= 0.")
        (A, B, C, D) = (wkc(gas)[s] for s in ["A", "B", "C", "D"])
        Sc = saltfactor*(A - B*T + C*T**2 - D*T**3)
    # Hamme & Emerson 2017 method
    elif method == 'HE17':
        # Eyring diffusivity calculation
        # units (cm2/s, kJ/mol)
        (A_coeff, activation_energy)  = (erc(gas)[s] for s in ["A", "Ea"])
        # *1000 in exponent to convert kJ/J to J/J
        D0 = A_coeff * np.exp(-activation_energy/(MGC * (T + TPW))*1000) # -> cm2/s
        # Saltwater correction used by R. Hamme in her Matlab script (https://oceangaseslab.uvic.ca/download.html)
        # *1e-4 to convert cm2/s to m2/s
        D = D0 * (1 - 0.049 * S / 35.5) * 1e-4 #PSS78 as Salinity
        # Kinematic viscosity calculation
        nu_sw = calc_kinvisc(T, S, magnitude=True)
        Sc = nu_sw / D
    else:
        raise ValueError("%s is not a valid method. Try 'auto', 'HE17' or 'W92'" % (method))
    
    global SCUNIT_CACHE
    id = hash(units)
    if cache_hit := SCUNIT_CACHE.get(id): # if the hashed unit is in our cache...
        compat_unit, unconverted_unit, unit_change = cache_hit # access the relevant values in the cache
    else:
        if not isinstance(units, Unit):  # create pint.Unit object from unit string argument
            units = _u.Unit(units)
        
        dmly = units.dimensionality
        if dmly == u_dimless.dimensionality: 
            compat_unit = UEnum.DIMLESS
            unconverted_unit = u_dimless
        else:
            raise ValueError(f"Invalid/unimplemented value for unit ({units}). Currently, only dimensionless units are supported for Schmidt number")
        
        unit_change = unconverted_unit != units
        SCUNIT_CACHE[id] = (compat_unit, unconverted_unit, unit_change) # add the unit to the cache if it's not already there

    # return H with desired units
    if compat_unit == UEnum.DIMLESS:
        ret = Sc
    else:
        raise ValueError(f"Invalid/unimplemented value for unit ({units}). Currently, only dimensionless units are supported for  Schmidt number")
    
    # return, after conversion if necessary - written like this to avoid _sto() for speed reasons
    if magnitude and not unit_change:
        return ret
    elif magnitude:
        return _sto(ret * unconverted_unit, units).magnitude
    elif not unit_change:
        return ret * unconverted_unit
    else:
        return _sto(ret * unconverted_unit, units)


def calc_Cstar(gas:str, T:float|Quantity, S:float|Quantity, ab='default') -> float: # TODO calc_Cstar returns a single-valued array due to unumpy... why did I use unumpy here again?
    """Calculate the moist atmospheric equilibrium concentration C* in mol/kg of a given gas at
    temperature T and salinity S.\\
    **Default input units** --- `T`:°C, `S`:‰\\
    **Output units** --- None\\
    C* = waterside gas concentration when the total water
    vapour-saturated atmospheric pressure is 1 atm (see Solubility of Gases in Water, W.
    Aeschbach-Hertig, Jan. 2004).

    :param gas: Gas for which C* should be calculated
    :type gas: str
    :param T: Temperature
    :type T: float | Quantity
    :param S: Salinity
    :type S: float | Quantity
    :return: Moist atmospheric equilibrium concentration C* of the given gas
    :rtype: Quantity
    """
    # calculation of C* (units mol/kg)
    T_K = T + TPW
    if hasgasprop(gas, 'isnoble'):
        A1, A2, A3, A4, B1, B2, B3, C1 = jkc(gas).values() #needs S in PSS78
        # C*, concentration calculated from Jenkins et al. 2019
        Cstar = np.exp(A1 + A2*100/T_K + A3*np.log(T_K/100) + A4*(T_K/100)
                        + S*(B1 + B2 * T_K/100 + B3 * (T_K/100)**2)
                        + C1*S**2)
    elif gas in ['CFC11', 'CFC12']:
        a1, a2, a3, a4, b1, b2, b3 = wwc(gas).values() #needs S in parts per thousand
        #TODO adopt for absolute salinity??
        # abundance
        if ab == 'default':
            ab = abn(gas)
        else:
            ab = ab
        # C* = F*abundance, concentration calculated from Warner and Weiss 1985
        Cstar = np.exp(a1 + a2*100/T_K + a3*np.log(T_K/100) + a4*(T_K/100)**2
                        + S*(b1 + b2*T_K/100 + b3*(T_K/100)**2)) * ab
    elif gas == 'SF6':
        a1, a2, a3, b1, b2, b3 = blc(gas).values() #don't know salinity unit
        # abundance
        if ab == 'default':
            ab = abn(gas)
        else:
            ab = ab
        # C* = F*abundance, concentration calculated from Bullister et al. 2002
        Cstar = np.exp(a1 + a2*(100/T_K) + a3*np.log(T_K/100)
                        + S*(b1 + b2*T_K/100 + b3*(T_K/100)**2)) * ab
    elif gas == 'N2':
        A0, A1, A2, A3, B0, B1, B2 = hec(gas).values() #PSS salinity
        # T_s, temperature expression used in the calculation of C*
        T_s = np.log((298.15 - T)/T_K)
        # C*, concentration calculated from Hamme and Emerson 2004. Multiplication by 10^-6 to have units of mol/kg
        Cstar = np.exp(A0 + A1*T_s + A2*T_s**2 + A3*T_s**3 + S*(B0 + B1*T_s + B2*T_s**2)) * 1e-6
    return Cstar


# TODO is Iterable[Quantity] here the best way, or should it specify that they have to be numpy arrays?
# TODO is instead a dict output the best choice for the multi-gas option? All other multi-gas functionalities in this program just spit out arrays... i.e., prioritise clarity or consistency? 
@_possibly_iterable
@wraptpint((None, 'degC', 'permille', 'atm', None, None, None), strict=False)
def calc_Ceq(gas:str|Iterable[str], T:float|Quantity, S:float|Quantity, p:float|Quantity, ab='default', units='mol_gas/kg_water', magnitude=False) -> float|Iterable[float]|Quantity|Iterable[Quantity]:
    """Calculate the waterside equilibrium concentration Ceq of a given gas at water
    temperature T, salinity S and airside pressure p.\\
    **Default input units** --- `T`:°C, `S`:‰, `p`:atm\\
    **Default output units** --- mol_gas/kg_water

    :param gas: Gas(es) for which Ceq should be calculated
    :type gas: str | Iterable[str]
    :param T: Temperature
    :type T: float | Quantity
    :param S: Salinity
    :type S: float | Quantity
    :param p: Pressure
    :type p: float | Quantity
    :raises ValueError: If the units given in units are unimplemented
    :return: Waterside equilibrium concentration Ceq of the given gas
    :rtype: float | Iterable[float] | Quantity | Iterable[Quantity]
    """
    # vapour pressure over the water, calculated according to Dyck and Peschke 1995 (atm)
    e_w = calc_vappres(T, magnitude=True) / 1013.25
    # calculation of C*, the gas solubility/water-side concentration expressed in units of mol/kg
    Cstar = calc_Cstar(gas, T, S, ab)
    # factor to account for pressure
    pref = (p - e_w) / (1 - e_w)

    ret = pref * Cstar
    """
    Cache-and-compare system, written by Kai Riedmiller (Heidelberg Scientific Software Centre 
    (https://www.ssc.uni-heidelberg.de/en/what-the-scientific-software-center-is-all-about/meet-our-team))
    Steps:
    1)  check if units has been used before (check for its hash in the keys of CEQUNIT_CACHE)
    2a) if it has, take the values from the cache for compat_unit, unconverted_unit and
        unit_change, which are the desired unit of the user, the "base" unconverted unit stored
        in PAGOS and whether the two are different.
    2b) otherwise, set these three values and store them under a new entry in the cache
    3)  calculate the Ceq-value in the requisite "base" unconverted unit
    4)  convert to the desired unit if necessary
    The reason for this caching system is to avoid calls of pint.Unit.is_compatible_with. Before
    this system was implemented, we called is_compatible_with every time the function was run. In
    fitting procedures, this meant that almost 1/3 of the entire execution time was spent inside
    is_compatible_with.
    """
    global CEQUNIT_CACHE
    id = hash(units)
    if cache_hit := CEQUNIT_CACHE.get(id): # if the hashed units is in our cache...
        compat_unit, unconverted_unit, unit_change = cache_hit # access the relevant values in the cache
    else:
        if not isinstance(units, Unit):  # create pint.Unit object from unit string argument
            units = _u.Unit(units)

        dmly = units.dimensionality
        if dmly == ugw_mol_kg.dimensionality:         # amount gas / mass water
            compat_unit = UEnum.GW_MOL_KG
            unconverted_unit = ugw_mol_kg
        elif dmly == ugw_mol_m3.dimensionality:       # amount gas / volume water
            compat_unit = UEnum.GW_MOL_M3
            unconverted_unit = ugw_mol_m3
        elif dmly == ugw_mol_mol.dimensionality:      # amount gas / amount water
            compat_unit = UEnum.GW_MOL_MOL
            unconverted_unit = ugw_mol_mol
        elif dmly == ugw_ccSTP_g.dimensionality:      # STP volume gas / mass water
            compat_unit = UEnum.GW_CCSTP_G
            unconverted_unit = ugw_ccSTP_g
        elif dmly == ugw_ccSTP_m3.dimensionality:     # STP volume gas / volume water
            compat_unit = UEnum.GW_CCSTP_M3
            unconverted_unit = ugw_ccSTP_m3
        elif dmly == ugw_ccSTP_mol.dimensionality:    # STP volume gas / amount water
            compat_unit = UEnum.GW_CCSTP_MOL
            unconverted_unit = ugw_ccSTP_mol
        elif dmly == ugw_g_mol.dimensionality:        # mass gas / amount water
            compat_unit = UEnum.GW_G_MOL
            unconverted_unit = ugw_g_mol
        elif dmly == ugw_g_m3.dimensionality:         # mass gas / volume water
            compat_unit = UEnum.GW_G_M3
            unconverted_unit = ugw_g_m3
        elif dmly == ugw_g_g.dimensionality:          # mass gas / mass water
            compat_unit = UEnum.GW_G_G
            unconverted_unit = ugw_g_g
        else:
            raise ValueError(f"Invalid/unimplemented value for unit ({units}). Try something like \"mol_g/kg_w\", \"ccSTP_g/g_w\" or \"mol_g/m3_w\".")
        
        unit_change = unconverted_unit != units
        CEQUNIT_CACHE[id] = (compat_unit, unconverted_unit, unit_change) # add the units to the cache if they're not already there
    
    # return equilibrium concentration with desired units
    if compat_unit == UEnum.GW_MOL_KG:
        ret = pref * Cstar
    elif compat_unit == UEnum.GW_MOL_M3:
        rho = calc_dens(T, S, magnitude=True)
        ret = pref * rho * Cstar
    elif compat_unit == UEnum.GW_MOL_MOL:
        ret = pref * Cstar * MMW * 1e-3  # *1e-3: mol/kmol -> mol/mol
    elif compat_unit == UEnum.GW_CCSTP_G:
        mvol = mv(gas)
        ret = pref * mvol * Cstar * 1e-3  # *1e-3: cc/kg -> cc/g
    elif compat_unit == UEnum.GW_CCSTP_MOL:
        mvol = mv(gas)
        ret = pref * mvol * MMW * Cstar * 1e-3  # *1e-3: cc/kmol -> cc/mol
    elif compat_unit == UEnum.GW_CCSTP_M3:
        rho = calc_dens(T, S, magnitude=True)
        mvol = mv(gas)
        ret = pref * mvol * rho * Cstar
    elif compat_unit == UEnum.GW_G_MOL:
        mmass = mm(gas)
        ret = pref * mmass * MMW * Cstar * 1e-3  # *1e-3: g/kmol -> g/mol
    elif compat_unit == UEnum.GW_G_M3:
        rho = calc_dens(T, S, magnitude=True)
        mmass = mm(gas)
        ret = pref * mmass * rho * Cstar
    elif compat_unit == UEnum.GW_G_G:
        mmass = mm(gas)
        ret = pref * mmass * Cstar * 1e-3  # *1e-3: g/kg -> g/g
    else:
        raise ValueError(f"Invalid/unimplemented value for unit ({units}). Try something like \"mol_g/kg_w\", \"ccSTP_g/g_w\" or \"mol_g/m3_w\".")
    
    # return, after conversion if necessary - written like this to avoid _sto() for speed reasons
    if magnitude and not unit_change:
        return ret
    elif magnitude:
        print('bzzt')
        return _sto(ret * unconverted_unit, units).magnitude
    elif not unit_change:
        return ret * unconverted_unit
    else:
        return _sto(ret * unconverted_unit, units)


@_possibly_iterable
@wraptpint((None, 'degC', 'permille', 'atm', None, None, None), strict=False)
def calc_dCeq_dT(gas:str, T:float|Quantity, S:float|Quantity, p:float|Quantity, ab='default', units='mol_gas/kg_water/K', magnitude=False) -> float|Iterable[float]|Quantity|Iterable[Quantity]:
    """Calculate the temperature-derivative dCeq_dT of the waterside equilibrium
    concentration of a given gas at water temperature T, salinity S and airside pressure p.\\
    **Default input units** --- `T`:°C, `S`:‰, `p`:atm\\
    **Output units** --- None

    :param gas: Gas(es) for which dCeq_dT should be calculated
    :type gas: str
    :param T: Temperature
    :type T: float | Quantity
    :param S: Salinity
    :type S: float | Quantity
    :param p: Pressure
    :type p: float | Quantity
    :param units: Units in which dCeq_dT should be expressed
    :type units: str | Unit, optional
    :param ret_quant: Whether to return the result as a Pint Quantity instead of just a float, defaults to False
    :type ret_quant: bool, optional
    :raises ValueError: If the units given in units are unimplemented
    :return: Waterside equilibrium concentration temperature derivative dCeq_dT of the given gas
    :rtype: float|Iterable[float]|Quantity|Iterable[Quantity]
    """
    # vapour pressure over the water, calculated according to Dyck and Peschke 1995 (atm)
    e_w = calc_vappres(T, magnitude=True) / 1013.25
    # calculation of C*, the gas solubility/water-side concentration (mol/kg)
    Cstar = calc_Cstar(gas, T, S, ab)
    # factor to account for pressure
    pref = (p - e_w) / (1 - e_w)
    # return equilibrium concentration with desired units
    # calculation of dC*/dT at the given T, S, p
    T_K = T + TPW
    if hasgasprop(gas, 'isnoble'):
        A1, A2, A3, A4, B1, B2, B3, C1 = jkc(gas).values() #needs S in PSS78
        dCstar_dT = (S*(B3*T_K/5000 + B2/100) + A3/T_K - 100*A2/(T_K**2) + A4/100)*Cstar
    elif gas in ['CFC11', 'CFC12']:
        a1, a2, a3, a4, b1, b2, b3 = wwc(gas).values() #needs S in parts per thousand
        #TODO adopt for absolute salinity??
        dCstar_dT = (S*(b3*T_K/5000 + b2/100) + a3/T_K - 100*a2/T_K**2 + a4*T_K/5000)*Cstar
    elif gas == 'SF6':
        a1, a2, a3, b1, b2, b3 = blc(gas).values() #don't know salinity unit
        dCstar_dT = (S*(b3*T_K/5000 + b2/100) + a3/T_K - 100*a2/T_K**2)*Cstar
    elif gas == 'N2':
        A0, A1, A2, A3, B0, B1, B2 = hec(gas).values() #PSS salinity
        # T_s, temperature expression used in the calculation of C*
        T_s = np.log((298.15 - T)/T_K)
        dCstar_dT = Cstar * 25/((T_K-25)*T_K) * (A1 + S*B1 + 2*(A2 + S*B2)*T_s + 3*A3*T_s**2) * 1e-6

    de_w_dT = calc_vappres_Tderiv(T, magnitude=True) / 1013.25 # mbar/K -> atm/K
    dCeq_dT_molkgK = pref * dCstar_dT + (p - 1)/((e_w - 1)**2) * de_w_dT * Cstar

    """
    Cache-and-compare system, written by Kai Riedmiller (Heidelberg Scientific Software Centre 
    (https://www.ssc.uni-heidelberg.de/en/what-the-scientific-software-center-is-all-about/meet-our-team))
    See calc_Ceq for a description of how this works.
    """
    global DT_CEQUNIT_CACHE
    id = hash(units)
    if cache_hit := DT_CEQUNIT_CACHE.get(id): # if the hashed units is in our cache...
        compat_unit, unconverted_unit, unit_change = cache_hit # access the relevant values in the cache
    else:
        if not isinstance(units, Unit):  # create pint.Unit object from unit string argument
            units = _u.Unit(units)
        
        dmly = units.dimensionality
        if dmly == ugw_mol_kg_K.dimensionality:         # amount gas / mass water / temperature
            compat_unit = UEnum.GW_MOL_KG_K
            unconverted_unit = ugw_mol_kg_K
        elif dmly == ugw_mol_m3_K.dimensionality:       # amount gas / volume water / temperature
            compat_unit = UEnum.GW_MOL_M3_K
            unconverted_unit = ugw_mol_m3_K
        elif dmly == ugw_mol_mol_K.dimensionality:      # amount gas / amount water / temperature
            compat_unit = UEnum.GW_MOL_MOL_K
            unconverted_unit = ugw_mol_mol_K
        elif dmly == ugw_ccSTP_g_K.dimensionality:      # STP volume gas / mass water / temperature
            compat_unit = UEnum.GW_CCSTP_G_K
            unconverted_unit = ugw_ccSTP_g_K
        elif dmly == ugw_ccSTP_mol_K.dimensionality:    # STP volume gas / amount water / temperature
            compat_unit = UEnum.GW_CCSTP_MOL_K
            unconverted_unit = ugw_ccSTP_mol_K
        elif dmly == ugw_ccSTP_m3_K.dimensionality:     # STP volume gas / volume water / temperature
            compat_unit = UEnum.GW_CCSTP_M3_K
            unconverted_unit = ugw_ccSTP_m3_K
        elif dmly == ugw_g_mol_K.dimensionality:        # mass gas / amount water / temperature
            compat_unit = UEnum.GW_G_MOL_K
            unconverted_unit = ugw_g_mol_K
        elif dmly == ugw_g_m3_K.dimensionality:         # mass gas / volume water / temperature
            compat_unit = UEnum.GW_G_M3_K
            unconverted_unit = ugw_g_m3_K
        elif dmly == ugw_g_g_K.dimensionality:          # mass gas / mass water / temperature
            compat_unit = UEnum.GW_G_G_K
            unconverted_unit = ugw_g_g_K
        else:
            raise ValueError(f"Invalid/unimplemented value for unit ({units}). Try something like \"mol_g/kg_w/K\", \"ccSTP_g/g_w/K\" or \"mol_g/m3_w/K\".")
        
        unit_change = unconverted_unit != units
        DT_CEQUNIT_CACHE[id] = (compat_unit, unconverted_unit, unit_change) # add the units to the cache if it's not already there
    
    # return dCeq/dT with desired units
    if compat_unit == UEnum.GW_MOL_KG_K:
        ret = dCeq_dT_molkgK
    elif compat_unit == UEnum.GW_MOL_M3_K:
        rho = calc_dens(T, S, magnitude=True)
        drho_dT = calc_dens_Tderiv(T, S, magnitude=True)
        ret = dCeq_dT_molkgK * rho + pref * Cstar * drho_dT
    elif compat_unit == UEnum.GW_MOL_MOL_K:
        ret = dCeq_dT_molkgK * MMW * 1e-3  # *1e-3: mol/kmol/K -> mol/mol/K
    elif compat_unit == UEnum.GW_CCSTP_G_K:
        mvol = mv(gas)
        ret = dCeq_dT_molkgK * mvol * 1e-3  # *1e-3: cc/kg/K -> cc/g/K
    elif compat_unit == UEnum.GW_CCSTP_MOL_K:
        mvol = mv(gas)
        ret = dCeq_dT_molkgK * MMW * mvol * 1e-3  # *1e-3: cc/kmol/K -> cc/mol/K
    elif compat_unit == UEnum.GW_CCSTP_M3_K:
        rho = calc_dens(T, S, magnitude=True)
        mvol = mv(gas)
        ret = (dCeq_dT_molkgK * mvol * rho + pref * Cstar * mvol * drho_dT)
    elif compat_unit == UEnum.GW_G_MOL_K:
        mmass = mm(gas)
        ret = dCeq_dT_molkgK * mmass * MMW * 1e-3  # *1e-3: g/kmol/K -> g/mol/K
    elif compat_unit == UEnum.GW_G_M3_K:
        rho = calc_dens(T, S, magnitude=True)
        drho_dT = calc_dens_Tderiv(T, S, magnitude=True)
        mmass = mm(gas)
        ret = dCeq_dT_molkgK * mmass * rho + pref * mmass * drho_dT * Cstar
    elif compat_unit == UEnum.GW_G_G_K:
        mmass = mm(gas)
        ret = dCeq_dT_molkgK * mmass * 1e-3  # *1e-3: g/kg/K -> g/g/K
    else:
        raise ValueError(f"Invalid/unimplemented value for unit ({units}). Try something like \"mol_g/kg_w/K\", \"ccSTP_g/g_w/K\" or \"mol_g/m3_w/K\".")
    
    # return, after conversion if necessary - written like this to avoid _sto() for speed reasons
    if magnitude and not unit_change:
        return ret
    elif magnitude:
        return _sto(ret * unconverted_unit, units).magnitude
    elif not unit_change:
        return ret * unconverted_unit
    else:
        return _sto(ret * unconverted_unit, units)


@_possibly_iterable
@wraptpint((None, 'degC', 'permille', 'atm', None, None, None), strict=False)
def calc_dCeq_dS(gas:str, T:float|Quantity, S:float|Quantity, p:float|Quantity, ab='default', units='mol_g/kg_water/permille', magnitude=False) -> float|Iterable[float]|Quantity|Iterable[Quantity]:
    """Calculate the salinity-derivative dCeq_dS of the waterside equilibrium
    concentration of a given gas at water temperature T, salinity S and airside pressure p.\\
    **Default input units** --- `T`:°C, `S`:‰, `p`:atm\\
    **Output units** --- None

    :param gas: Gas(es) for which dCeq_dS should be calculated
    :type gas: str
    :param T: Temperature
    :type T: float | Quantity
    :param S: Salinity
    :type S: float | Quantity
    :param p: Pressure
    :type p: float | Quantity
    :param units: Units in which dCeq_dS should be expressed
    :type units: str | Unit, optional
    :param ret_quant: Whether to return the result as a Pint Quantity instead of just a float, defaults to False
    :type ret_quant: bool, optional
    :raises ValueError: If the units given in units are unimplemented
    :return: Waterside equilibrium concentration salinity derivative dCeq_dS of the given gas
    :rtype: float|Iterable[float]|Quantity|Iterable[Quantity]
    """
    # vapour pressure over the water, calculated according to Dyck and Peschke 1995 (atm)
    e_w = calc_vappres(T, magnitude=True) / 1013.25
    # calculation of C*, the gas solubility/water-side concentration (mol/kg)
    Cstar = calc_Cstar(gas, T, S, ab)
    # factor to account for pressure
    pref = (p - e_w) / (1 - e_w)
    # return equilibrium concentration with desired units
    # calculation of dC*/dS at the given T, S, p
    T_K = T + TPW
    if hasgasprop(gas, 'isnoble'):
        A1, A2, A3, A4, B1, B2, B3, C1 = jkc(gas).values() #needs S in PSS78
        dCstar_dS = (B1 + B2*(T_K/100) + B3*(T_K/100)**2 + 2*C1*S) * Cstar
    elif gas in ['CFC11', 'CFC12']:
        a1, a2, a3, a4, b1, b2, b3 = wwc(gas).values() #needs S in parts per thousand
        #TODO adopt for absolute salinity??
        dCstar_dS = (b1 + b2*(T_K/100) + b3*(T_K/100)**2) * Cstar
    elif gas == 'SF6':
        a1, a2, a3, b1, b2, b3 = blc(gas).values() #don't know salinity unit
        dCstar_dS = (b1 + b2*(T_K/100) + b3*(T_K/100)**2) * Cstar
    elif gas == 'N2':
        A0, A1, A2, A3, B0, B1, B2 = hec(gas).values() #PSS salinity
        # T_s, temperature expression used in the calculation of C*
        T_s = np.log((298.15 - T)/T_K)
        dCstar_dS = (B0 + B1*T_s + B2*T_s**2) * Cstar

    dCeq_dS_molkgpm = pref * dCstar_dS
    
    """
    Cache-and-compare system, written by Kai Riedmiller (Heidelberg Scientific Software Centre 
    (https://www.ssc.uni-heidelberg.de/en/what-the-scientific-software-center-is-all-about/meet-our-team))
    See calc_Ceq for a description of how this works.
    """
    global DS_CEQUNIT_CACHE
    id = hash(units)
    if cache_hit := DS_CEQUNIT_CACHE.get(id): # if the hashed units is in our cache...
        compat_unit, unconverted_unit, unit_change = cache_hit # access the relevant values in the cache
    else:
        if not isinstance(units, Unit):  # create pint.Unit object from unit string argument
            units = _u.Unit(units)
        
        dmly = units.dimensionality
        if dmly == ugw_mol_kg_pml.dimensionality:         # amount gas / mass water / salinity
            compat_unit = UEnum.GW_MOL_KG_PML
            unconverted_unit = ugw_mol_kg_pml
        elif dmly == ugw_mol_m3_pml.dimensionality:       # amount gas / volume water / salinity
            compat_unit = UEnum.GW_MOL_M3_PML
            unconverted_unit = ugw_mol_m3_pml
        elif dmly == ugw_mol_mol_pml.dimensionality:      # amount gas / amount water / salinity
            compat_unit = UEnum.GW_MOL_MOL_PML
            unconverted_unit = ugw_mol_mol_pml
        elif dmly == ugw_ccSTP_g_pml.dimensionality:      # STP volume gas / mass water / salinity
            compat_unit = UEnum.GW_CCSTP_G_PML
            unconverted_unit = ugw_ccSTP_g_pml
        elif dmly == ugw_ccSTP_mol_pml.dimensionality:    # STP volume gas / amount water / salinity
            compat_unit = UEnum.GW_CCSTP_MOL_PML
            unconverted_unit = ugw_ccSTP_mol_pml
        elif dmly == ugw_ccSTP_m3_pml.dimensionality:     # STP volume gas / volume water / salinity
            compat_unit = UEnum.GW_CCSTP_M3_PML
            unconverted_unit = ugw_ccSTP_m3_pml
        elif dmly == ugw_g_mol_pml.dimensionality:        # mass gas / amount water / salinity
            compat_unit = UEnum.GW_G_MOL_PML
            unconverted_unit = ugw_g_mol_pml
        elif dmly == ugw_g_m3_pml.dimensionality:         # mass gas / volume water / salinity
            compat_unit = UEnum.GW_G_M3_PML
            unconverted_unit = ugw_g_m3_pml
        elif dmly == ugw_g_g_pml.dimensionality:          # mass gas / mass water / salinity
            compat_unit = UEnum.GW_G_G_PML
            unconverted_unit = ugw_g_g_pml
        else:
            raise ValueError(f"Invalid/unimplemented value for unit ({units}). Try something like \"mol_g/kg_w/permille\", \"ccSTP_g/g_w/permille\" or \"mol_g/m3_w/permille\".")
        
        unit_change = unconverted_unit != units
        DS_CEQUNIT_CACHE[id] = (compat_unit, unconverted_unit, unit_change) # add the units to the cache if it's not already there
    
    # return dCeq/dS with desired units
    if compat_unit == UEnum.GW_MOL_KG_PML:
        ret = dCeq_dS_molkgpm
    elif compat_unit == UEnum.GW_MOL_M3_PML:
        rho = calc_dens(T, S, magnitude=True)
        drho_dS = calc_dens_Sderiv(T, S, magnitude=True)
        ret = dCeq_dS_molkgpm * rho + pref * Cstar * drho_dS
    elif compat_unit == UEnum.GW_MOL_MOL_PML:
        ret = dCeq_dS_molkgpm * MMW * 1e-3  # *1e-3: mol/kmol/permille -> mol/mol/permille
    elif compat_unit == UEnum.GW_CCSTP_G_PML:
        mvol = mv(gas)
        ret = dCeq_dS_molkgpm * mvol * 1e-3  # *1e-3: cc/kg/permille -> cc/g/permille
    elif compat_unit == UEnum.GW_CCSTP_M3_PML:
        rho = calc_dens(T, S, magnitude=True)
        drho_dS = calc_dens_Sderiv(T, S, magnitude=True)
        mvol = mv(gas)
        ret = (dCeq_dS_molkgpm * mvol * rho + pref * Cstar * mvol * drho_dS)
    elif compat_unit == UEnum.GW_CCSTP_MOL_PML:
        mvol = mv(gas)
        ret = dCeq_dS_molkgpm * MMW * mvol * 1e-3  # *1e-3: cc/kmol/permille -> cc/mol/permille
    elif compat_unit == UEnum.GW_G_MOL_PML:
        mmass = mm(gas)
        ret = dCeq_dS_molkgpm * mmass * MMW * 1e-3  # *1e-3: g/kmol/permille -> g/mol/permille
    elif compat_unit == UEnum.GW_G_M3_PML:
        rho = calc_dens(T, S, magnitude=True)
        drho_dS = calc_dens_Sderiv(T, S, magnitude=True)
        mmass = mm(gas)
        ret = dCeq_dS_molkgpm * mmass * rho + pref * mmass * drho_dS * Cstar
    elif compat_unit == UEnum.GW_G_G_PML:
        mmass = mm(gas)
        ret = dCeq_dS_molkgpm * mmass * 1e-3  # *1e-3: g/kg/permille -> g/g/permille
    else:
        raise ValueError(f"Invalid/unimplemented value for unit ({units}). Try something like \"mol_g/kg_w/permille\", \"ccSTP_g/g_w/permille\" or \"mol_g/m3_w/permille\".")

    # return, after conversion if necessary - written like this to avoid _sto() for speed reasons
    if magnitude and not unit_change:
        return ret
    elif magnitude:
        return _sto(ret * unconverted_unit, units).magnitude
    elif not unit_change:
        return ret * unconverted_unit
    else:
        return _sto(ret * unconverted_unit, units)


@_possibly_iterable
@wraptpint((None, 'degC', 'permille', 'atm', None, None, None), strict=False)
def calc_dCeq_dp(gas:str, T:float|Quantity, S:float|Quantity, p:float|Quantity, ab='default', units='mol_gas/kg_water/atm', magnitude=False) -> float|Iterable[float]|Quantity|Iterable[Quantity]:
    """Calculate the pressure-derivative dCeq_dp of the waterside equilibrium
    concentration of a given gas at water temperature T, salinity S and airside pressure p.\\
    **Default input units** --- `T`:°C, `S`:‰, `p`:atm\\
    **Output units** --- None

    :param gas: Gas(es) for which dCeq_dp should be calculated
    :type gas: str
    :param T: Temperature
    :type T: float | Quantity
    :param S: Salinity
    :type S: float | Quantity
    :param p: Pressure
    :type p: float | Quantity
    :param dCeq_dp_unit: Units in which dCeq_dp should be expressed
    :type dCeq_dp_unit: str | Unit, optional
    :param ret_quant: Whether to return the result as a Pint Quantity instead of just a float, defaults to False
    :type ret_quant: bool, optional
    :raises ValueError: If the units given in dCeq_dp_unit are unimplemented
    :return: Waterside equilibrium concentration pressure derivative dCeq_dp of the given gas
    :rtype: float | Iterable[float] | Quantity | Iterable[Quantity]
    """
    # molar volume and molar mass
    mvol = mv(gas)
    mmass = mm(gas)
    # vapour pressure over the water, calculated according to Dyck and Peschke 1995 (atm)
    e_w = calc_vappres(T, magnitude=True) / 1013.25
    # density of the water (kg/m3)
    rho = calc_dens(T, S, magnitude=True)
    # calculation of C*, the gas solubility/water-side concentration (mol/kg)
    Cstar = calc_Cstar(gas, T, S, ab)
    # factor to account for pressure (this is the pressure-derivative of (p - e_w) / (1 - e_w))
    pref = 1 / (1 - e_w)
    # return equilibrium concentration with desired units

    """
    Cache-and-compare system, written by Kai Riedmiller (Heidelberg Scientific Software Centre 
    (https://www.ssc.uni-heidelberg.de/en/what-the-scientific-software-center-is-all-about/meet-our-team))
    See calc_Ceq for a description of how this works.
    """
    global DP_CEQUNIT_CACHE
    id = hash(units)
    if cache_hit := DP_CEQUNIT_CACHE.get(id): # if the hashed dCeq_dp_unit is in our cache...
        compat_unit, unconverted_unit, unit_change = cache_hit # access the relevant values in the cache
    else:
        if not isinstance(units, Unit):  # create pint.Unit object from unit string argument
            units = _u.Unit(units)
        
        dmly = units.dimensionality
        if dmly == ugw_mol_kg_atm.dimensionality:         # amount gas / mass water / pressure
            compat_unit = UEnum.GW_MOL_KG_ATM
            unconverted_unit = ugw_mol_kg_atm
        elif dmly == ugw_mol_m3_atm.dimensionality:       # amount gas / volume water / pressure
            compat_unit = UEnum.GW_MOL_M3_ATM
            unconverted_unit = ugw_mol_m3_atm
        elif dmly == ugw_mol_mol_atm.dimensionality:      # amount gas / amount water / pressure
            compat_unit = UEnum.GW_MOL_MOL_ATM
            unconverted_unit = ugw_mol_mol_atm
        elif dmly == ugw_ccSTP_g_atm.dimensionality:      # STP volume gas / mass water / pressure
            compat_unit = UEnum.GW_CCSTP_G_ATM
            unconverted_unit = ugw_ccSTP_g_atm
        elif dmly == ugw_ccSTP_mol_atm.dimensionality:    # STP volume gas / amount water / pressure
            compat_unit = UEnum.GW_CCSTP_MOL_ATM
            unconverted_unit = ugw_ccSTP_mol_atm
        elif dmly == ugw_ccSTP_m3_atm.dimensionality:     # STP volume gas / volume water / pressure
            compat_unit = UEnum.GW_CCSTP_M3_ATM
            unconverted_unit = ugw_ccSTP_m3_atm
        elif dmly == ugw_g_mol_atm.dimensionality:        # mass gas / amount water / pressure
            compat_unit = UEnum.GW_G_MOL_ATM
            unconverted_unit = ugw_g_mol_atm
        elif dmly == ugw_g_m3_atm.dimensionality:         # mass gas / volume water / pressure
            compat_unit = UEnum.GW_G_M3_ATM
            unconverted_unit = ugw_g_m3_atm
        elif dmly == ugw_g_g_atm.dimensionality:          # mass gas / mass water / pressure
            compat_unit = UEnum.GW_G_G_ATM
            unconverted_unit = ugw_g_g_atm
        else:
            raise ValueError(f"Invalid/unimplemented value for unit ({units}). Try something like \"mol_g/kg_w/atm\", \"ccSTP_g/g_w/atm\" or \"mol_g/m3_w/atm\".")
        
        unit_change = unconverted_unit != units
        DP_CEQUNIT_CACHE[id] = (compat_unit, unconverted_unit, unit_change) # add the units to the cache if it's not already there
    
    # return dCeq/dp with desired units
    if compat_unit == UEnum.GW_MOL_KG_ATM:
        ret = pref * Cstar
    elif compat_unit == UEnum.GW_MOL_M3_ATM:
        rho = calc_dens(T, S, magnitude=True)
        ret = pref * Cstar * rho
    elif compat_unit == UEnum.GW_MOL_MOL_ATM:
        ret = pref * Cstar * MMW * 1e-3  # *1e-3: mol/kmol/atm -> mol/mol/atm
    elif compat_unit == UEnum.GW_CCSTP_G_ATM:
        mvol = mv(gas)
        ret = pref * Cstar * mvol * 1e-3  # *1e-3: cc/kg/atm -> cc/g/atm
    elif compat_unit == UEnum.GW_CCSTP_MOL_ATM:
        mvol = mv(gas)
        ret = pref * Cstar * MMW * mvol * 1e-3  # *1e-3: cc/kmol/atm -> cc/mol/atm
    elif compat_unit == UEnum.GW_CCSTP_M3_ATM:
        rho = calc_dens(T, S, magnitude=True)
        mvol = mv(gas)
        ret = pref * Cstar * mvol * rho
    elif compat_unit == UEnum.GW_G_MOL_ATM:
        mmass = mm(gas)
        ret = pref * Cstar * mmass * MMW * 1e-3  # *1e-3: g/kmol/atm -> g/mol/atm
    elif compat_unit == UEnum.GW_G_M3_ATM:
        rho = calc_dens(T, S, magnitude=True)
        mmass = mm(gas)
        ret = pref * Cstar * mmass * rho
    elif compat_unit == UEnum.GW_G_G_ATM:
        mmass = mm(gas)
        ret = pref * Cstar * mmass * 1e-3  # *1e-3: g/kg/permille -> g/g/permille
    else:
        raise ValueError(f"Invalid/unimplemented value for unit ({units}). Try something like \"mol_g/kg_w/atm\", \"ccSTP_g/g_w/atm\" or \"mol_g/m3_w/atm\".")

    # return, after conversion if necessary - written like this to avoid _sto() for speed reasons
    if magnitude and not unit_change:
        return ret
    elif magnitude:
        return _sto(ret * unconverted_unit, units).magnitude
    elif not unit_change:
        return ret * unconverted_unit
    else:
        return _sto(ret * unconverted_unit, units)


@_possibly_iterable
@wraptpint((None, 'degC', 'permille', 'atm', None, None, None), strict=False)
def calc_henry(gas:str, T:float|Quantity, S:float|Quantity, p:float|Quantity, ab='default', units='dimensionless', magnitude=False) -> float|Iterable[float]|Quantity|Iterable[Quantity]:
    """Calculate the Henry solubility coefficient of a gas in water at water temperature T, salinity S and airside pressure p.\\
    **Default input units** --- `T`:°C, `S`:‰, `p`:atm\\
    **Output units** --- dimensionless\\
    The type of solubility coefficient (`solcoeff_type`) can be:
    * dimensionless (`'dimensionless'`, `''`)
    * amount gas / volume water / partial pressure (`'mol/L/Pa'`)
    * STP volume gas / volume water / partial pressure (`'Pa^-1'`)
    * amount gas / amount water / partial pressure (`Pa^-1`)

    :param gas: Gas(es) for which the solubility coefficient should be calculated.
    :type gas: str
    :param T: Temperature
    :type T: float | Quantity
    :param S: Salinity
    :type S: float | Quantity
    :param p: Pressure
    :type p: float | Quantity
    :param solcoeff_type: Units of solubility coefficient, defaults to 'dimensionless'
    :type solcoeff_type: str, optional
    :raises ValueError: If the type of solubility coefficient is unimplemented
    :return: Solubility coefficient of the given gas
    :rtype: float | Iterable[float] | Quantity | Iterable[Quantity]
    """
    # gas abundance
    if ab == 'default':
        ab = abn(gas)
    else:
        ab = ab
    # vapour pressure in air
    e_w = calc_vappres(T, magnitude=True)
    # temperature degrees to K
    T_K = T + TPW
    # gas-side concentration
    C_g = 100 * ab * (p*1013.25 - e_w) / MGC / T_K # x100 to convert from hPa mol / J to mol / m^3
    # water-side concentration
    C_w = calc_Ceq(gas, T, S, p, ab=ab, magnitude=True, units='mol_gas/m3_water')
    # calculate Henry coefficient H [L_water / L_air]
    H = C_g / C_w

    global HENUNIT_CACHE
    id = hash(units)
    if cache_hit := HENUNIT_CACHE.get(id): # if the hashed unit is in our cache...
        compat_unit, unconverted_unit, unit_change = cache_hit # access the relevant values in the cache
    else:
        if not isinstance(units, Unit):  # create pint.Unit object from unit string argument
            units = _u.Unit(units)
        
        dmly = units.dimensionality
        if dmly == u_dimless.dimensionality: 
            compat_unit = UEnum.DIMLESS
            unconverted_unit = u_dimless
        else:
            raise ValueError(f"Invalid/unimplemented value for unit ({units}). Currently, only dimensionless units are supported for Henry coefficients")
        
        unit_change = unconverted_unit != units
        HENUNIT_CACHE[id] = (compat_unit, unconverted_unit, unit_change) # add the unit to the cache if it's not already there

    # return H with desired units
    if compat_unit == UEnum.DIMLESS:
        ret = H
    else:
        raise ValueError(f"Invalid/unimplemented value for unit ({units}). Currently, only dimensionless units are supported for Henry coefficients")
    
    # return, after conversion if necessary - written like this to avoid _sto() for speed reasons
    if magnitude and not unit_change:
        return ret
    elif magnitude:
        return _sto(ret * unconverted_unit, units).magnitude
    elif not unit_change:
        return ret * unconverted_unit
    else:
        return _sto(ret * unconverted_unit, units)