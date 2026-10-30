from numpy.testing import assert_allclose

from pagos.new_water import (
    new_calc_dens,
    new_calc_dens_Sderiv,
    new_calc_dens_Tderiv,
    new_calc_kinvisc,
    new_calc_vappres,
    new_calc_vappres_Tderiv,
)


def test_calc_dens():
    rho = new_calc_dens(20, 20)
    assert_allclose(rho, 1013.361992394515)


def test_calc_dens_Sderiv():
    drhodS = new_calc_dens_Sderiv(20, 20)
    assert_allclose(drhodS, 0.7577394559086271)


def test_calc_dens_Tderiv():
    drhodT = new_calc_dens_Tderiv(20, 20)
    assert_allclose(drhodT, -0.24004752043855768)


def test_calc_vappres():
    pv = new_calc_vappres(20)
    assert_allclose(pv, 23.368677427751695)


def test_calc_vappres_Tderiv():
    dpv_dT = new_calc_vappres_Tderiv(20)
    assert_allclose(dpv_dT, 1.4470971600899605)


def test_calc_kinvisc():
    nu = new_calc_kinvisc(20, 20)
    assert_allclose(nu, 1.0289999429800068e-06)


if __name__ == "__main__":
    test_calc_dens()
    test_calc_dens_Sderiv()
    test_calc_dens_Tderiv()
    test_calc_vappres()
    test_calc_vappres_Tderiv()
    test_calc_kinvisc()
