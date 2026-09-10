from pint.testing import assert_allclose, assert_equal

from pagos.newcore import pCalc, pQ, set_warn_nonmult
from pagos.gasobject import calc_Ceq


def test_calc_Cstar_with_float_args():
    assert calc_Ceq("He", T=15, S=20, p=0.97) == pQ(
        1.8013573277458656e-09, "mol_He / kg"
    )


def test_calc_Cstar_with_quantity_args():
    assert calc_Ceq("He", T=pQ(15, "degC"), S=pQ(20, "g/kg"), p=0.97) == pQ(
        1.8013573277458656e-09, "mol_He / kg"
    )
    assert calc_Ceq("He", T=pQ(288.15, "K"), S=pQ(2, "percent"), p=0.97) == pQ(
        1.8013573277458656e-09, "mol_He / kg"
    )


def test_calc_Cstar_with_mixed_args():
    assert calc_Ceq("He", T=15, S=pQ(20, "g/kg"), p=0.97) == pQ(
        1.8013573277458656e-09, "mol_He / kg"
    )
    assert calc_Ceq("He", T=pQ(15, "degC"), S=20, p=pQ(982.8525, "mbar")) == pQ(
        1.8013573277458656e-09, "mol_He / kg"
    )
