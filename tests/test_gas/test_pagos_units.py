from pint.testing import assert_allclose, assert_equal

from pagos.newcore import pCalc, pQ, set_warn_nonmult

import unittest

# battery of tests for PAGOS units and their combinations/conversions
# PAGOS units are anything involving mol_gas, gram_gas or cubic_centimeter_gas


def test_simple_PAGOS_units_can_initialise():
    n1 = pQ(5, "mol_Ar")  # 5 moles of argon
    n2 = pQ(5, "mol_SF6")  # 5 moles of SF6
    n3 = pQ(5, "mol_gas", gas="He")  # 5 moles of a gas <- helium
    n4 = pQ(5, "mol_g")  # 5 moles of a gas <- ...

    m1 = pQ(5, "g_Ar")  # 5 grams of argon
    m2 = pQ(5, "g_SF6")  # 5 grams of SF6
    m3 = pQ(5, "g_gas", gas="He")  # 5 grams of a gas <- helium
    m4 = pQ(5, "g_g")  # 5 grams of a gas <- ...

    v1 = pQ(5, "ccSTP_Ar")  # 5 ccSTP of argon
    v2 = pQ(5, "ccSTP_SF6")  # 5 ccSTP of SF6
    v3 = pQ(5, "ccSTP_gas", gas="He")  # 5 ccSTP of a gas <- helium
    v4 = pQ(5, "ccSTP_g")  # 5 ccSTP of a gas <- ...


def test_compound_PAGOS_units_can_initialise():
    n_m = pQ(5, "mol_Ar / kg")  # mole argon per kilogram
    v_t = pQ(5, "ccSTP_g / s")  # ccSTP ... per second
    m_T1 = pQ(5, "g_He / K")  # gram helium per kelvin
    m_T2 = pQ(5, "mol_He / degC")  # gram helium per delta-degC (automatic delta)

    n_mm = pQ(5, "mol_SF6 / kg^2")
    m_TT = pQ(5, "g_g / K^2")
    v_TT = pQ(5, "ccSTP_g / degC^2")
    vv_mm = pQ(5, "ccSTP_g^2 / kg^2")
    mm = pQ(5, "g_He^2")
    mnv_Ttm = pQ(5, "g_Ar * mol_Ar * ccSTP_Ar / K / s / kg")


def test_PAGOS_units_can_be_prefixed():
    n_m = pQ(5, "umol_Ar / g")
    m_t = pQ(5, "kg_Ar / s")
    m_m = pQ(5, "mg_g / kg")


class TestConversions(unittest.TestCase):
    def test_PAGOSQuantity_to_method(self):
        # check good conversion works
        x = pQ(5, "mol_He").to("g_He")
        assert x == pQ(20.01301, "g_He")
        assert x != pQ(20.01301, "mol_He")
        assert x != pQ(5, "g_He")
        assert x == pQ(5.0, "mol_He")

        # check good generic conversion works (specific gas -> generic)
        assert pQ(5, "mol_He").to("mol_g") == x
        assert pQ(5, "mol_He").to("ccSTP_g") == x

        # check bad conversion does NOT work (generic gas -> specific)
        with self.assertRaises(ValueError):
            pQ(5, "mol_g").to("mol_He")
