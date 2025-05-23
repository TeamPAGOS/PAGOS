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
@wraptpint('dimensionless', (None, 'degC', 'permille', None), False)
def calc_Sc(gas:str|Iterable[str], T:float|Quantity, S:float|Quantity, method:str='auto') -> Quantity|Iterable[Quantity]:
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
    return Sc


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


# cache to hold Ceq_units if they have previously been used so that Unit.is_compatible_with() is
# called as infrequently as possible (it gets expensive when running fitting routines)
CEQUNIT_CACHE = dict()
# TODO is Iterable[Quantity] here the best way, or should it specify that they have to be numpy arrays?
# TODO is instead a dict output the best choice for the multi-gas option? All other multi-gas functionalities in this program just spit out arrays... i.e., prioritise clarity or consistency? 
@_possibly_iterable
@wraptpint(None, (None, 'degC', 'permille', 'atm', None, None, None), strict=False)
def calc_Ceq(gas:str|Iterable[str], T:float|Quantity, S:float|Quantity, p:float|Quantity, Ceq_unit:str|Unit='cc/g', ret_quant:bool=False, ab='default') -> float|Iterable[float]|Quantity|Iterable[Quantity]:
    """Calculate the waterside equilibrium concentration Ceq of a given gas at water
    temperature T, salinity S and airside pressure p.\\
    **Default input units** --- `T`:°C, `S`:‰, `p`:atm\\
    **Output units** --- None

    :param gas: Gas(es) for which Ceq should be calculated
    :type gas: str | Iterable[str]
    :param T: Temperature
    :type T: float | Quantity
    :param S: Salinity
    :type S: float | Quantity
    :param p: Pressure
    :type p: float | Quantity
    :param Ceq_unit: Units in which Ceq should be expressed
    :type Ceq_unit: str | Unit
    :param ret_quant: Whether to return the result as a Pint Quantity instead of just a float, defaults to False
    :type ret_quant: bool, optional
    :raises ValueError: If the units given in Ceq_unit are unimplemented
    :return: Waterside equilibrium concentration Ceq of the given gas
    :rtype: float | Iterable[float] | Quantity | Iterable[Quantity]
    """
    # molar volume and molar mass
    mvol = mv(gas)
    mmass = mm(gas)
    # vapour pressure over the water, calculated according to Dyck and Peschke 1995 (atm)
    e_w = calc_vappres(T, magnitude=True) / 1013.25
    # density of the water (kg/m3)
    rho = calc_dens(T, S, magnitude=True)

    # calculation of C*, the gas solubility/water-side concentration expressed in units of mol/kg
    Cstar = calc_Cstar(gas, T, S, ab)
    # factor to account for pressure
    pref = (p - e_w) / (1 - e_w)

    """
    Cache-and-compare system, written by Kai Riedmiller (Heidelberg Scientific Software Centre 
    (https://www.ssc.uni-heidelberg.de/en/what-the-scientific-software-center-is-all-about/meet-our-team))
    Steps:
    1)  check if Ceq_unit has been used before (check for its hash in the keys of CEQUNIT_CACHE)
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
    id = hash(Ceq_unit)
    if cache_hit := CEQUNIT_CACHE.get(id): # if the hashed Ceq_unit is in our cache...
        compat_unit, unconverted_unit, unit_change = cache_hit # access the relevant values in the cache
    else:
        if not isinstance(Ceq_unit, Unit):  # create pint.Unit object from unit string argument
            Ceq_unit = _u.Unit(Ceq_unit)
        
        if Ceq_unit.is_compatible_with(u_mol_kg):  # amount gas / mass water
            compat_unit = UEnum.MOL_KG
            unconverted_unit = u_mol_kg
        elif Ceq_unit.is_compatible_with(u_mol_cc):  # amount gas / volume water
            compat_unit = UEnum.MOL_CC
            unconverted_unit = u_mol_cc
        elif Ceq_unit.is_compatible_with(u_cc_g):  # volume gas / mass water
            compat_unit = UEnum.CC_G
            unconverted_unit = u_cc_g
        elif Ceq_unit.is_compatible_with(u_kg_mol):  # mass gas / amount water
            compat_unit = UEnum.KG_MOL
            unconverted_unit = u_kg_mol
        elif Ceq_unit.is_compatible_with(u_cc_mol):  # volume gas / amount water
            compat_unit = UEnum.CC_MOL
            unconverted_unit = u_cc_mol
        elif Ceq_unit.is_compatible_with(u_kg_m3):  # mass gas / volume water
            compat_unit = UEnum.KG_M3
            unconverted_unit = u_kg_m3
        else:
            raise ValueError("Invalid/unimplemented value for unit. Try something like \"mol/kg\", \"mol/cc\" or \"cc/g\".")
        
        unit_change = unconverted_unit != Ceq_unit
        CEQUNIT_CACHE[id] = (compat_unit, unconverted_unit, unit_change) # add the Ceq_unit to the cache if it's not already there
    
    # return equilibrium concentration with desired units
    if compat_unit == UEnum.MOL_KG:  # amount gas / mass water
        ret = pref * Cstar
    elif compat_unit == UEnum.MOL_CC:  # amount gas / volume water
        ret = pref * rho * Cstar * 1e-6  # *1e-6: mol/m^3 -> mol/cc
    elif compat_unit == UEnum.CC_G:  # volume gas / mass water
        ret = pref * mvol * Cstar * 1e-3  # *1e-3: cc/kg -> cc/g
    elif compat_unit == UEnum.KG_MOL:  # mass gas / amount water
        ret = pref * mmass * MMW * Cstar * 1e-6  # *1e-6: mg/mol -> kg/mol
    elif compat_unit == UEnum.CC_MOL:  # volume gas / amount water
        ret = pref * mvol * MMW * Cstar * 1e-3  # *1e-3: μL/mol -> cc/mol
    elif compat_unit == UEnum.KG_M3:  # mass gas / volume water
        ret = pref * mmass * rho * Cstar * 1e-3  # 1e-3: g/m^3 -> kg/m^3
    else:
        raise ValueError("Invalid/unimplemented value for unit. Try something like \"mol/kg\", \"mol/cc\" or \"cc/g\".")

    # return, after conversion if necessary - written like this to avoid _sto() for speed reasons
    if not ret_quant and not unit_change:
        return ret
    elif not ret_quant:
        return _sto(ret * unconverted_unit, Ceq_unit).magnitude
    elif not unit_change:
        return ret * unconverted_unit
    else:
        return _sto(ret * unconverted_unit, Ceq_unit)


# cache to hold dCeq_dT_units if they have previously been used so that Unit.is_compatible_with()
# is called as infrequently as possible (it gets expensive when running fitting routines)
DT_CEQUNIT_CACHE = dict()
@_possibly_iterable
@wraptpint(None, (None, 'degC', 'permille', 'atm', None, None, None), strict=False)
def calc_dCeq_dT(gas:str, T:float|Quantity, S:float|Quantity, p:float|Quantity, dCeq_dT_unit:str|Unit='cc/g/K', ret_quant:bool=False, ab='default') -> float|Iterable[float]|Quantity|Iterable[Quantity]:
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
    :param dCeq_dT_unit: Units in which dCeq_dT should be expressed
    :type dCeq_dT_unit: str | Unit, optional
    :param ret_quant: Whether to return the result as a Pint Quantity instead of just a float, defaults to False
    :type ret_quant: bool, optional
    :raises ValueError: If the units given in dCeq_dT_unit are unimplemented
    :return: Waterside equilibrium concentration temperature derivative dCeq_dT of the given gas
    :rtype: float|Iterable[float]|Quantity|Iterable[Quantity]
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

    drho_dT = calc_dens_Tderiv(T, S, magnitude=True)
    de_w_dT = calc_vappres_Tderiv(T, magnitude=True) / 1013.25 # mbar/K -> atm/K
    dCeq_dT_molkgK = pref * dCstar_dT + (p - 1)/((e_w - 1)**2) * de_w_dT * Cstar

    """
    Cache-and-compare system, written by Kai Riedmiller (Heidelberg Scientific Software Centre 
    (https://www.ssc.uni-heidelberg.de/en/what-the-scientific-software-center-is-all-about/meet-our-team))
    See calc_Ceq for a description of how this works.
    """
    global DT_CEQUNIT_CACHE
    id = hash(dCeq_dT_unit)
    # TODO reformulate this using CONTEXTS? (see pint Github)
    if cache_hit := DT_CEQUNIT_CACHE.get(id): # if the hashed dCeq_dT_unit is in our cache...
        compat_unit, unconverted_unit, unit_change = cache_hit # access the relevant values in the cache
    else:
        if not isinstance(dCeq_dT_unit, Unit):  # create pint.Unit object from unit string argument
            dCeq_dT_unit = _u.Unit(dCeq_dT_unit)
        
        if dCeq_dT_unit.is_compatible_with(u_mol_kg_K):  # amount gas / mass water
            compat_unit = UEnum.MOL_KG_K
            unconverted_unit = u_mol_kg_K
        elif dCeq_dT_unit.is_compatible_with(u_mol_cc_K):  # amount gas / volume water
            compat_unit = UEnum.MOL_CC_K
            unconverted_unit = u_mol_cc_K
        elif dCeq_dT_unit.is_compatible_with(u_cc_g_K):  # volume gas / mass water
            compat_unit = UEnum.CC_G_K
            unconverted_unit = u_cc_g_K
        elif dCeq_dT_unit.is_compatible_with(u_kg_mol_K):  # mass gas / amount water
            compat_unit = UEnum.KG_MOL_K
            unconverted_unit = u_kg_mol_K
        elif dCeq_dT_unit.is_compatible_with(u_cc_mol_K):  # volume gas / amount water
            compat_unit = UEnum.CC_MOL_K
            unconverted_unit = u_cc_mol_K
        elif dCeq_dT_unit.is_compatible_with(u_kg_m3_K):  # mass gas / volume water
            compat_unit = UEnum.KG_M3_K
            unconverted_unit = u_kg_m3_K
        else:
            raise ValueError("Invalid/unimplemented value for unit. Try something like \"mol/kg\", \"mol/cc\" or \"cc/g\".")
        
        unit_change = unconverted_unit != dCeq_dT_unit
        DT_CEQUNIT_CACHE[id] = (compat_unit, unconverted_unit, unit_change) # add the dCeq_dT_unit to the cache if it's not already there
    
    if compat_unit == UEnum.MOL_KG_K:  # amount gas / mass water
        ret = dCeq_dT_molkgK
    elif compat_unit == UEnum.MOL_CC_K:  # amount gas / volume water
        ret = (dCeq_dT_molkgK * rho + pref * Cstar * drho_dT) * 1e-6 # *1e-6: mol/m3/K -> mol/cc/K
    elif compat_unit == UEnum.CC_G_K:  # volume gas / mass water
        ret = dCeq_dT_molkgK * mvol * 1e-3 # *1e-3: cc/kg/K -> cc/g/K
    elif compat_unit == UEnum.KG_MOL_K:  # mass gas / amount water
        ret = dCeq_dT_molkgK * mmass * MMW * 1e-6 # *1e-6: mg/mol/K -> kg/mol/K
    elif compat_unit == UEnum.CC_MOL_K:  # volume gas / amount water
        ret = dCeq_dT_molkgK * MMW * mvol * 1e-3 # *1e-3: μL/mol/K -> cc/mol/K
    elif compat_unit == UEnum.KG_M3_K:  # mass gas / volume water
        ret = (dCeq_dT_molkgK * mmass * rho + pref * mmass * drho_dT * Cstar) * 1e-3 # *1e-3: g/m^3/K -> kg/m^3/K
    else:
        raise ValueError("Invalid/unimplemented value for unit. Try something like \"mol/kg/K\", \"mol/cc/K\" or \"cc/g/K\".")

    # return, after conversion if necessary - written like this to avoid _sto() for speed reasons
    if not ret_quant and not unit_change:
        return ret
    elif not ret_quant:
        return _sto(ret * unconverted_unit, dCeq_dT_unit).magnitude
    elif not unit_change:
        return ret * unconverted_unit
    else:
        return _sto(ret * unconverted_unit, dCeq_dT_unit)

# cache to hold dCeq_dS_units if they have previously been used so that Unit.is_compatible_with()
# is called as infrequently as possible (it gets expensive when running fitting routines)
DS_CEQUNIT_CACHE = dict()
@_possibly_iterable
@wraptpint(None, (None, 'degC', 'permille', 'atm', None, None, None), strict=False)
def calc_dCeq_dS(gas:str, T:float|Quantity, S:float|Quantity, p:float|Quantity, dCeq_dS_unit:str|Unit='cc/g/permille', ret_quant:bool=False, ab='default') -> float|Iterable[float]|Quantity|Iterable[Quantity]:
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
    :param dCeq_dS_unit: Units in which dCeq_dS should be expressed
    :type dCeq_dS_unit: str | Unit, optional
    :param ret_quant: Whether to return the result as a Pint Quantity instead of just a float, defaults to False
    :type ret_quant: bool, optional
    :raises ValueError: If the units given in dCeq_dS_unit are unimplemented
    :return: Waterside equilibrium concentration salinity derivative dCeq_dS of the given gas
    :rtype: float|Iterable[float]|Quantity|Iterable[Quantity]
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
    
    drho_dS = calc_dens_Sderiv(T, S, magnitude=True)
    dCeq_dS_molkgpm = pref * dCstar_dS
    
    """
    Cache-and-compare system, written by Kai Riedmiller (Heidelberg Scientific Software Centre 
    (https://www.ssc.uni-heidelberg.de/en/what-the-scientific-software-center-is-all-about/meet-our-team))
    See calc_Ceq for a description of how this works.
    """
    global DS_CEQUNIT_CACHE
    id = hash(dCeq_dS_unit)
    # TODO reformulate this using CONTEXTS? (see pint Github)
    if cache_hit := DS_CEQUNIT_CACHE.get(id): # if the hashed dCeq_dS_unit is in our cache...
        compat_unit, unconverted_unit, unit_change = cache_hit # access the relevant values in the cache
    else:
        if not isinstance(dCeq_dS_unit, Unit):  # create pint.Unit object from unit string argument
            dCeq_dS_unit = _u.Unit(dCeq_dS_unit)
        
        if dCeq_dS_unit.is_compatible_with(u_mol_kg_permille):  # amount gas / mass water
            compat_unit = UEnum.MOL_KG_PERMILLE
            unconverted_unit = u_mol_kg_permille
        elif dCeq_dS_unit.is_compatible_with(u_mol_cc_permille):  # amount gas / volume water
            compat_unit = UEnum.MOL_CC_PERMILLE
            unconverted_unit = u_mol_cc_permille
        elif dCeq_dS_unit.is_compatible_with(u_cc_g_permille):  # volume gas / mass water
            compat_unit = UEnum.CC_G_PERMILLE
            unconverted_unit = u_cc_g_permille
        elif dCeq_dS_unit.is_compatible_with(u_kg_mol_permille):  # mass gas / amount water
            compat_unit = UEnum.KG_MOL_PERMILLE
            unconverted_unit = u_kg_mol_permille
        elif dCeq_dS_unit.is_compatible_with(u_cc_mol_permille):  # volume gas / amount water
            compat_unit = UEnum.CC_MOL_PERMILLE
            unconverted_unit = u_cc_mol_permille
        elif dCeq_dS_unit.is_compatible_with(u_kg_m3_permille):  # mass gas / volume water
            compat_unit = UEnum.KG_M3_PERMILLE
            unconverted_unit = u_kg_m3_permille
        else:
            raise ValueError("Invalid/unimplemented value for unit. Try something like \"mol/kg\", \"mol/cc\" or \"cc/g\".")
        
        unit_change = unconverted_unit != dCeq_dS_unit
        DS_CEQUNIT_CACHE[id] = (compat_unit, unconverted_unit, unit_change) # add the dCeq_dS_unit to the cache if it's not already there
    
    if compat_unit == UEnum.MOL_KG_PERMILLE:  # amount gas / mass water
        ret = dCeq_dS_molkgpm
    elif compat_unit == UEnum.MOL_CC_PERMILLE:  # amount gas / volume water
        ret = (dCeq_dS_molkgpm * rho + pref * Cstar * drho_dS) * 1e-6 # *1e-6: mol/m3/permille -> mol/cc/permille
    elif compat_unit == UEnum.CC_G_PERMILLE:  # volume gas / mass water
        ret = dCeq_dS_molkgpm * mvol * 1e-3 # *1e-3: cc/kg/permille -> cc/g/permille
    elif compat_unit == UEnum.KG_MOL_PERMILLE:  # mass gas / amount water
        ret = dCeq_dS_molkgpm * mmass * MMW * 1e-6 # *1e-6: mg/mol/permille -> kg/mol/permille
    elif compat_unit == UEnum.CC_MOL_PERMILLE:  # volume gas / amount water
        ret = dCeq_dS_molkgpm * MMW * mvol * 1e-3 # *1e-3: μL/mol/permille -> cc/mol/permille
    elif compat_unit == UEnum.KG_M3_PERMILLE:  # mass gas / volume water
        ret = (dCeq_dS_molkgpm * mmass * rho + pref * mmass * drho_dS * Cstar) * 1e-3 # *1e-3: g/m^3/permille -> kg/m^3/permille
    else:
        raise ValueError("Invalid/unimplemented value for unit. Try something like \"mol/kg/permille\", \"mol/cc/permille\" or \"cc/g/permille\".")

    # return, after conversion if necessary - written like this to avoid _sto() for speed reasons
    if not ret_quant and not unit_change:
        return ret
    elif not ret_quant:
        return _sto(ret * unconverted_unit, dCeq_dS_unit).magnitude
    elif not unit_change:
        return ret * unconverted_unit
    else:
        return _sto(ret * unconverted_unit, dCeq_dS_unit)


# cache to hold dCeq_dp_units if they have previously been used so that Unit.is_compatible_with()
# is called as infrequently as possible (it gets expensive when running fitting routines)
DP_CEQUNIT_CACHE = dict()
@_possibly_iterable
@wraptpint(None, (None, 'degC', 'permille', 'atm', None, None, None), strict=False)
def calc_dCeq_dp(gas:str, T:float|Quantity, S:float|Quantity, p:float|Quantity, dCeq_dp_unit:str|Unit='cc/g/atm', ret_quant:bool=False, ab='default') -> float|Iterable[float]|Quantity|Iterable[Quantity]:
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
    id = hash(dCeq_dp_unit)
    # TODO reformulate this using CONTEXTS? (see pint Github)
    if cache_hit := DP_CEQUNIT_CACHE.get(id): # if the hashed dCeq_dp_unit is in our cache...
        compat_unit, unconverted_unit, unit_change = cache_hit # access the relevant values in the cache
    else:
        if not isinstance(dCeq_dp_unit, Unit):  # create pint.Unit object from unit string argument
            dCeq_dp_unit = _u.Unit(dCeq_dp_unit)
        
        if dCeq_dp_unit.is_compatible_with(u_mol_kg_atm):  # amount gas / mass water
            compat_unit = UEnum.MOL_KG_ATM
            unconverted_unit = u_mol_kg_atm
        elif dCeq_dp_unit.is_compatible_with(u_mol_cc_atm):  # amount gas / volume water
            compat_unit = UEnum.MOL_CC_ATM
            unconverted_unit = u_mol_cc_atm
        elif dCeq_dp_unit.is_compatible_with(u_cc_g_atm):  # volume gas / mass water
            compat_unit = UEnum.CC_G_ATM
            unconverted_unit = u_cc_g_atm
        elif dCeq_dp_unit.is_compatible_with(u_kg_mol_atm):  # mass gas / amount water
            compat_unit = UEnum.KG_MOL_ATM
            unconverted_unit = u_kg_mol_atm
        elif dCeq_dp_unit.is_compatible_with(u_cc_mol_atm):  # volume gas / amount water
            compat_unit = UEnum.CC_MOL_ATM
            unconverted_unit = u_cc_mol_atm
        elif dCeq_dp_unit.is_compatible_with(u_kg_m3_atm):  # mass gas / volume water
            compat_unit = UEnum.KG_M3_ATM
            unconverted_unit = u_kg_m3_atm
        else:
            raise ValueError("Invalid/unimplemented value for unit. Try something like \"mol/kg/atm\", \"mol/cc/atm\" or \"cc/g/atm\".")
        
        unit_change = unconverted_unit != dCeq_dp_unit
        DP_CEQUNIT_CACHE[id] = (compat_unit, unconverted_unit, unit_change) # add the dCeq_dp_unit to the cache if it's not already there
    
    if compat_unit == UEnum.MOL_KG_ATM:  # amount gas / mass water
        ret = pref * Cstar
    elif compat_unit == UEnum.MOL_CC_ATM:  # amount gas / volume water
        ret = pref * Cstar * rho * 1e-6 # *1e-6: mol/m3/atm -> mol/cc/atm
    elif compat_unit == UEnum.CC_G_ATM:  # volume gas / mass water
        ret = pref * Cstar * mvol * 1e-3 # *1e-3: cc/kg/atm -> cc/g/atm
    elif compat_unit == UEnum.KG_MOL_ATM:  # mass gas / amount water
        ret = pref * Cstar * mmass * MMW * 1e-6 # *1e-6: mg/mol/atm -> kg/mol/atm
    elif compat_unit == UEnum.CC_MOL_ATM:  # volume gas / amount water
        ret = pref * Cstar * MMW * mvol * 1e-3 # *1e-3: μL/mol/atm -> cc/mol/atm
    elif compat_unit == UEnum.KG_M3_ATM:  # mass gas / volume water
        ret = pref * Cstar * mmass * rho * 1e-3 # *1e-3: g/m^3/atm -> kg/m^3/atm
    else:
        raise ValueError("Invalid/unimplemented value for unit. Try something like \"mol/kg/permille\", \"mol/cc/permille\" or \"cc/g/permille\".")

    # return, after conversion if necessary - written like this to avoid _sto() for speed reasons
    if not ret_quant and not unit_change:
        return ret
    elif not ret_quant:
        return _sto(ret * unconverted_unit, dCeq_dp_unit).magnitude
    elif not unit_change:
        return ret * unconverted_unit
    else:
        return _sto(ret * unconverted_unit, dCeq_dp_unit)


@_possibly_iterable
@wraptpint(None, (None, 'degC', 'permille', 'atm', None, None, None), strict=False)
def calc_solcoeff(gas:str, T:float|Quantity, S:float|Quantity, p:float|Quantity, solcoeff_type:str='dimensionless', ret_quant:bool=False, ab='default') -> float|Iterable[float]|Quantity|Iterable[Quantity]:
    """Calculate the solubility coefficient of a gas in water at water temperature T, salinity S and airside pressure p.\\
    **Default input units** --- `T`:°C, `S`:‰, `p`:atm\\
    **Output units** --- None\\
    The type of solubility coefficient (`solcoeff_type`) can be:
    * dimensionless (`['dimless', 'dimensionless', 'H']`)
    * amount gas / volume water / partial pressure (`['nv', 'Knv', 'nvp', 'Knvp']`)
    * STP volume gas / volume water / partial pressure (`['vv', 'Kvv', 'vvp', 'Kvvp']`)
    * amount gas / amount water / partial pressure (`['nn', 'Knn', 'nnp', 'Knnp']`)

    :param gas: Gas(es) for which the solubility coefficient should be calculated.
    :type gas: str
    :param T: Temperature
    :type T: float | Quantity
    :param S: Salinity
    :type S: float | Quantity
    :param p: Pressure
    :type p: float | Quantity
    :param solcoeff_type: Type of solubility coefficient, defaults to 'dimensionless'
    :type solcoeff_type: str, optional
    :param ret_quant: Whether to return the result as a Pint Quantity instead of just a float, defaults to False
    :type ret_quant: bool, optional
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
    C_w = calc_Ceq(gas, T, S, p, 'mol/m^3', ab)
    # calculate Ostwald coefficient L [L_g / L_w]
    L = C_w / C_g

    # TODO reformulate this using CONTEXTS? - in this case differentiating between mol_w and mol_g so that units can be used instead of arbitrary solcoeff_type argument (see pint Github)
    if solcoeff_type in ['dimless', 'dimensionless', 'L']:
        ret = L
        unit_out = u_dimless
    elif solcoeff_type in ['nv', 'Knv', 'nvp', 'Knvp']:       # amount gas / volume water / partial pressure
        ret = L / MGC / T_K
        unit_out = u_mol_m3_Pa
    elif solcoeff_type in ['vv', 'Kvv', 'vvp', 'Kvvp']:     # STP volume gas / volume water / partial pressure
        ret = L * TPW / PAT / T_K
        unit_out = u_perPa
    elif solcoeff_type in ['nn', 'Knn', 'nnp', 'Knnp']:     # amount gas / amount water / partial pressure
        rho = calc_dens(T, S)
        ret = 0.001 * L * MMW / MGC / T_K / rho
        unit_out = u_perPa
    else:
        raise ValueError("Invalid/unimplemented value for solcoeff_type. Available options: 'L' (dimensionless), 'Knv' (mol/m3/Pa), 'Kvv' (m3_STP/m3_w/Pa), 'Knn (mol_g/mol_w/Pa)'.")
    
    # return, after unit implementation if required:
    if not ret_quant:
        return ret
    else:
        return ret * unit_out