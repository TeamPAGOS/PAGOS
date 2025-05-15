"""
Units for the PAGOS package. The universal UnitRegistry `u` is included here.
"""

from pint import UnitRegistry
from enum import Enum, auto

"""
THE UNIT REGISTRY u

This is the object from which ALL units within PAGOS and with which PAGOS should
interact will come from. If the user defines another UnitRegistry v in their program, and then
attempts to use PAGOS, it will fail and throw: "ValueError: Cannot operate with Quantity and
Quantity of different registries."
"""
# unit registry
u = UnitRegistry()

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