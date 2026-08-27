from pagos.newcore import pQ, set_warn_nonmult
from pagos.newwater import calc_vappres, calc_vappres_Tderiv
from pint.testing import assert_equal

set_warn_nonmult(False)


def test_calc_vappres():
    T_degC = pQ(8, "degC")
    T_K = pQ(281.15, "K")

    target_pv = pQ(10.722034932109734, "mbar")

    assert_equal(calc_vappres(T_degC), target_pv)
    assert_equal(calc_vappres(T_K), target_pv)
    assert_equal(calc_vappres(8), target_pv)


def test_calc_vappres_Tderiv():
    T_degC = pQ(8, "degC")
    T_K = pQ(281.15, "K")

    target_dpv_dT = pQ(0.7298484017763172, "mbar/K")

    assert_equal(calc_vappres_Tderiv(T_degC), target_dpv_dT)
    assert_equal(calc_vappres_Tderiv(T_K), target_dpv_dT)
    assert_equal(calc_vappres_Tderiv(8), target_dpv_dT)
