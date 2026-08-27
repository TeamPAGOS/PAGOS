from pagos.newcore import pQ, set_warn_nonmult, pCalc
from pagos.newwater import calc_dens, calc_dens_Tderiv, calc_dens_Sderiv
from pint.testing import assert_allclose, assert_equal

set_warn_nonmult(False)


def test_calc_dens():
    T_degC = pQ(8, "degC")
    S_permille = pQ(15, "permille")
    T_K = pQ(281.15, "K")
    S_percent = pQ(1.5, "percent")

    target_rho = pQ(1011.6124219164217, "kg/m^3")

    assert_equal(calc_dens(T_degC, S_permille), target_rho)
    assert_equal(calc_dens(T_K, S_percent), target_rho)


def test_calc_dens_Tderiv():
    T_degC = pQ(8, "degC")
    S_permille = pQ(15, "permille")
    T_K = pQ(281.15, "K")
    S_percent = pQ(1.5, "percent")

    target_drho_dT = pQ(-0.10132238658110286, "kg/m^3/K")

    assert_equal(calc_dens_Tderiv(T_degC, S_permille), target_drho_dT)
    assert_equal(calc_dens_Tderiv(T_K, S_percent), target_drho_dT)


def test_calc_dens_Sderiv():
    T_degC = pQ(8, "degC")
    S_permille = pQ(15, "permille")
    T_K = pQ(281.15, "K")
    S_percent = pQ(1.5, "percent")

    target_drho_dS = pQ(0.7816404881062651, "kg/m^3/permille")

    assert_equal(calc_dens_Sderiv(T_degC, S_permille), target_drho_dS)
    assert_equal(calc_dens_Sderiv(T_K, S_percent), target_drho_dS)
