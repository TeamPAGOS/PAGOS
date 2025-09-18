"""
Units for the PAGOS package. The universal UnitRegistry `u` is included here.
"""

from pint import UnitRegistry, Context
from enum import Enum, auto

from pagos.constants import MOLAR_MASSES, MOLAR_VOLUMES

"""
THE UNIT REGISTRY u

This is the object from which ALL units within PAGOS and with which PAGOS should
interact will come from. If the user defines another UnitRegistry v in their program, and then
attempts to use PAGOS, it will fail and throw: "ValueError: Cannot operate with Quantity and
Quantity of different registries."
"""
# unit registry
u = UnitRegistry()

# define units that distinguish beween gas and water phases
u.define('gram_gas = [mass_gas] = g_gas = g_g')
u.define('mole_gas = [amount_gas] = mol_gas = mol_g')
u.define('length_STP_gas = [STPlength_gas] = mSTP_gas = mSTP_g')
u.define('[STPvolume_gas] = [STPlength_gas] ** 3')
u.define('gram_water = [mass_water] = g_water = g_w')
u.define('mole_water = [amount_water] = mol_water = mol_w')
u.define('length_water = [length_water] = m_water = m_w')
u.define('[volume_water] = [length_water] ** 3')
# specially named units
u.define('mm3STP_gas = 1e-9 * mSTP_gas**3 = mm3STP_g')
u.define('cm3STP_gas = 1e-6 * mSTP_gas**3 = ccSTP_gas = cm3STP_g = ccSTP_g')
u.define('LSTP_gas = 1e-3 * mSTP_gas**3 = lSTP_gas = dm3STP_gas = dm3STP_g = lSTP_g = LSTP_g')
u.define('mm3_water = 1e-9 * m_water**3 = mm3_w')
u.define('cm3_water = 1e-6 * m_water**3 = cc_water = cm3_w = cc_w')
u.define('L_water = 1e-3 * m_water**3 = l_water = dm3_water = dm3_w = l_w = L_w')
u.define('m3_water = m_water**3 = m3_w')

# Make physicochemical context with conversion between grams and moles of substance
pc = Context('pc', defaults={'gas': None, 'T': None, 'S': None})
# gas phase transformations
pc.add_transformation('[amount_gas]', '[mass_gas]', lambda ureg, n, gas, T, S:n * u.Quantity(MOLAR_MASSES[gas], u.g_gas/u.mol_gas))
pc.add_transformation('[mass_gas]', '[amount_gas]', lambda ureg, m, gas, T, S:m / u.Quantity(MOLAR_MASSES[gas], u.g_gas/u.mol_gas))
pc.add_transformation('[amount_gas]', '[STPvolume_gas]', lambda ureg, n, gas, T, S:n * u.Quantity(MOLAR_VOLUMES[gas], u.cm3STP_gas/u.mol_gas))
pc.add_transformation('[STPvolume_gas]', '[amount_gas]', lambda ureg, v, gas, T, S:v / u.Quantity(MOLAR_VOLUMES[gas], u.cm3STP_gas/u.mol_gas))
# water phase transformations
pc.add_transformation('[amount_water]', '[mass_water]', lambda ureg, n, gas, T, S:n * u.Quantity(18.0153, u.g_water/u.mol_water))
pc.add_transformation('[mass_water]', '[amount_water]', lambda ureg, m, gas, T, S:m / u.Quantity(18.0153, u.g_water/u.mol_water))
pc.add_transformation('[mass_water]', '[volume_water]', lambda ureg, m, gas, T, S:m / (__dens__(T, S) * u.kg_water/u.m3_water))
pc.add_transformation('[volume_water]', '[mass_water]', lambda ureg, v, gas, T, S:v * __dens__(T, S) * u.kg_water/u.m3_water)
# inverted transformations so that units ^-1 can be handled
# gas phase inverse transformations
pc.add_transformation('[amount_gas]^-1', '[mass_gas]^-1', lambda ureg, n, gas, T, S: n / u.Quantity(MOLAR_MASSES[gas], u.g_gas/u.mol_gas))
pc.add_transformation('[mass_gas]^-1', '[amount_gas]^-1', lambda ureg, m, gas, T, S: m * u.Quantity(MOLAR_MASSES[gas], u.g_gas/u.mol_gas))
pc.add_transformation('[amount_gas]^-1', '[STPvolume_gas]^-1', lambda ureg, n, gas, T, S: n / u.Quantity(MOLAR_VOLUMES[gas], u.cm3STP_gas/u.mol_gas))
pc.add_transformation('[STPvolume_gas]^-1', '[amount_gas]^-1', lambda ureg, v, gas, T, S: v * u.Quantity(MOLAR_VOLUMES[gas], u.cm3STP_gas/u.mol_gas))
# water phase inverse  transformations
pc.add_transformation('[amount_water]^-1', '[mass_water]^-1', lambda ureg, n, gas, T, S: n / u.Quantity(18.0153, u.g_water/u.mol_water))
pc.add_transformation('[mass_water]^-1', '[amount_water]^-1', lambda ureg, m, gas, T, S: m * u.Quantity(18.0153, u.g_water/u.mol_water))
pc.add_transformation('[mass_water]^-1', '[volume_water]^-1', lambda ureg, m, gas, T, S: m * (__dens__(T, S) * u.kg_water/u.m3_water))
pc.add_transformation('[volume_water]^-1', '[mass_water]^-1', lambda ureg, v, gas, T, S: v / (__dens__(T, S) * u.kg_water/u.m3_water))

