import sys
sys.path.insert(0, 'C:/Users/scopi/source/repos/PAGOS/PAGOS/src')

from pagos.gas import calc_solcoeff
from pagos import Q
import numpy as np
from pint.testing import assert_allclose

def test_calc_solcoeff_all_floats():
    assert_allclose(calc_solcoeff('He', 5, 30, 0.98, magnitude=True), 0.00819712956000799)
    assert_allclose(calc_solcoeff('He', 5, 30, 0.98, units='LSTP_g/L_w', magnitude=True), 0.00819712956000799)

    assert_allclose(calc_solcoeff('He', 5, 30, 0.98, magnitude=False), Q(0.00819712956000799, 'LSTP_g/L_w'))
    assert_allclose(calc_solcoeff('He', 5, 30, 0.98, units='LSTP_g/L_w', magnitude=False), Q(0.00819712956000799, 'LSTP_g/L_w'))

    assert_allclose(calc_solcoeff(['He', 'Ne'], 5, 30, 0.98, magnitude=True), np.array([0.00819712956000799, 0.01026083349981193]))
    assert_allclose(calc_solcoeff(['He', 'Ne'], 5, 30, 0.98, magnitude=False), Q([0.00819712956000799, 0.01026083349981193], 'LSTP_g/L_w'))

def test_calc_solcoeff_all_quants_default_units():
    assert_allclose(calc_solcoeff('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), magnitude=True), 0.00819712956000799)
    assert_allclose(calc_solcoeff('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), units='LSTP_g/L_w', magnitude=True), 0.00819712956000799)

    assert_allclose(calc_solcoeff('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), magnitude=False),  Q(0.00819712956000799, 'LSTP_g/L_w'))
    assert_allclose(calc_solcoeff('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), units='LSTP_g/L_w', magnitude=False),  Q(0.00819712956000799, 'LSTP_g/L_w'))

    assert_allclose(calc_solcoeff(['He', 'Ne'], Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), magnitude=True), np.array([0.00819712956000799, 0.01026083349981193]))
    assert_allclose(calc_solcoeff(['He', 'Ne'], Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), units='cm3STP_g/cm3_w', magnitude=True), np.array([0.00819712956000799, 0.01026083349981193]))

def test_calc_solcoeff_all_quants_custom_units():
    assert_allclose(calc_solcoeff('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), magnitude=True), 0.00819712956000799)
    assert_allclose(calc_solcoeff('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), units='LSTP_g/L_w', magnitude=True), 0.00819712956000799)

    assert_allclose(calc_solcoeff('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), magnitude=False),  Q(0.00819712956000799, 'LSTP_g/L_w'))
    assert_allclose(calc_solcoeff('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), units='LSTP_g/L_w', magnitude=False),  Q(0.00819712956000799, 'LSTP_g/L_w'))

    assert_allclose(calc_solcoeff(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), magnitude=True), np.array([0.00819712956000799, 0.01026083349981193]))
    assert_allclose(calc_solcoeff(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), units='cm3STP_g/cm3_w', magnitude=True), np.array([0.00819712956000799, 0.01026083349981193]))

def test_calc_solcoeff_mixed():
    assert_allclose(calc_solcoeff('He', 5, Q(3, 'percent'), Q(744.799893891099, 'mmHg'), magnitude=True), 0.00819712956000799)
    assert_allclose(calc_solcoeff('He', 5, Q(3, 'percent'), Q(744.799893891099, 'mmHg'), units='LSTP_g/L_w', magnitude=True), 0.00819712956000799)

    assert_allclose(calc_solcoeff('He', Q(278.15, 'K'), 30, Q(744.799893891099, 'mmHg'), magnitude=False),  Q(0.00819712956000799, 'LSTP_g/L_w'))
    assert_allclose(calc_solcoeff('He', Q(278.15, 'K'), 30, Q(744.799893891099, 'mmHg'), units='LSTP_g/L_w', magnitude=False),  Q(0.00819712956000799, 'LSTP_g/L_w'))

    assert_allclose(calc_solcoeff(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), 0.98, magnitude=True), np.array([0.00819712956000799, 0.01026083349981193]))
    assert_allclose(calc_solcoeff(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), 0.98, units='cm3STP_g/cm3_w', magnitude=True), np.array([0.00819712956000799, 0.01026083349981193]))
    