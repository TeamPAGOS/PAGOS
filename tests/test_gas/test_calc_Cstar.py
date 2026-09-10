from pint.testing import assert_allclose, assert_equal

from pagos.newcore import pCalc, pQ, set_warn_nonmult
from pagos.gasobject import calc_Cstar


def test_calc_Cstar_with_float_args():
    assert calc_Cstar("He", T=15, S=20) == pQ(1.8580524797612681e-09, "mol_He / kg")


def test_calc_Cstar_with_quantity_args():
    assert calc_Cstar("He", T=pQ(15, "degC"), S=pQ(20, "g/kg")) == pQ(
        1.8580524797612681e-09, "mol_He / kg"
    )


def test_calc_Cstar_with_mixed_args():
    assert calc_Cstar("He", T=15, S=pQ(20, "g/kg")) == pQ(
        1.8580524797612681e-09, "mol_He / kg"
    )
    assert calc_Cstar("He", T=pQ(15, "degC"), S=20) == pQ(
        1.8580524797612681e-09, "mol_He / kg"
    )