u.add_context(pc)
u.enable_contexts('pc')

# common units that PAGOS methods will access. We define them explicitly here to avoid many
# __getattr__ calls
u_mol_gas = u.mol_gas
u_kg_water = u.kg_water
u_ccSTP_gas = u.ccSTP_gas
u_g_gas = u.g_gas
u_g_water = u.g_water
u_m3_water = u.m3_water
u_mol_water = u.mol_water
u_K = u.K
u_permille = u.permille
u_atm = u.atm
u_mbar = u.mbar
u_Pa = u.Pa
u_dimless = u.dimensionless
u_m = u.m
u_s = u.s

# common unit combinations to avoid many __truediv__ calls
# used in calc_dens
uww_kg_m3 = u_kg_water / u_m3_water

# used in calc_dens_Tderiv
uww_kg_m3_K = u_kg_water / u_m3_water / u_K

# used in calc_dens_Sderiv
uww_kg_m3_pml = u_kg_water / u_m3_water / u_permille

# used in calc_vappres_Tderiv
u_mbar_K = u_mbar / u_K

# used in calc_kinvisc
u_m2_s = u_m**2 / u_s

# used in calc_Ceq
ugw_mol_kg = u_mol_gas / u_kg_water         # mol / kg
ugw_ccSTP_g = u_ccSTP_gas / u_g_water       # ccSTP / g
ugw_g_g = u_g_gas / u_g_water               # g / g
ugw_mol_m3 = u_mol_gas / u_m3_water         # mol / m3
ugw_ccSTP_m3 = u_ccSTP_gas / u_m3_water     # ccSTP / m3
ugw_g_m3 = u_g_gas / u_m3_water             # g / m3
ugw_mol_mol = u_mol_gas / u_mol_water       # mol / mol
ugw_ccSTP_mol = u_ccSTP_gas / u_mol_water   # ccSTP / mol
ugw_g_mol = u_g_gas / u_mol_water           # g / mol

# used in calc_dCeq_dT
ugw_mol_kg_K = u_mol_gas / u_kg_water / u_K         # mol / kg / K
ugw_ccSTP_g_K = u_ccSTP_gas / u_g_water / u_K       # ccSTP / g / K
ugw_g_g_K = u_g_gas / u_g_water / u_K               # g / g / K
ugw_mol_m3_K = u_mol_gas / u_m3_water / u_K         # mol / m3 / K
ugw_ccSTP_m3_K = u_ccSTP_gas / u_m3_water / u_K     # ccSTP / m3 / K
ugw_g_m3_K = u_g_gas / u_m3_water / u_K             # g / m3 / K
ugw_mol_mol_K = u_mol_gas / u_mol_water / u_K       # mol / mol / K
ugw_ccSTP_mol_K = u_ccSTP_gas / u_mol_water / u_K   # ccSTP / mol / K
ugw_g_mol_K = u_g_gas / u_mol_water / u_K       # g / mol / K

# used in calc_dCeq_dS
ugw_mol_kg_pml = u_mol_gas / u_kg_water / u_permille         # mol / kg / permille
ugw_ccSTP_g_pml = u_ccSTP_gas / u_g_water / u_permille       # ccSTP / g / permille
ugw_g_g_pml = u_g_gas / u_g_water / u_permille               # g / g / permille
ugw_mol_m3_pml = u_mol_gas / u_m3_water / u_permille         # mol / m3 / permille
ugw_ccSTP_m3_pml = u_ccSTP_gas / u_m3_water / u_permille     # ccSTP / m3 / permille
ugw_g_m3_pml = u_g_gas / u_m3_water / u_permille             # g / m3 / permille
ugw_mol_mol_pml = u_mol_gas / u_mol_water / u_permille       # mol / mol / permille
ugw_ccSTP_mol_pml = u_ccSTP_gas / u_mol_water / u_permille   # ccSTP / mol / permille
ugw_g_mol_pml = u_g_gas / u_mol_water / u_permille       # g / mol / permille

