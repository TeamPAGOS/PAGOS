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
u_mol = u.mol
u_kg = u.kg
u_cc = u.cc
u_g = u.g
u_m3 = u.m**3
u_K = u.K
u_permille = u.permille
u_atm = u.atm
u_Pa = u.Pa
u_dimless = u.dimensionless

# common unit combinations to avoid many __truediv__ calls
# used in calc_Ceq
u_mol_kg = u_mol / u_kg
u_mol_g = u_mol / u_g
u_mol_cc = u_mol / u_cc
u_kg_mol = u_kg / u_mol
u_cc_mol = u_cc / u_mol
u_cc_g = u_cc / u_g
u_kg_m3 = u_kg / u_m3

# used in calc_dCeq_dT
u_mol_kg_K = u_mol / u_kg / u_K
u_mol_g_K = u_mol / u_g / u_K
u_mol_cc_K = u_mol / u_cc / u_K
u_kg_mol_K = u_kg / u_mol / u_K
u_cc_mol_K = u_cc / u_mol / u_K
u_cc_g_K = u_cc / u_g / u_K
u_kg_m3_K = u_kg / u_m3 / u_K

# used in calc_dCeq_dS
u_mol_kg_permille = u_mol / u_kg / u_permille
u_mol_g_permille = u_mol / u_g / u_permille
u_mol_cc_permille = u_mol / u_cc / u_permille
u_kg_mol_permille = u_kg / u_mol / u_permille
u_cc_mol_permille = u_cc / u_mol / u_permille
u_cc_g_permille = u_cc / u_g / u_permille
u_kg_m3_permille = u_kg / u_m3 / u_permille

# used in calc_dCeq_dp
u_mol_kg_atm = u_mol / u_kg / u_atm
u_mol_g_atm = u_mol / u_g / u_atm
u_mol_cc_atm = u_mol / u_cc / u_atm
u_kg_mol_atm = u_kg / u_mol / u_atm
u_cc_mol_atm = u_cc / u_mol / u_atm
u_cc_g_atm = u_cc / u_g / u_atm
u_kg_m3_atm = u_kg / u_m3 / u_atm

# used in calc_solcoeff
u_mol_m3_Pa = u_mol / u_m3 / u_Pa
u_perPa = u_Pa ** -1


# Enum of units combinations, used in caching in gas.py
class UEnum(Enum):
    DIMLESS = auto()
    PER_PA = auto()

    MOL_KG = auto()
    MOL_CC = auto()
    CC_G = auto()
    KG_MOL = auto()
    CC_MOL = auto()
    KG_M3 = auto()

    MOL_KG_K = auto()
    MOL_CC_K = auto()
    CC_G_K = auto()
    KG_MOL_K = auto()
    CC_MOL_K = auto()
    KG_M3_K = auto()

    MOL_KG_PERMILLE = auto()
    MOL_CC_PERMILLE = auto()
    CC_G_PERMILLE = auto()
    KG_MOL_PERMILLE = auto()
    CC_MOL_PERMILLE = auto()
    KG_M3_PERMILLE = auto()

    MOL_KG_ATM = auto()
    MOL_CC_ATM = auto()
    CC_G_ATM = auto()
    KG_MOL_ATM = auto()
    CC_MOL_ATM = auto()
    KG_M3_ATM = auto()


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