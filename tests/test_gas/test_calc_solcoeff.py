import sys
sys.path.insert(0, 'C:/Users/scopi/source/repos/PAGOS/PAGOS/src')

from pagos.gas import calc_henry
from pagos import Q
import numpy as np
from pint.testing import assert_allclose

def test_calc_henry_all_floats():
    assert_allclose(calc_henry('He', 5, 30, 0.98, magnitude=True), 121.99392393146768)
    assert_allclose(calc_henry('He', 5, 30, 0.98, units='dimensionless', magnitude=True), 121.99392393146768)

    assert_allclose(calc_henry('He', 5, 30, 0.98, magnitude=False), Q(121.99392393146768, 'dimensionless'))
    assert_allclose(calc_henry('He', 5, 30, 0.98, units='dimensionless', magnitude=False), Q(121.99392393146768, 'dimensionless'))

    assert_allclose(calc_henry(['He', 'Ne'], 5, 30, 0.98, magnitude=True), np.array([121.99392393146768, 97.45796966867545]))
    assert_allclose(calc_henry(['He', 'Ne'], 5, 30, 0.98, magnitude=False), Q([121.99392393146768, 97.45796966867545], 'dimensionless'))

def test_calc_henry_all_quants_default_units():
    assert_allclose(calc_henry('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), magnitude=True), 121.99392393146768)
    assert_allclose(calc_henry('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), units='dimensionless', magnitude=True), 121.99392393146768)

    assert_allclose(calc_henry('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), magnitude=False),  Q(121.99392393146768, 'dimensionless'))
    assert_allclose(calc_henry('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), units='dimensionless', magnitude=False),  Q(121.99392393146768, 'dimensionless'))

    assert_allclose(calc_henry(['He', 'Ne'], Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), magnitude=True), np.array([121.99392393146768, 97.45796966867545]))

def test_calc_henry_all_quants_custom_units():
    assert_allclose(calc_henry('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), magnitude=True), 121.99392393146768)
    assert_allclose(calc_henry('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), units='dimensionless', magnitude=True), 121.99392393146768)

    assert_allclose(calc_henry('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), magnitude=False),  Q(121.99392393146768, 'dimensionless'))
    assert_allclose(calc_henry('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), units='dimensionless', magnitude=False),  Q(121.99392393146768, 'dimensionless'))

    assert_allclose(calc_henry(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), magnitude=True), np.array([121.99392393146768, 97.45796966867545]))

def test_calc_henry_mixed():
    assert_allclose(calc_henry('He', 5, Q(3, 'percent'), Q(744.799893891099, 'mmHg'), magnitude=True), 121.99392393146768)
    assert_allclose(calc_henry('He', 5, Q(3, 'percent'), Q(744.799893891099, 'mmHg'), units='dimensionless', magnitude=True), 121.99392393146768)

    assert_allclose(calc_henry('He', Q(278.15, 'K'), 30, Q(744.799893891099, 'mmHg'), magnitude=False),  Q(121.99392393146768, 'dimensionless'))
    assert_allclose(calc_henry('He', Q(278.15, 'K'), 30, Q(744.799893891099, 'mmHg'), units='dimensionless', magnitude=False),  Q(121.99392393146768, 'dimensionless'))

    assert_allclose(calc_henry(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), 0.98, magnitude=True), np.array([121.99392393146768, 97.45796966867545]))
    