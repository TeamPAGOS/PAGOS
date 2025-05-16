# Tests calc_Ceq() from pagos.gas and its associated derivatives. Tests are not carried out for all
# possible gases, as in theory test_calc_Cstar should handle any discrepancies (up to errors in the
# abn() function, but test_getters.py should also handle most of those cases).

from pagos.gas import calc_Ceq, calc_dCeq_dT, calc_dCeq_dS, calc_dCeq_dp, calc_solcoeff
from pagos import Q
import numpy as np

def test_calc_Ceq_all_floats():
    assert calc_Ceq('He', 5, 30, 0.98) == 4.004634568050064e-08 # <- this will likely fail in future due to changing the default value of ret_quant; be sure to update appropriately
    assert calc_Ceq('He', 5, 30, 0.98, Ceq_unit='cc/g') == 4.004634568050064e-08 # <- "
    assert calc_Ceq('He', 5, 30, 0.98, Ceq_unit='g/mol') == 1.2876990243812647e-10 # <- "
    assert calc_Ceq('He', 5, 30, 0.98, Ceq_unit='mol/m^3') == 1.828067122190318e-06 # <- "

    assert calc_Ceq('He', 5, 30, 0.98, ret_quant=True) == Q(4.004634568050064e-08, 'cc/g')
    assert calc_Ceq('He', 5, 30, 0.98, Ceq_unit='cc/g', ret_quant=True) == Q(4.004634568050064e-08, 'cc/g')
    assert calc_Ceq('He', 5, 30, 0.98, Ceq_unit='g/mol', ret_quant=True) == Q(1.2876990243812647e-10, 'g/mol')
    assert calc_Ceq('He', 5, 30, 0.98, Ceq_unit='mol/m^3', ret_quant=True) == Q(1.828067122190318e-06, 'mol/m^3')

    assert all(calc_Ceq(['He', 'Ne'], 5, 30, 0.98) == np.array([4.004634568050064e-08, 1.7391096248593038e-07]))
    assert all(calc_Ceq(['He', 'Ne'], 5, 30, 0.98, Ceq_unit='mol/m^3') == np.array([1.828067122190318e-06, 7.939178580807624e-06]))
    assert all(calc_Ceq(['He', 'Ne'], 5, 30, 0.98, ret_quant=True) == Q([4.004634568050064e-08, 1.7391096248593038e-07], 'cc/g'))
    assert all(calc_Ceq(['He', 'Ne'], 5, 30, 0.98, Ceq_unit='mol/m^3', ret_quant=True) == Q([1.828067122190318e-06, 7.939178580807624e-06], 'mol/m^3'))

