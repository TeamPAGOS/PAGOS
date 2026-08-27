from pagos.newcore import pQ, set_warn_nonmult
from pagos.newwater import calc_kinvisc
from pint.testing import assert_equal

set_warn_nonmult(False)


def test_calc_kinvisc():
    T_degC = pQ(8, "degC")
    S_permille = pQ(15, "permille")
    T_K = pQ(281.15, "K")
    S_percent = pQ(1.5, "percent")

    target_nu = pQ(1.4061391442621585e-06, "m^2/s")

    assert_equal(calc_kinvisc(T_degC, S_permille), target_nu)
    assert_equal(calc_kinvisc(T_K, S_percent), target_nu)
    assert_equal(calc_kinvisc(8, 15), target_nu)
