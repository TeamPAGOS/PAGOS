from pint.testing import assert_allclose, assert_equal

from pagos.newcore import pCalc, pQ, set_warn_nonmult
from pagos.gasobject import calc_Sc


def test_calc_Sc_with_float_args():
    assert calc_Sc("He", T=15, S=20) == 193.58579233493526
    assert calc_Sc("He", T=15, S=20) == pQ(193.58579233493526, "dimensionless")


def test_calc_Sc_with_quantity_args():
    assert calc_Sc("He", T=pQ(15, "degC"), S=pQ(20, "g/kg")) == 193.58579233493526
    assert calc_Sc("He", T=pQ(15, "degC"), S=pQ(20, "g/kg")) == pQ(
        193.58579233493526, "dimensionless"
    )


def test_calc_Sc_with_mixed_args():
    assert calc_Sc("He", T=15, S=pQ(20, "g/kg")) == 193.58579233493526
    assert calc_Sc("He", T=15, S=pQ(20, "g/kg")) == pQ(
        193.58579233493526, "dimensionless"
    )
    assert calc_Sc("He", T=pQ(15, "degC"), S=20) == 193.58579233493526
    assert calc_Sc("He", T=pQ(15, "degC"), S=20) == pQ(
        193.58579233493526, "dimensionless"
    )