def test_calc_Ceq_all_quants_default_units():
    assert calc_Ceq('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm')) == 4.004634568050064e-08 # <- this will likely fail in future due to changing the default value of ret_quant; be sure to update appropriately
    assert calc_Ceq('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), Ceq_unit='cc/g') == 4.004634568050064e-08 # <- "
    assert calc_Ceq('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), Ceq_unit='g/mol') == 1.2876990243812647e-10 # <- "
    assert calc_Ceq('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), Ceq_unit='mol/m^3') == 1.828067122190318e-06 # <- "

    assert calc_Ceq('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), ret_quant=True) == Q(4.004634568050064e-08, 'cc/g')
    assert calc_Ceq('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), Ceq_unit='cc/g', ret_quant=True) == Q(4.004634568050064e-08, 'cc/g')
    assert calc_Ceq('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), Ceq_unit='g/mol', ret_quant=True) == Q(1.2876990243812647e-10, 'g/mol')
    assert calc_Ceq('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), Ceq_unit='mol/m^3', ret_quant=True) == Q(1.828067122190318e-06, 'mol/m^3')

    assert all(calc_Ceq(['He', 'Ne'], Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm')) == np.array([4.004634568050064e-08, 1.7391096248593038e-07]))
    assert all(calc_Ceq(['He', 'Ne'], Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), Ceq_unit='mol/m^3') == np.array([1.828067122190318e-06, 7.939178580807624e-06]))
    assert all(calc_Ceq(['He', 'Ne'], Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), ret_quant=True) == Q([4.004634568050064e-08, 1.7391096248593038e-07], 'cc/g'))
    assert all(calc_Ceq(['He', 'Ne'], Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), Ceq_unit='mol/m^3', ret_quant=True) == Q([1.828067122190318e-06, 7.939178580807624e-06], 'mol/m^3'))

def test_calc_Ceq_all_quants_custom_units():
    assert calc_Ceq('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg')) == 4.004634568050064e-08 # <- this will likely fail in future due to changing the default value of ret_quant; be sure to update appropriately
    assert calc_Ceq('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), Ceq_unit='cc/g') == 4.004634568050064e-08 # <- "
    assert calc_Ceq('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), Ceq_unit='g/mol') == 1.2876990243812647e-10 # <- "
    assert calc_Ceq('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), Ceq_unit='mol/m^3') == 1.828067122190318e-06 # <- "

    assert calc_Ceq('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), ret_quant=True) == Q(4.004634568050064e-08, 'cc/g')
    assert calc_Ceq('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), Ceq_unit='cc/g', ret_quant=True) == Q(4.004634568050064e-08, 'cc/g')
    assert calc_Ceq('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), Ceq_unit='g/mol', ret_quant=True) == Q(1.2876990243812647e-10, 'g/mol')
    assert calc_Ceq('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), Ceq_unit='mol/m^3', ret_quant=True) == Q(1.828067122190318e-06, 'mol/m^3')

    assert all(calc_Ceq(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg')) == np.array([4.004634568050064e-08, 1.7391096248593038e-07]))
    assert all(calc_Ceq(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), Ceq_unit='mol/m^3') == np.array([1.828067122190318e-06, 7.939178580807624e-06]))
    assert all(calc_Ceq(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), ret_quant=True) == Q([4.004634568050064e-08, 1.7391096248593038e-07], 'cc/g'))
    assert all(calc_Ceq(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), Ceq_unit='mol/m^3', ret_quant=True) == Q([1.828067122190318e-06, 7.939178580807624e-06], 'mol/m^3'))

def test_calc_Ceq_mixed():
    assert calc_Ceq('He', 5, Q(3, 'percent'), Q(744.799893891099, 'mmHg')) == 4.004634568050064e-08 # <- this will likely fail in future due to changing the default value of ret_quant; be sure to update appropriately
    assert calc_Ceq('He', 5, Q(3, 'percent'), Q(744.799893891099, 'mmHg'), Ceq_unit='cc/g') == 4.004634568050064e-08 # <- "
    assert calc_Ceq('He', 5, Q(3, 'percent'), Q(744.799893891099, 'mmHg'), Ceq_unit='g/mol') == 1.2876990243812647e-10 # <- "
    assert calc_Ceq('He', 5, Q(3, 'percent'), Q(744.799893891099, 'mmHg'), Ceq_unit='mol/m^3') == 1.828067122190318e-06 # <- "

    assert calc_Ceq('He', Q(278.15, 'K'), 30, Q(744.799893891099, 'mmHg'), ret_quant=True) == Q(4.004634568050064e-08, 'cc/g')
    assert calc_Ceq('He', Q(278.15, 'K'), 30, Q(744.799893891099, 'mmHg'), Ceq_unit='cc/g', ret_quant=True) == Q(4.004634568050064e-08, 'cc/g')
    assert calc_Ceq('He', Q(278.15, 'K'), 30, Q(744.799893891099, 'mmHg'), Ceq_unit='g/mol', ret_quant=True) == Q(1.2876990243812647e-10, 'g/mol')
    assert calc_Ceq('He', Q(278.15, 'K'), 30, Q(744.799893891099, 'mmHg'), Ceq_unit='mol/m^3', ret_quant=True) == Q(1.828067122190318e-06, 'mol/m^3')

    assert all(calc_Ceq(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), 0.98) == np.array([4.004634568050064e-08, 1.7391096248593038e-07]))
    assert all(calc_Ceq(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), 0.98, Ceq_unit='mol/m^3') == np.array([1.828067122190318e-06, 7.939178580807624e-06]))
    assert all(calc_Ceq(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), 0.98, ret_quant=True) == Q([4.004634568050064e-08, 1.7391096248593038e-07], 'cc/g'))
    assert all(calc_Ceq(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), 0.98, Ceq_unit='mol/m^3', ret_quant=True) == Q([1.828067122190318e-06, 7.939178580807624e-06], 'mol/m^3'))


# T-derivatives

def test_calc_dCeq_dT_all_floats():
    assert calc_dCeq_dT('He', 5, 30, 0.98) == -1.6699136016129173e-10 # <- this will likely fail in future due to changing the default value of ret_quant; be sure to update appropriately
    assert calc_dCeq_dT('He', 5, 30, 0.98, dCeq_dT_unit='cc/g/K') == -1.6699136016129173e-10 # <- "
    assert calc_dCeq_dT('He', 5, 30, 0.98, dCeq_dT_unit='g/mol/K') == -5.369643794102802e-13 # <- "
    assert calc_dCeq_dT('He', 5, 30, 0.98, dCeq_dT_unit='mol/m^3/K') == -7.807765868185713e-09 # <- "

    assert calc_dCeq_dT('He', 5, 30, 0.98, ret_quant=True) == Q(-1.6699136016129173e-10, 'cc/g/K')
    assert calc_dCeq_dT('He', 5, 30, 0.98, dCeq_dT_unit='cc/g/K', ret_quant=True) == Q(-1.6699136016129173e-10, 'cc/g/K')
    assert calc_dCeq_dT('He', 5, 30, 0.98, dCeq_dT_unit='g/mol/K', ret_quant=True) == Q(-5.369643794102802e-13, 'g/mol/K')
    assert calc_dCeq_dT('He', 5, 30, 0.98, dCeq_dT_unit='mol/m^3/K', ret_quant=True) == Q(-7.807765868185713e-09, 'mol/m^3/K')

    assert all(calc_dCeq_dT(['He', 'Ne'], 5, 30, 0.98) == np.array([-1.6699136016129173e-10, -1.639218360334283e-09]))
    assert all(calc_dCeq_dT(['He', 'Ne'], 5, 30, 0.98, dCeq_dT_unit='mol/m^3/K') == np.array([-7.807765868185713e-09, -7.563429736712584e-08]))
    assert all(calc_dCeq_dT(['He', 'Ne'], 5, 30, 0.98, ret_quant=True) == Q([-1.6699136016129173e-10, -1.639218360334283e-09], 'cc/g/K'))
    assert all(calc_dCeq_dT(['He', 'Ne'], 5, 30, 0.98, dCeq_dT_unit='mol/m^3/K', ret_quant=True) == Q([-7.807765868185713e-09, -7.563429736712584e-08], 'mol/m^3/K'))

def test_calc_dCeq_dT_all_quants_default_units():
    assert calc_dCeq_dT('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm')) == -1.6699136016129173e-10 # <- this will likely fail in future due to changing the default value of ret_quant; be sure to update appropriately
    assert calc_dCeq_dT('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), dCeq_dT_unit='cc/g/K') == -1.6699136016129173e-10 # <- "
    assert calc_dCeq_dT('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), dCeq_dT_unit='g/mol/K') == -5.369643794102802e-13 # <- "
    assert calc_dCeq_dT('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), dCeq_dT_unit='mol/m^3/K') == -7.807765868185713e-09 # <- "

    assert calc_dCeq_dT('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), ret_quant=True) == Q(-1.6699136016129173e-10, 'cc/g/K')
    assert calc_dCeq_dT('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), dCeq_dT_unit='cc/g/K', ret_quant=True) == Q(-1.6699136016129173e-10, 'cc/g/K')
    assert calc_dCeq_dT('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), dCeq_dT_unit='g/mol/K', ret_quant=True) == Q(-5.369643794102802e-13, 'g/mol/K')
    assert calc_dCeq_dT('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), dCeq_dT_unit='mol/m^3/K', ret_quant=True) == Q(-7.807765868185713e-09, 'mol/m^3/K')

    assert all(calc_dCeq_dT(['He', 'Ne'], Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm')) == np.array([-1.6699136016129173e-10, -1.639218360334283e-09]))
    assert all(calc_dCeq_dT(['He', 'Ne'], Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), dCeq_dT_unit='mol/m^3/K') == np.array([-7.807765868185713e-09, -7.563429736712584e-08]))
    assert all(calc_dCeq_dT(['He', 'Ne'], Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), ret_quant=True) == Q([-1.6699136016129173e-10, -1.639218360334283e-09], 'cc/g/K'))
    assert all(calc_dCeq_dT(['He', 'Ne'], Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), dCeq_dT_unit='mol/m^3/K', ret_quant=True) == Q([-7.807765868185713e-09, -7.563429736712584e-08], 'mol/m^3/K'))

def test_calc_dCeq_dT_all_quants_custom_units():
    assert calc_dCeq_dT('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg')) == -1.6699136016129173e-10 # <- this will likely fail in future due to changing the default value of ret_quant; be sure to update appropriately
    assert calc_dCeq_dT('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), dCeq_dT_unit='cc/g/K') == -1.6699136016129173e-10 # <- "
    assert calc_dCeq_dT('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), dCeq_dT_unit='g/mol/K') == -5.369643794102802e-13 # <- "
    assert calc_dCeq_dT('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), dCeq_dT_unit='mol/m^3/K') == -7.807765868185713e-09 # <- "

    assert calc_dCeq_dT('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), ret_quant=True) == Q(-1.6699136016129173e-10, 'cc/g/K')
    assert calc_dCeq_dT('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), dCeq_dT_unit='cc/g/K', ret_quant=True) == Q(-1.6699136016129173e-10, 'cc/g/K')
    assert calc_dCeq_dT('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), dCeq_dT_unit='g/mol/K', ret_quant=True) == Q(-5.369643794102802e-13, 'g/mol/K')
    assert calc_dCeq_dT('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), dCeq_dT_unit='mol/m^3/K', ret_quant=True) == Q(-7.807765868185713e-09, 'mol/m^3/K')

    assert all(calc_dCeq_dT(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg')) == np.array([-1.6699136016129173e-10, -1.639218360334283e-09]))
    assert all(calc_dCeq_dT(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), dCeq_dT_unit='mol/m^3/K') == np.array([-7.807765868185713e-09, -7.563429736712584e-08]))
    assert all(calc_dCeq_dT(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), ret_quant=True) == Q([-1.6699136016129173e-10, -1.639218360334283e-09], 'cc/g/K'))
    assert all(calc_dCeq_dT(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), dCeq_dT_unit='mol/m^3/K', ret_quant=True) == Q([-7.807765868185713e-09, -7.563429736712584e-08], 'mol/m^3/K'))

def test_calc_dCeq_dT_mixed():
    assert calc_dCeq_dT('He', 5, Q(3, 'percent'), Q(744.799893891099, 'mmHg')) == -1.6699136016129173e-10 # <- this will likely fail in future due to changing the default value of ret_quant; be sure to update appropriately
    assert calc_dCeq_dT('He', 5, Q(3, 'percent'), Q(744.799893891099, 'mmHg'), dCeq_dT_unit='cc/g/K') == -1.6699136016129173e-10 # <- "
    assert calc_dCeq_dT('He', 5, Q(3, 'percent'), Q(744.799893891099, 'mmHg'), dCeq_dT_unit='g/mol/K') == -5.369643794102802e-13 # <- "
    assert calc_dCeq_dT('He', 5, Q(3, 'percent'), Q(744.799893891099, 'mmHg'), dCeq_dT_unit='mol/m^3/K') == -7.807765868185713e-09 # <- "

    assert calc_dCeq_dT('He', Q(278.15, 'K'), 30, Q(744.799893891099, 'mmHg'), ret_quant=True) == Q(-1.6699136016129173e-10, 'cc/g/K')
    assert calc_dCeq_dT('He', Q(278.15, 'K'), 30, Q(744.799893891099, 'mmHg'), dCeq_dT_unit='cc/g/K', ret_quant=True) == Q(-1.6699136016129173e-10, 'cc/g/K')
    assert calc_dCeq_dT('He', Q(278.15, 'K'), 30, Q(744.799893891099, 'mmHg'), dCeq_dT_unit='g/mol/K', ret_quant=True) == Q(-5.369643794102802e-13, 'g/mol/K')
    assert calc_dCeq_dT('He', Q(278.15, 'K'), 30, Q(744.799893891099, 'mmHg'), dCeq_dT_unit='mol/m^3/K', ret_quant=True) == Q(-7.807765868185713e-09, 'mol/m^3/K')

    assert all(calc_dCeq_dT(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), 0.98) == np.array([-1.6699136016129173e-10, -1.639218360334283e-09]))
    assert all(calc_dCeq_dT(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), 0.98, dCeq_dT_unit='mol/m^3/K') == np.array([-7.807765868185713e-09, -7.563429736712584e-08]))
    assert all(calc_dCeq_dT(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), 0.98, ret_quant=True) == Q([-1.6699136016129173e-10, -1.639218360334283e-09], 'cc/g/K'))
    assert all(calc_dCeq_dT(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), 0.98, dCeq_dT_unit='mol/m^3/K', ret_quant=True) == Q([-7.807765868185713e-09, -7.563429736712584e-08], 'mol/m^3/K'))


# S-derivatives

def test_calc_dCeq_dS_all_floats():
    assert calc_dCeq_dS('He', 5, 30, 0.98) == -2.288808241950027e-10# <- this will likely fail in future due to changing the default value of ret_quant; be sure to update appropriately
    assert calc_dCeq_dS('He', 5, 30, 0.98, dCeq_dS_unit='cc/g/permille') == -2.288808241950027e-10# <- "
    assert calc_dCeq_dS('He', 5, 30, 0.98, dCeq_dS_unit='g/mol/permille') == -7.359713077615333e-13 # <- "
    assert calc_dCeq_dS('He', 5, 30, 0.98, dCeq_dS_unit='mol/m^3/permille') == -9.034427609203887e-09 # <- "

    assert calc_dCeq_dS('He', 5, 30, 0.98, ret_quant=True) == Q(-2.288808241950027e-10, 'cc/g/permille')
    assert calc_dCeq_dS('He', 5, 30, 0.98, dCeq_dS_unit='cc/g/permille', ret_quant=True) == Q(-2.288808241950027e-10, 'cc/g/permille')
    assert calc_dCeq_dS('He', 5, 30, 0.98, dCeq_dS_unit='g/mol/permille', ret_quant=True) == Q(-7.359713077615333e-13, 'g/mol/permille')
    assert calc_dCeq_dS('He', 5, 30, 0.98, dCeq_dS_unit='mol/m^3/permille', ret_quant=True) == Q(-9.034427609203887e-09, 'mol/m^3/permille')

    assert all(calc_dCeq_dS(['He', 'Ne'], 5, 30, 0.98) == np.array([-2.288808241950027e-10, -1.0496700267720907e-09]))
    assert all(calc_dCeq_dS(['He', 'Ne'], 5, 30, 0.98, dCeq_dS_unit='mol/m^3/permille') == np.array([-9.034427609203887e-09, -4.17786725313511e-08]))
    assert all(calc_dCeq_dS(['He', 'Ne'], 5, 30, 0.98, ret_quant=True) == Q([-2.288808241950027e-10, -1.0496700267720907e-09], 'cc/g/permille'))
    assert all(calc_dCeq_dS(['He', 'Ne'], 5, 30, 0.98, dCeq_dS_unit='mol/m^3/permille', ret_quant=True) == Q([-9.034427609203887e-09, -4.17786725313511e-08], 'mol/m^3/permille'))

def test_calc_dCeq_dS_all_quants_default_units():
    assert calc_dCeq_dS('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm')) == -2.288808241950027e-10# <- this will likely fail in future due to changing the default value of ret_quant; be sure to update appropriately
    assert calc_dCeq_dS('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), dCeq_dS_unit='cc/g/permille') == -2.288808241950027e-10# <- "
    assert calc_dCeq_dS('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), dCeq_dS_unit='g/mol/permille') == -7.359713077615333e-13 # <- "
    assert calc_dCeq_dS('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), dCeq_dS_unit='mol/m^3/permille') == -9.034427609203887e-09 # <- "

    assert calc_dCeq_dS('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), ret_quant=True) == Q(-2.288808241950027e-10, 'cc/g/permille')
    assert calc_dCeq_dS('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), dCeq_dS_unit='cc/g/permille', ret_quant=True) == Q(-2.288808241950027e-10, 'cc/g/permille')
    assert calc_dCeq_dS('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), dCeq_dS_unit='g/mol/permille', ret_quant=True) == Q(-7.359713077615333e-13, 'g/mol/permille')
    assert calc_dCeq_dS('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), dCeq_dS_unit='mol/m^3/permille', ret_quant=True) == Q(-9.034427609203887e-09, 'mol/m^3/permille')

    assert all(calc_dCeq_dS(['He', 'Ne'], Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm')) == np.array([-2.288808241950027e-10, -1.0496700267720907e-09]))
    assert all(calc_dCeq_dS(['He', 'Ne'], Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), dCeq_dS_unit='mol/m^3/permille') == np.array([-9.034427609203887e-09, -4.17786725313511e-08]))
    assert all(calc_dCeq_dS(['He', 'Ne'], Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), ret_quant=True) == Q([-2.288808241950027e-10, -1.0496700267720907e-09], 'cc/g/permille'))
    assert all(calc_dCeq_dS(['He', 'Ne'], Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), dCeq_dS_unit='mol/m^3/permille', ret_quant=True) == Q([-9.034427609203887e-09, -4.17786725313511e-08], 'mol/m^3/permille'))

def test_calc_dCeq_dS_all_quants_custom_units():
    assert calc_dCeq_dS('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg')) == -2.288808241950027e-10# <- this will likely fail in future due to changing the default value of ret_quant; be sure to update appropriately
    assert calc_dCeq_dS('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), dCeq_dS_unit='cc/g/permille') == -2.288808241950027e-10# <- "
    assert calc_dCeq_dS('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), dCeq_dS_unit='g/mol/permille') == -7.359713077615333e-13 # <- "
    assert calc_dCeq_dS('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), dCeq_dS_unit='mol/m^3/permille') == -9.034427609203887e-09 # <- "

    assert calc_dCeq_dS('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), ret_quant=True) == Q(-2.288808241950027e-10, 'cc/g/permille')
    assert calc_dCeq_dS('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), dCeq_dS_unit='cc/g/permille', ret_quant=True) == Q(-2.288808241950027e-10, 'cc/g/permille')
    assert calc_dCeq_dS('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), dCeq_dS_unit='g/mol/permille', ret_quant=True) == Q(-7.359713077615333e-13, 'g/mol/permille')
    assert calc_dCeq_dS('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), dCeq_dS_unit='mol/m^3/permille', ret_quant=True) == Q(-9.034427609203887e-09, 'mol/m^3/permille')

    assert all(calc_dCeq_dS(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg')) == np.array([-2.288808241950027e-10, -1.0496700267720907e-09]))
    assert all(calc_dCeq_dS(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), dCeq_dS_unit='mol/m^3/permille') == np.array([-9.034427609203887e-09, -4.17786725313511e-08]))
    assert all(calc_dCeq_dS(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), ret_quant=True) == Q([-2.288808241950027e-10, -1.0496700267720907e-09], 'cc/g/permille'))
    assert all(calc_dCeq_dS(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), dCeq_dS_unit='mol/m^3/permille', ret_quant=True) == Q([-9.034427609203887e-09, -4.17786725313511e-08], 'mol/m^3/permille'))

def test_calc_dCeq_dS_mixed():
    assert calc_dCeq_dS('He', 5, Q(3, 'percent'), Q(744.799893891099, 'mmHg')) == -2.288808241950027e-10# <- this will likely fail in future due to changing the default value of ret_quant; be sure to update appropriately
    assert calc_dCeq_dS('He', 5, Q(3, 'percent'), Q(744.799893891099, 'mmHg'), dCeq_dS_unit='cc/g/permille') == -2.288808241950027e-10# <- "
    assert calc_dCeq_dS('He', 5, Q(3, 'percent'), Q(744.799893891099, 'mmHg'), dCeq_dS_unit='g/mol/permille') == -7.359713077615333e-13 # <- "
    assert calc_dCeq_dS('He', 5, Q(3, 'percent'), Q(744.799893891099, 'mmHg'), dCeq_dS_unit='mol/m^3/permille') == -9.034427609203887e-09 # <- "

    assert calc_dCeq_dS('He', Q(278.15, 'K'), 30, Q(744.799893891099, 'mmHg'), ret_quant=True) == Q(-2.288808241950027e-10, 'cc/g/permille')
    assert calc_dCeq_dS('He', Q(278.15, 'K'), 30, Q(744.799893891099, 'mmHg'), dCeq_dS_unit='cc/g/permille', ret_quant=True) == Q(-2.288808241950027e-10, 'cc/g/permille')
    assert calc_dCeq_dS('He', Q(278.15, 'K'), 30, Q(744.799893891099, 'mmHg'), dCeq_dS_unit='g/mol/permille', ret_quant=True) == Q(-7.359713077615333e-13, 'g/mol/permille')
    assert calc_dCeq_dS('He', Q(278.15, 'K'), 30, Q(744.799893891099, 'mmHg'), dCeq_dS_unit='mol/m^3/permille', ret_quant=True) == Q(-9.034427609203887e-09, 'mol/m^3/permille')

    assert all(calc_dCeq_dS(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), 0.98) == np.array([-2.288808241950027e-10, -1.0496700267720907e-09]))
    assert all(calc_dCeq_dS(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), 0.98, dCeq_dS_unit='mol/m^3/permille') == np.array([-9.034427609203887e-09, -4.17786725313511e-08]))
    assert all(calc_dCeq_dS(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), 0.98, ret_quant=True) == Q([-2.288808241950027e-10, -1.0496700267720907e-09], 'cc/g/permille'))
    assert all(calc_dCeq_dS(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), 0.98, dCeq_dS_unit='mol/m^3/permille', ret_quant=True) == Q([-9.034427609203887e-09, -4.17786725313511e-08], 'mol/m^3/permille'))


# p-derivatives

def test_calc_dCeq_dp_all_floats():
    assert calc_dCeq_dp('He', 5, 30, 0.98) == 4.122563370265567e-08# <- this will likely fail in future due to changing the default value of ret_quant; be sure to update appropriately
    assert calc_dCeq_dp('He', 5, 30, 0.98, dCeq_dp_unit='cc/g/atm') == 4.122563370265567e-08# <- "
    assert calc_dCeq_dp('He', 5, 30, 0.98, dCeq_dp_unit='g/mol/atm') == 1.3256192892590907e-10 # <- "
    assert calc_dCeq_dp('He', 5, 30, 0.98, dCeq_dp_unit='mol/m^3/atm') == 1.881900190458122e-06 # <- "

    assert calc_dCeq_dp('He', 5, 30, 0.98, ret_quant=True) == Q(4.122563370265567e-08, 'cc/g/atm')
    assert calc_dCeq_dp('He', 5, 30, 0.98, dCeq_dp_unit='cc/g/atm', ret_quant=True) == Q(4.122563370265567e-08, 'cc/g/atm')
    assert calc_dCeq_dp('He', 5, 30, 0.98, dCeq_dp_unit='g/mol/atm', ret_quant=True) == Q(1.3256192892590907e-10, 'g/mol/atm')
    assert calc_dCeq_dp('He', 5, 30, 0.98, dCeq_dp_unit='mol/m^3/atm', ret_quant=True) == Q(1.881900190458122e-06, 'mol/m^3/atm')

    assert all(calc_dCeq_dp(['He', 'Ne'], 5, 30, 0.98) == np.array([4.122563370265567e-08, 1.79032306556058e-07]))
    assert all(calc_dCeq_dp(['He', 'Ne'], 5, 30, 0.98, dCeq_dp_unit='mol/m^3/atm') == np.array([1.881900190458122e-06, 8.172972152905139e-06]))
    assert all(calc_dCeq_dp(['He', 'Ne'], 5, 30, 0.98, ret_quant=True) == Q([4.122563370265567e-08, 1.79032306556058e-07], 'cc/g/atm'))
    assert all(calc_dCeq_dp(['He', 'Ne'], 5, 30, 0.98, dCeq_dp_unit='mol/m^3/atm', ret_quant=True) == Q([1.881900190458122e-06, 8.172972152905139e-06], 'mol/m^3/atm'))

def test_calc_dCeq_dp_all_quants_default_units():
    assert calc_dCeq_dp('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm')) == 4.122563370265567e-08# <- this will likely fail in future due to changing the default value of ret_quant; be sure to update appropriately
    assert calc_dCeq_dp('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), dCeq_dp_unit='cc/g/atm') == 4.122563370265567e-08# <- "
    assert calc_dCeq_dp('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), dCeq_dp_unit='g/mol/atm') == 1.3256192892590907e-10 # <- "
    assert calc_dCeq_dp('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), dCeq_dp_unit='mol/m^3/atm') == 1.881900190458122e-06 # <- "

    assert calc_dCeq_dp('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), ret_quant=True) == Q(4.122563370265567e-08, 'cc/g/atm')
    assert calc_dCeq_dp('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), dCeq_dp_unit='cc/g/atm', ret_quant=True) == Q(4.122563370265567e-08, 'cc/g/atm')
    assert calc_dCeq_dp('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), dCeq_dp_unit='g/mol/atm', ret_quant=True) == Q(1.3256192892590907e-10, 'g/mol/atm')
    assert calc_dCeq_dp('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), dCeq_dp_unit='mol/m^3/atm', ret_quant=True) == Q(1.881900190458122e-06, 'mol/m^3/atm')

    assert all(calc_dCeq_dp(['He', 'Ne'], Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm')) == np.array([4.122563370265567e-08, 1.79032306556058e-07]))
    assert all(calc_dCeq_dp(['He', 'Ne'], Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), dCeq_dp_unit='mol/m^3/atm') == np.array([1.881900190458122e-06, 8.172972152905139e-06]))
    assert all(calc_dCeq_dp(['He', 'Ne'], Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), ret_quant=True) == Q([4.122563370265567e-08, 1.79032306556058e-07], 'cc/g/atm'))
    assert all(calc_dCeq_dp(['He', 'Ne'], Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), dCeq_dp_unit='mol/m^3/atm', ret_quant=True) == Q([1.881900190458122e-06, 8.172972152905139e-06], 'mol/m^3/atm'))

def test_calc_dCeq_dp_all_quants_custom_units():
    assert calc_dCeq_dp('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg')) == 4.122563370265567e-08# <- this will likely fail in future due to changing the default value of ret_quant; be sure to update appropriately
    assert calc_dCeq_dp('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), dCeq_dp_unit='cc/g/atm') == 4.122563370265567e-08# <- "
    assert calc_dCeq_dp('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), dCeq_dp_unit='g/mol/atm') == 1.3256192892590907e-10 # <- "
    assert calc_dCeq_dp('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), dCeq_dp_unit='mol/m^3/atm') == 1.881900190458122e-06 # <- "

    assert calc_dCeq_dp('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), ret_quant=True) == Q(4.122563370265567e-08, 'cc/g/atm')
    assert calc_dCeq_dp('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), dCeq_dp_unit='cc/g/atm', ret_quant=True) == Q(4.122563370265567e-08, 'cc/g/atm')
    assert calc_dCeq_dp('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), dCeq_dp_unit='g/mol/atm', ret_quant=True) == Q(1.3256192892590907e-10, 'g/mol/atm')
    assert calc_dCeq_dp('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), dCeq_dp_unit='mol/m^3/atm', ret_quant=True) == Q(1.881900190458122e-06, 'mol/m^3/atm')

    assert all(calc_dCeq_dp(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg')) == np.array([4.122563370265567e-08, 1.79032306556058e-07]))
    assert all(calc_dCeq_dp(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), dCeq_dp_unit='mol/m^3/atm') == np.array([1.881900190458122e-06, 8.172972152905139e-06]))
    assert all(calc_dCeq_dp(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), ret_quant=True) == Q([4.122563370265567e-08, 1.79032306556058e-07], 'cc/g/atm'))
    assert all(calc_dCeq_dp(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), dCeq_dp_unit='mol/m^3/atm', ret_quant=True) == Q([1.881900190458122e-06, 8.172972152905139e-06], 'mol/m^3/atm'))

def test_calc_dCeq_dp_mixed():
    assert calc_dCeq_dp('He', 5, Q(3, 'percent'), Q(744.799893891099, 'mmHg')) == 4.122563370265567e-08# <- this will likely fail in future due to changing the default value of ret_quant; be sure to update appropriately
    assert calc_dCeq_dp('He', 5, Q(3, 'percent'), Q(744.799893891099, 'mmHg'), dCeq_dp_unit='cc/g/atm') == 4.122563370265567e-08# <- "
    assert calc_dCeq_dp('He', 5, Q(3, 'percent'), Q(744.799893891099, 'mmHg'), dCeq_dp_unit='g/mol/atm') == 1.3256192892590907e-10 # <- "
    assert calc_dCeq_dp('He', 5, Q(3, 'percent'), Q(744.799893891099, 'mmHg'), dCeq_dp_unit='mol/m^3/atm') == 1.881900190458122e-06 # <- "

    assert calc_dCeq_dp('He', Q(278.15, 'K'), 30, Q(744.799893891099, 'mmHg'), ret_quant=True) == Q(4.122563370265567e-08, 'cc/g/atm')
    assert calc_dCeq_dp('He', Q(278.15, 'K'), 30, Q(744.799893891099, 'mmHg'), dCeq_dp_unit='cc/g/atm', ret_quant=True) == Q(4.122563370265567e-08, 'cc/g/atm')
    assert calc_dCeq_dp('He', Q(278.15, 'K'), 30, Q(744.799893891099, 'mmHg'), dCeq_dp_unit='g/mol/atm', ret_quant=True) == Q(1.3256192892590907e-10, 'g/mol/atm')
    assert calc_dCeq_dp('He', Q(278.15, 'K'), 30, Q(744.799893891099, 'mmHg'), dCeq_dp_unit='mol/m^3/atm', ret_quant=True) == Q(1.881900190458122e-06, 'mol/m^3/atm')

    assert all(calc_dCeq_dp(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), 0.98) == np.array([4.122563370265567e-08, 1.79032306556058e-07]))
    assert all(calc_dCeq_dp(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), 0.98, dCeq_dp_unit='mol/m^3/atm') == np.array([1.881900190458122e-06, 8.172972152905139e-06]))
    assert all(calc_dCeq_dp(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), 0.98, ret_quant=True) == Q([4.122563370265567e-08, 1.79032306556058e-07], 'cc/g/atm'))
    assert all(calc_dCeq_dp(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), 0.98, dCeq_dp_unit='mol/m^3/atm', ret_quant=True) == Q([1.881900190458122e-06, 8.172972152905139e-06], 'mol/m^3/atm'))
