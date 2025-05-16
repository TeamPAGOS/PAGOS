
from pagos.gas import calc_solcoeff
from pagos import Q
import numpy as np
from numpy.testing import assert_allclose

def test_calc_solcoeff_all_floats():
    assert_allclose(calc_solcoeff('He', 5, 30, 0.98), 0.00819712956000799) # <- this will likely fail in future due to changing the default value of ret_quant; be sure to update appropriately
    assert_allclose(calc_solcoeff('He', 5, 30, 0.98, solcoeff_type='L'), 0.00819712956000799) # <- "
    assert_allclose(calc_solcoeff('He', 5, 30, 0.98, solcoeff_type='Knv'), 3.5444486328252232e-06) # <- "
    assert_allclose(calc_solcoeff('He', 5, 30, 0.98, solcoeff_type='Kvv'), 7.944513869340828e-08) # <- "

    assert_allclose(calc_solcoeff('He', 5, 30, 0.98, ret_quant=True), Q(0.00819712956000799, 'dimensionless'))
    assert_allclose(calc_solcoeff('He', 5, 30, 0.98, solcoeff_type='L', ret_quant=True), Q(0.00819712956000799, 'dimensionless'))
    assert_allclose(calc_solcoeff('He', 5, 30, 0.98, solcoeff_type='nv', ret_quant=True), Q(3.5444486328252232e-06, 'mol/m^3/Pa'))
    assert_allclose(calc_solcoeff('He', 5, 30, 0.98, solcoeff_type='Kvv', ret_quant=True), Q(7.944513869340828e-08, 'Pa^-1'))

    assert_allclose(calc_solcoeff(['He', 'Ne'], 5, 30, 0.98), np.array([0.00819712956000799, 0.01026083349981193]))
    assert_allclose(calc_solcoeff(['He', 'Ne'], 5, 30, 0.98, ret_quant=True), Q([0.00819712956000799, 0.01026083349981193], 'dimensionless'))
    assert_allclose(calc_solcoeff(['He', 'Ne'], 5, 30, 0.98, solcoeff_type='Kvv'), np.array([7.944513869340828e-08, 9.944619449222586e-08]))
    assert_allclose(calc_solcoeff(['He', 'Ne'], 5, 30, 0.98, solcoeff_type='Kvv', ret_quant=True), Q([7.944513869340828e-08, 9.944619449222586e-08], 'mol/m^3/Pa'))