# used in calc_dCeq_dp
ugw_mol_kg_atm = u_mol_gas / u_kg_water / u_atm         # mol / kg / atm
ugw_ccSTP_g_atm = u_ccSTP_gas / u_g_water / u_atm       # ccSTP / g / atm
ugw_g_g_atm = u_g_gas / u_g_water / u_atm               # g / g / atm
ugw_mol_m3_atm = u_mol_gas / u_m3_water / u_atm         # mol / m3 / atm
ugw_ccSTP_m3_atm = u_ccSTP_gas / u_m3_water / u_atm     # ccSTP / m3 / atm
ugw_g_m3_atm = u_g_gas / u_m3_water / u_atm             # g / m3 / atm
ugw_mol_mol_atm = u_mol_gas / u_mol_water / u_atm       # mol / mol / atm
ugw_ccSTP_mol_atm = u_ccSTP_gas / u_mol_water / u_atm   # ccSTP / mol / atm
ugw_g_mol_atm = u_g_gas / u_mol_water / u_atm       # g / mol / atm

# used in calc_solcoeff
u_mol_m3_Pa = u_mol_gas / u_m3_water / u_Pa
u_perPa = u_Pa ** -1


# Enum of units combinations, used in caching in gas.py
class UEnum(Enum):
    DIMLESS = auto()
    PER_PA = auto()

    PA = auto()
    PA_K = auto()
    MBAR = auto()
    MBAR_K = auto()

    M2_S = auto()

    WW_KG_M3 = auto()
    WW_KG_M3_K = auto()
    WW_KG_M3_PML = auto()

    GW_MOL_KG = auto()
    GW_CCSTP_G = auto()
    GW_G_G = auto()
    GW_MOL_M3 = auto()
    GW_CCSTP_M3 = auto()
    GW_G_M3 = auto()
    GW_MOL_MOL = auto()
    GW_CCSTP_MOL = auto()
    GW_G_MOL = auto()

    GW_MOL_KG_K = auto()
    GW_CCSTP_G_K = auto()
    GW_G_G_K = auto()
    GW_MOL_M3_K = auto()
    GW_CCSTP_M3_K = auto()
    GW_G_M3_K = auto()
    GW_MOL_MOL_K = auto()
    GW_CCSTP_MOL_K = auto()
    GW_G_MOL_K = auto()

    GW_MOL_KG_PML = auto()
    GW_CCSTP_G_PML = auto()
    GW_G_G_PML = auto()
    GW_MOL_M3_PML = auto()
    GW_CCSTP_M3_PML = auto()
    GW_G_M3_PML = auto()
    GW_MOL_MOL_PML = auto()
    GW_CCSTP_MOL_PML = auto()
    GW_G_MOL_PML = auto()

    GW_MOL_KG_ATM = auto()
    GW_CCSTP_G_ATM = auto()
    GW_G_G_ATM = auto()
    GW_MOL_M3_ATM = auto()
    GW_CCSTP_M3_ATM = auto()
    GW_G_M3_ATM = auto()
    GW_MOL_MOL_ATM = auto()
    GW_CCSTP_MOL_ATM = auto()
    GW_G_MOL_ATM = auto()

# unit caches
DENSUNIT_CACHE = dict()
DT_DENSUNIT_CACHE = dict()
DS_DENSUNIT_CACHE = dict()
VPUNIT_CACHE = dict()
DT_VPUNIT_CACHE = dict()
KVUNIT_CACHE = dict()

SCUNIT_CACHE = dict()
CEQUNIT_CACHE = dict()
DT_CEQUNIT_CACHE = dict()
DS_CEQUNIT_CACHE = dict()
DP_CEQUNIT_CACHE = dict()
HENUNIT_CACHE = dict()

"""
FUNCTIONS FOR CALCULATING PROPERTIES OF SEAWATER
"""
from pagos.constants import GILL_82_COEFFS
def __dens__(T:float, S:float) -> float:
    """
    See water.calc_dens for documentation.
    """
    # NOTE: THIS FUNCTION IS DUPLICATED IN UNITS.PY TO AVOID CIRCULAR IMPORT; IF YOU CHANGE IT HERE, CHANGE IT THERE TOO
    a0, a1, a2, a3, a4, a5, b0, b1, b2, b3, b4, c0, c1, c2, d0 = GILL_82_COEFFS.values()

    if type(T) == u.Quantity:
        T = T.magnitude
    if type(S) == u.Quantity:
        S = S.magnitude
    rho0 = a0 + a1*T + a2*T**2 + a3*T**3 + a4*T**4 + a5*T**5
    ret = rho0 + S*(b0 + b1*T + b2*T**2 + b3*T**3 + b4*T**4) + \
          (S**(3/2))*(c0 + c1*T + c2*T**2) + \
          d0*S**2
    return ret