def test_calc_solcoeff_all_quants_default_units():
    assert_allclose(calc_solcoeff('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm')), 0.00819712956000799) # <- this will likely fail in future due to changing the default value of ret_quant; be sure to update appropriately
    assert_allclose(calc_solcoeff('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), solcoeff_type='L'), 0.00819712956000799) # <- "
    assert_allclose(calc_solcoeff('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), solcoeff_type='nv'), 3.5444486328252232e-06) # <- "
    assert_allclose(calc_solcoeff('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), solcoeff_type='Kvv'), 7.944513869340828e-08) # <- "

    assert_allclose(calc_solcoeff('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), ret_quant=True),  Q(0.00819712956000799, 'dimensionless'))
    assert_allclose(calc_solcoeff('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), solcoeff_type='L', ret_quant=True),  Q(0.00819712956000799, 'dimensionless'))
    assert_allclose(calc_solcoeff('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), solcoeff_type='nv', ret_quant=True), Q(3.5444486328252232e-06, 'mol/m^3/Pa'))
    assert_allclose(calc_solcoeff('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), solcoeff_type='Kvv', ret_quant=True), Q(7.944513869340828e-08, 'Pa^-1'))

    assert_allclose(calc_solcoeff(['He', 'Ne'], Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm')), np.array([0.00819712956000799, 0.01026083349981193]))
    assert_allclose(calc_solcoeff(['He', 'Ne'], Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), solcoeff_type='Kvv'), np.array([7.944513869340828e-08, 9.944619449222586e-08]))
    assert_allclose(calc_solcoeff(['He', 'Ne'], Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), ret_quant=True), Q([0.00819712956000799, 0.01026083349981193], 'mol/m^3/Pa'))
    assert_allclose(calc_solcoeff(['He', 'Ne'], Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), solcoeff_type='Kvv', ret_quant=True), Q([7.944513869340828e-08, 9.944619449222586e-08], 'Pa^-1'))

def test_calc_solcoeff_all_quants_custom_units():
    assert_allclose(calc_solcoeff('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg')), 0.00819712956000799) # <- this will likely fail in future due to changing the default value of ret_quant; be sure to update appropriately
    assert_allclose(calc_solcoeff('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), solcoeff_type='L'), 0.00819712956000799) # <- "
    assert_allclose(calc_solcoeff('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), solcoeff_type='nv'), 3.5444486328252232e-06) # <- "
    assert_allclose(calc_solcoeff('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), solcoeff_type='Kvv'), 7.944513869340828e-08) # <- "

    assert_allclose(calc_solcoeff('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), ret_quant=True),  Q(0.00819712956000799, 'dimensionless'))
    assert_allclose(calc_solcoeff('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), solcoeff_type='L', ret_quant=True),  Q(0.00819712956000799, 'dimensionless'))
    assert_allclose(calc_solcoeff('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), solcoeff_type='nv', ret_quant=True), Q(3.5444486328252232e-06, 'mol/m^3/Pa'))
    assert_allclose(calc_solcoeff('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), solcoeff_type='Kvv', ret_quant=True), Q(7.944513869340828e-08, 'Pa^-1'))

    assert_allclose(calc_solcoeff(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg')), np.array([0.00819712956000799, 0.01026083349981193]))
    assert_allclose(calc_solcoeff(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), solcoeff_type='Kvv'), np.array([7.944513869340828e-08, 9.944619449222586e-08]))
    assert_allclose(calc_solcoeff(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), ret_quant=True), Q([0.00819712956000799, 0.01026083349981193], 'mol/m^3/Pa'))
    assert_allclose(calc_solcoeff(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), solcoeff_type='Kvv', ret_quant=True), Q([7.944513869340828e-08, 9.944619449222586e-08], 'Pa^-1'))

def test_calc_solcoeff_mixed():
    assert_allclose(calc_solcoeff('He', 5, Q(3, 'percent'), Q(744.799893891099, 'mmHg')), 0.00819712956000799) # <- this will likely fail in future due to changing the default value of ret_quant; be sure to update appropriately
    assert_allclose(calc_solcoeff('He', 5, Q(3, 'percent'), Q(744.799893891099, 'mmHg'), solcoeff_type='L'), 0.00819712956000799) # <- "
    assert_allclose(calc_solcoeff('He', 5, Q(3, 'percent'), Q(744.799893891099, 'mmHg'), solcoeff_type='nv'), 3.5444486328252232e-06) # <- "
    assert_allclose(calc_solcoeff('He', 5, Q(3, 'percent'), Q(744.799893891099, 'mmHg'), solcoeff_type='Kvv'), 7.944513869340828e-08) # <- "

    assert_allclose(calc_solcoeff('He', Q(278.15, 'K'), 30, Q(744.799893891099, 'mmHg'), ret_quant=True),  Q(0.00819712956000799, 'dimensionless'))
    assert_allclose(calc_solcoeff('He', Q(278.15, 'K'), 30, Q(744.799893891099, 'mmHg'), solcoeff_type='L', ret_quant=True),  Q(0.00819712956000799, 'dimensionless'))
    assert_allclose(calc_solcoeff('He', Q(278.15, 'K'), 30, Q(744.799893891099, 'mmHg'), solcoeff_type='nv', ret_quant=True), Q(3.5444486328252232e-06, 'mol/m^3/Pa'))
    assert_allclose(calc_solcoeff('He', Q(278.15, 'K'), 30, Q(744.799893891099, 'mmHg'), solcoeff_type='Kvv', ret_quant=True), Q(7.944513869340828e-08, 'Pa^-1'))

    assert_allclose(calc_solcoeff(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), 0.98), np.array([0.00819712956000799, 0.01026083349981193]))
    assert_allclose(calc_solcoeff(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), 0.98, solcoeff_type='Kvv'), np.array([7.944513869340828e-08, 9.944619449222586e-08]))
    assert_allclose(calc_solcoeff(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), 0.98, ret_quant=True), Q([0.00819712956000799, 0.01026083349981193], 'mol/m^3/Pa'))
    assert_allclose(calc_solcoeff(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), 0.98, solcoeff_type='Kvv', ret_quant=True), Q([7.944513869340828e-08, 9.944619449222586e-08], 'Pa^-1'))
