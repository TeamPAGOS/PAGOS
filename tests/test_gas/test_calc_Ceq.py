# Tests calc_Ceq() from pagos.gas and its associated derivatives. Tests are not carried out for all
# possible gases, as in theory test_calc_Cstar should handle any discrepancies (up to errors in the
# abn() function, but test_getters.py should also handle most of those cases).

from pagos.gas import calc_Ceq, calc_dCeq_dT, calc_dCeq_dS, calc_dCeq_dp
from pagos import Q
import numpy as np
from pint.testing import assert_allclose

def test_calc_Ceq_all_floats():
    assert_allclose(calc_Ceq('He', 5, 30, 0.98, magnitude=True), 1.785720915716375e-09) # <- this will likely fail in future due to changing the default value of ret_quant; be sure to update appropriately
    assert_allclose(calc_Ceq('He', 5, 30, 0.98, units='ccSTP_g/g_w', magnitude=True), 4.004634568050064e-08) # <- "
    assert_allclose(calc_Ceq('He', 5, 30, 0.98, units='g_g/mol_w', magnitude=True), 1.287699024381265e-10) # <- "
    assert_allclose(calc_Ceq('He', 5, 30, 0.98, units='mol_g/m3_w', magnitude=True), 1.8280671221903182e-06) # <- "

    assert_allclose(calc_Ceq('He', 5, 30, 0.98), Q(1.785720915716375e-09, 'mol_g/kg_w'))
    assert_allclose(calc_Ceq('He', 5, 30, 0.98, units='ccSTP_g/g_w'), Q(4.004634568050064e-08, 'ccSTP_g/g_w'))
    assert_allclose(calc_Ceq('He', 5, 30, 0.98, units='g_g/mol_w'), Q(1.287699024381265e-10, 'g_g/mol_w'))
    assert_allclose(calc_Ceq('He', 5, 30, 0.98, units='mol_g/m3_w'), Q(1.8280671221903182e-06, 'mol_g/m3_w'))

    assert_allclose(calc_Ceq(['He', 'Ne'], 5, 30, 0.98, magnitude=True), np.array([1.785720915716375e-09, 7.75527171473283e-09]))
    assert_allclose(calc_Ceq(['He', 'Ne'], 5, 30, 0.98, units='mol_g/m3_w', magnitude=True), np.array([1.8280671221903182e-06, 7.939178580807624e-06]))
    assert_allclose(calc_Ceq(['He', 'Ne'], 5, 30, 0.98), Q([1.785720915716375e-09, 7.75527171473283e-09], 'mol_g/kg_w'))
    assert_allclose(calc_Ceq(['He', 'Ne'], 5, 30, 0.98, units='mol_g/m3_w'), Q([1.8280671221903182e-06, 7.939178580807624e-06], 'mol_g/m3_w'))

def test_calc_Ceq_all_quants_default_units():
    assert_allclose(calc_Ceq('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), magnitude=True), 1.785720915716375e-09) # <- this will likely fail in future due to changing the default value of ret_quant; be sure to update appropriately
    assert_allclose(calc_Ceq('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), units='ccSTP_g/g_w', magnitude=True), 4.004634568050064e-08) # <- "
    assert_allclose(calc_Ceq('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), units='g_g/mol_w', magnitude=True), 1.287699024381265e-10) # <- "
    assert_allclose(calc_Ceq('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), units='mol_g/m3_w', magnitude=True), 1.8280671221903182e-06) # <- "

    assert_allclose(calc_Ceq('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm')), Q(1.785720915716375e-09, 'mol_g/kg_w'))
    assert_allclose(calc_Ceq('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), units='ccSTP_g/g_w'), Q(4.004634568050064e-08, 'ccSTP_g/g_w'))
    assert_allclose(calc_Ceq('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), units='g_g/mol_w'), Q(1.287699024381265e-10, 'g_g/mol_w'))
    assert_allclose(calc_Ceq('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), units='mol_g/m3_w'), Q(1.8280671221903182e-06, 'mol_g/m3_w'))

    assert_allclose(calc_Ceq(['He', 'Ne'], Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), magnitude=True), np.array([1.785720915716375e-09, 7.75527171473283e-09]))
    assert_allclose(calc_Ceq(['He', 'Ne'], Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), units='mol_g/m3_w', magnitude=True), np.array([1.8280671221903182e-06, 7.939178580807624e-06]))
    assert_allclose(calc_Ceq(['He', 'Ne'], Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm')), Q([1.785720915716375e-09, 7.75527171473283e-09], 'mol_g/kg_w'))
    assert_allclose(calc_Ceq(['He', 'Ne'], Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), units='mol_g/m3_w'), Q([1.8280671221903182e-06, 7.939178580807624e-06], 'mol_g/m3_w'))

def test_calc_Ceq_all_quants_custom_units():
    assert_allclose(calc_Ceq('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), magnitude=True), 1.785720915716375e-09) # <- this will likely fail in future due to changing the default value of ret_quant; be sure to update appropriately
    assert_allclose(calc_Ceq('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), units='ccSTP_g/g_w', magnitude=True), 4.004634568050064e-08) # <- "
    assert_allclose(calc_Ceq('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), units='g_g/mol_w', magnitude=True), 1.287699024381265e-10) # <- "
    assert_allclose(calc_Ceq('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), units='mol_g/m3_w', magnitude=True), 1.8280671221903182e-06) # <- "

    assert_allclose(calc_Ceq('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg')), Q(1.785720915716375e-09, 'mol_g/kg_w'))
    assert_allclose(calc_Ceq('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), units='ccSTP_g/g_w'), Q(4.004634568050064e-08, 'ccSTP_g/g_w'))
    assert_allclose(calc_Ceq('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), units='g_g/mol_w'), Q(1.287699024381265e-10, 'g_g/mol_w'))
    assert_allclose(calc_Ceq('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), units='mol_g/m3_w'), Q(1.8280671221903182e-06, 'mol_g/m3_w'))

    assert_allclose(calc_Ceq(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), magnitude=True), np.array([1.785720915716375e-09, 7.75527171473283e-09]))
    assert_allclose(calc_Ceq(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), units='mol_g/m3_w', magnitude=True), np.array([1.8280671221903182e-06, 7.939178580807624e-06]))
    assert_allclose(calc_Ceq(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg')), Q([1.785720915716375e-09, 7.75527171473283e-09], 'mol_g/kg_w'))
    assert_allclose(calc_Ceq(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), units='mol_g/m3_w'), Q([1.8280671221903182e-06, 7.939178580807624e-06], 'mol_g/m3_w'))

def test_calc_Ceq_mixed():
    assert_allclose(calc_Ceq('He', 5, Q(3, 'percent'), Q(744.799893891099, 'mmHg'), magnitude=True), 1.785720915716375e-09) # <- this will likely fail in future due to changing the default value of ret_quant; be sure to update appropriately
    assert_allclose(calc_Ceq('He', 5, Q(3, 'percent'), Q(744.799893891099, 'mmHg'), units='ccSTP_g/g_w', magnitude=True), 4.004634568050064e-08) # <- "
    assert_allclose(calc_Ceq('He', 5, Q(3, 'percent'), Q(744.799893891099, 'mmHg'), units='g_g/mol_w', magnitude=True), 1.287699024381265e-10) # <- "
    assert_allclose(calc_Ceq('He', 5, Q(3, 'percent'), Q(744.799893891099, 'mmHg'), units='mol_g/m3_w', magnitude=True), 1.8280671221903182e-06) # <- "

    assert_allclose(calc_Ceq('He', Q(278.15, 'K'), 30, Q(744.799893891099, 'mmHg')), Q(1.785720915716375e-09, 'mol_g/kg_w'))
    assert_allclose(calc_Ceq('He', Q(278.15, 'K'), 30, Q(744.799893891099, 'mmHg'), units='ccSTP_g/g_w'), Q(4.004634568050064e-08, 'ccSTP_g/g_w'))
    assert_allclose(calc_Ceq('He', Q(278.15, 'K'), 30, Q(744.799893891099, 'mmHg'), units='g_g/mol_w'), Q(1.287699024381265e-10, 'g_g/mol_w'))
    assert_allclose(calc_Ceq('He', Q(278.15, 'K'), 30, Q(744.799893891099, 'mmHg'), units='mol_g/m3_w'), Q(1.8280671221903182e-06, 'mol_g/m3_w'))

    assert_allclose(calc_Ceq(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), 0.98, magnitude=True), np.array([1.785720915716375e-09, 7.75527171473283e-09]))
    assert_allclose(calc_Ceq(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), 0.98, units='mol_g/m3_w', magnitude=True), np.array([1.8280671221903182e-06, 7.939178580807624e-06]))
    assert_allclose(calc_Ceq(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), 0.98), Q([1.785720915716375e-09, 7.75527171473283e-09], 'mol_g/kg_w'))
    assert_allclose(calc_Ceq(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), 0.98, units='mol_g/m3_w'), Q([1.8280671221903182e-06, 7.939178580807624e-06], 'mol_g/m3_w'))


# T-derivatives

def test_calc_dCeq_dT_all_floats():
    assert_allclose(calc_dCeq_dT('He', 5, 30, 0.98, magnitude=True), -7.44637143581229e-12) # <- this will likely fail in future due to changing the default value of ret_quant; be sure to update appropriately
    assert_allclose(calc_dCeq_dT('He', 5, 30, 0.98, units='ccSTP_g/g_w/K', magnitude=True), -1.6699136016129173e-10) # <- "
    assert_allclose(calc_dCeq_dT('He', 5, 30, 0.98, units='g_g/mol_w/K', magnitude=True), -5.369643794102802e-13) # <- "
    assert_allclose(calc_dCeq_dT('He', 5, 30, 0.98, units='mol_g/m3_w/K', magnitude=True), -7.807765868185713e-09) # <- "

    assert_allclose(calc_dCeq_dT('He', 5, 30, 0.98), Q(-7.44637143581229e-12, 'mol_g/kg_w/K'))
    assert_allclose(calc_dCeq_dT('He', 5, 30, 0.98, units='ccSTP_g/g_w/K'), Q(-1.6699136016129173e-10, 'ccSTP_g/g_w/K'))
    assert_allclose(calc_dCeq_dT('He', 5, 30, 0.98, units='g_g/mol_w/K'), Q(-5.369643794102802e-13, 'g_g/mol_w/K'))
    assert_allclose(calc_dCeq_dT('He', 5, 30, 0.98, units='mol_g/m3_w/K'), Q(-7.807765868185713e-09, 'mol_g/m3_w/K'))

    assert_allclose(calc_dCeq_dT(['He', 'Ne'], 5, 30, 0.98, magnitude=True), np.array([-7.44637143581229e-12, -7.309823143092348e-11]))
    assert_allclose(calc_dCeq_dT(['He', 'Ne'], 5, 30, 0.98, units='mol_g/m3_w/K', magnitude=True), np.array([-7.807765868185713e-09, -7.563429736712584e-08]))
    assert_allclose(calc_dCeq_dT(['He', 'Ne'], 5, 30, 0.98), Q([-7.44637143581229e-12, -7.309823143092348e-11], 'mol_g/kg_w/K'))
    assert_allclose(calc_dCeq_dT(['He', 'Ne'], 5, 30, 0.98, units='mol_g/m3_w/K'), Q([-7.807765868185713e-09, -7.563429736712584e-08], 'mol_g/m3_w/K'))

def test_calc_dCeq_dT_all_quants_default_units():
    assert_allclose(calc_dCeq_dT('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), magnitude=True), -7.44637143581229e-12) # <- this will likely fail in future due to changing the default value of ret_quant; be sure to update appropriately
    assert_allclose(calc_dCeq_dT('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), units='ccSTP_g/g_w/K', magnitude=True), -1.6699136016129173e-10) # <- "
    assert_allclose(calc_dCeq_dT('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), units='g_g/mol_w/K', magnitude=True), -5.369643794102802e-13) # <- "
    assert_allclose(calc_dCeq_dT('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), units='mol_g/m3_w/K', magnitude=True), -7.807765868185713e-09) # <- "

    assert_allclose(calc_dCeq_dT('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm')), Q(-7.44637143581229e-12, 'mol_g/kg_w/K'))
    assert_allclose(calc_dCeq_dT('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), units='ccSTP_g/g_w/K'), Q(-1.6699136016129173e-10, 'ccSTP_g/g_w/K'))
    assert_allclose(calc_dCeq_dT('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), units='g_g/mol_w/K'), Q(-5.369643794102802e-13, 'g_g/mol_w/K'))
    assert_allclose(calc_dCeq_dT('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), units='mol_g/m3_w/K'), Q(-7.807765868185713e-09, 'mol_g/m3_w/K'))

    assert_allclose(calc_dCeq_dT(['He', 'Ne'], Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), magnitude=True), np.array([-7.44637143581229e-12, -7.309823143092348e-11]))
    assert_allclose(calc_dCeq_dT(['He', 'Ne'], Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), units='mol_g/m3_w/K', magnitude=True), np.array([-7.807765868185713e-09, -7.563429736712584e-08]))
    assert_allclose(calc_dCeq_dT(['He', 'Ne'], Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm')), Q([-7.44637143581229e-12, -7.309823143092348e-11], 'mol_g/kg_w/K'))
    assert_allclose(calc_dCeq_dT(['He', 'Ne'], Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), units='mol_g/m3_w/K'), Q([-7.807765868185713e-09, -7.563429736712584e-08], 'mol_g/m3_w/K'))

def test_calc_dCeq_dT_all_quants_custom_units():
    assert_allclose(calc_dCeq_dT('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), magnitude=True), -7.44637143581229e-12) # <- this will likely fail in future due to changing the default value of ret_quant; be sure to update appropriately
    assert_allclose(calc_dCeq_dT('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), units='ccSTP_g/g_w/K', magnitude=True), -1.6699136016129173e-10) # <- "
    assert_allclose(calc_dCeq_dT('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), units='g_g/mol_w/K', magnitude=True), -5.369643794102802e-13) # <- "
    assert_allclose(calc_dCeq_dT('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), units='mol_g/m3_w/K', magnitude=True), -7.807765868185713e-09) # <- "

    assert_allclose(calc_dCeq_dT('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg')), Q(-7.44637143581229e-12, 'mol_g/kg_w/K'))
    assert_allclose(calc_dCeq_dT('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), units='ccSTP_g/g_w/K'), Q(-1.6699136016129173e-10, 'ccSTP_g/g_w/K'))
    assert_allclose(calc_dCeq_dT('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), units='g_g/mol_w/K'), Q(-5.369643794102802e-13, 'g_g/mol_w/K'))
    assert_allclose(calc_dCeq_dT('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), units='mol_g/m3_w/K'), Q(-7.807765868185713e-09, 'mol_g/m3_w/K'))

    assert_allclose(calc_dCeq_dT(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), magnitude=True), np.array([-7.44637143581229e-12, -7.309823143092348e-11]))
    assert_allclose(calc_dCeq_dT(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), units='mol_g/m3_w/K', magnitude=True), np.array([-7.807765868185713e-09, -7.563429736712584e-08]))
    assert_allclose(calc_dCeq_dT(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg')), Q([-7.44637143581229e-12, -7.309823143092348e-11], 'mol_g/kg_w/K'))
    assert_allclose(calc_dCeq_dT(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), units='mol_g/m3_w/K'), Q([-7.807765868185713e-09, -7.563429736712584e-08], 'mol_g/m3_w/K'))

def test_calc_dCeq_dT_mixed():
    assert_allclose(calc_dCeq_dT('He', 5, Q(3, 'percent'), Q(744.799893891099, 'mmHg'), magnitude=True), -7.44637143581229e-12) # <- this will likely fail in future due to changing the default value of ret_quant; be sure to update appropriately
    assert_allclose(calc_dCeq_dT('He', 5, Q(3, 'percent'), Q(744.799893891099, 'mmHg'), units='ccSTP_g/g_w/K', magnitude=True), -1.6699136016129173e-10) # <- "
    assert_allclose(calc_dCeq_dT('He', 5, Q(3, 'percent'), Q(744.799893891099, 'mmHg'), units='g_g/mol_w/K', magnitude=True), -5.369643794102802e-13) # <- "
    assert_allclose(calc_dCeq_dT('He', 5, Q(3, 'percent'), Q(744.799893891099, 'mmHg'), units='mol_g/m3_w/K', magnitude=True), -7.807765868185713e-09) # <- "

    assert_allclose(calc_dCeq_dT('He', Q(278.15, 'K'), 30, Q(744.799893891099, 'mmHg')), Q(-7.44637143581229e-12, 'mol_g/kg_w/K'))
    assert_allclose(calc_dCeq_dT('He', Q(278.15, 'K'), 30, Q(744.799893891099, 'mmHg'), units='ccSTP_g/g_w/K'), Q(-1.6699136016129173e-10, 'ccSTP_g/g_w/K'))
    assert_allclose(calc_dCeq_dT('He', Q(278.15, 'K'), 30, Q(744.799893891099, 'mmHg'), units='g_g/mol_w/K'), Q(-5.369643794102802e-13, 'g_g/mol_w/K'))
    assert_allclose(calc_dCeq_dT('He', Q(278.15, 'K'), 30, Q(744.799893891099, 'mmHg'), units='mol_g/m3_w/K'), Q(-7.807765868185713e-09, 'mol_g/m3_w/K'))

    assert_allclose(calc_dCeq_dT(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), 0.98, magnitude=True), np.array([-7.44637143581229e-12, -7.309823143092348e-11]))
    assert_allclose(calc_dCeq_dT(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), 0.98, units='mol_g/m3_w/K', magnitude=True), np.array([-7.807765868185713e-09, -7.563429736712584e-08]))
    assert_allclose(calc_dCeq_dT(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), 0.98), Q([-7.44637143581229e-12, -7.309823143092348e-11], 'mol_g/kg_w/K'))
    assert_allclose(calc_dCeq_dT(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), 0.98, units='mol_g/m3_w/K'), Q([-7.807765868185713e-09, -7.563429736712584e-08], 'mol_g/m3_w/K'))


# S-derivatives

def test_calc_dCeq_dS_all_floats():
    assert_allclose(calc_dCeq_dS('He', 5, 30, 0.98, magnitude=True), -1.0206106650336174e-11) # <- this will likely fail in future due to changing the default value of ret_quant; be sure to update appropriately
    assert_allclose(calc_dCeq_dS('He', 5, 30, 0.98, units='ccSTP_g/g_w/permille', magnitude=True), -2.288808241950027e-10) # <- "
    assert_allclose(calc_dCeq_dS('He', 5, 30, 0.98, units='g_g/mol_w/permille', magnitude=True), -7.359713077615333e-13) # <- "
    assert_allclose(calc_dCeq_dS('He', 5, 30, 0.98, units='mol_g/m3_w/permille', magnitude=True), -9.034427609203887e-09) # <- "

    assert_allclose(calc_dCeq_dS('He', 5, 30, 0.98), Q(-1.0206106650336174e-11, 'mol_g/kg_w/permille'))
    assert_allclose(calc_dCeq_dS('He', 5, 30, 0.98, units='ccSTP_g/g_w/permille'), Q(-2.288808241950027e-10, 'ccSTP_g/g_w/permille'))
    assert_allclose(calc_dCeq_dS('He', 5, 30, 0.98, units='g_g/mol_w/permille'), Q(-7.359713077615333e-13, 'g_g/mol_w/permille'))
    assert_allclose(calc_dCeq_dS('He', 5, 30, 0.98, units='mol_g/m3_w/permille'), Q(-9.034427609203887e-09, 'mol_g/m3_w/permille'))

    assert_allclose(calc_dCeq_dS(['He', 'Ne'], 5, 30, 0.98, magnitude=True), np.array([-1.0206106650336174e-11, -4.6808298637798766e-11]))
    assert_allclose(calc_dCeq_dS(['He', 'Ne'], 5, 30, 0.98, units='mol_g/m3_w/permille', magnitude=True), np.array([-9.034427609203887e-09, -4.17786725313511e-08]))
    assert_allclose(calc_dCeq_dS(['He', 'Ne'], 5, 30, 0.98), Q([-1.0206106650336174e-11, -4.6808298637798766e-11], 'mol_g/kg_w/permille'))
    assert_allclose(calc_dCeq_dS(['He', 'Ne'], 5, 30, 0.98, units='mol_g/m3_w/permille'), Q([-9.034427609203887e-09, -4.17786725313511e-08], 'mol_g/m3_w/permille'))

def test_calc_dCeq_dS_all_quants_default_units():
    assert_allclose(calc_dCeq_dS('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), magnitude=True), -1.0206106650336174e-11) # <- this will likely fail in future due to changing the default value of ret_quant; be sure to update appropriately
    assert_allclose(calc_dCeq_dS('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), units='ccSTP_g/g_w/permille', magnitude=True), -2.288808241950027e-10) # <- "
    assert_allclose(calc_dCeq_dS('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), units='g_g/mol_w/permille', magnitude=True), -7.359713077615333e-13) # <- "
    assert_allclose(calc_dCeq_dS('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), units='mol_g/m3_w/permille', magnitude=True), -9.034427609203887e-09) # <- "

    assert_allclose(calc_dCeq_dS('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm')), Q(-1.0206106650336174e-11, 'mol_g/kg_w/permille'))
    assert_allclose(calc_dCeq_dS('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), units='ccSTP_g/g_w/permille'), Q(-2.288808241950027e-10, 'ccSTP_g/g_w/permille'))
    assert_allclose(calc_dCeq_dS('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), units='g_g/mol_w/permille'), Q(-7.359713077615333e-13, 'g_g/mol_w/permille'))
    assert_allclose(calc_dCeq_dS('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), units='mol_g/m3_w/permille'), Q(-9.034427609203887e-09, 'mol_g/m3_w/permille'))

    assert_allclose(calc_dCeq_dS(['He', 'Ne'], Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), magnitude=True), np.array([-1.0206106650336174e-11, -4.6808298637798766e-11]))
    assert_allclose(calc_dCeq_dS(['He', 'Ne'], Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), units='mol_g/m3_w/permille', magnitude=True), np.array([-9.034427609203887e-09, -4.17786725313511e-08]))
    assert_allclose(calc_dCeq_dS(['He', 'Ne'], Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm')), Q([-1.0206106650336174e-11, -4.6808298637798766e-11], 'mol_g/kg_w/permille'))
    assert_allclose(calc_dCeq_dS(['He', 'Ne'], Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), units='mol_g/m3_w/permille'), Q([-9.034427609203887e-09, -4.17786725313511e-08], 'mol_g/m3_w/permille'))

def test_calc_dCeq_dS_all_quants_custom_units():
    assert_allclose(calc_dCeq_dS('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), magnitude=True), -1.0206106650336174e-11) # <- this will likely fail in future due to changing the default value of ret_quant; be sure to update appropriately
    assert_allclose(calc_dCeq_dS('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), units='ccSTP_g/g_w/permille', magnitude=True), -2.288808241950027e-10) # <- "
    assert_allclose(calc_dCeq_dS('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), units='g_g/mol_w/permille', magnitude=True), -7.359713077615333e-13) # <- "
    assert_allclose(calc_dCeq_dS('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), units='mol_g/m3_w/permille', magnitude=True), -9.034427609203887e-09) # <- "

    assert_allclose(calc_dCeq_dS('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg')), Q(-1.0206106650336174e-11, 'mol_g/kg_w/permille'))
    assert_allclose(calc_dCeq_dS('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), units='ccSTP_g/g_w/permille'), Q(-2.288808241950027e-10, 'ccSTP_g/g_w/permille'))
    assert_allclose(calc_dCeq_dS('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), units='g_g/mol_w/permille'), Q(-7.359713077615333e-13, 'g_g/mol_w/permille'))
    assert_allclose(calc_dCeq_dS('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), units='mol_g/m3_w/permille'), Q(-9.034427609203887e-09, 'mol_g/m3_w/permille'))

    assert_allclose(calc_dCeq_dS(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), magnitude=True), np.array([-1.0206106650336174e-11, -4.6808298637798766e-11]))
    assert_allclose(calc_dCeq_dS(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), units='mol_g/m3_w/permille', magnitude=True), np.array([-9.034427609203887e-09, -4.17786725313511e-08]))
    assert_allclose(calc_dCeq_dS(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg')), Q([-1.0206106650336174e-11, -4.6808298637798766e-11], 'mol_g/kg_w/permille'))
    assert_allclose(calc_dCeq_dS(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), units='mol_g/m3_w/permille'), Q([-9.034427609203887e-09, -4.17786725313511e-08], 'mol_g/m3_w/permille'))

def test_calc_dCeq_dS_mixed():
    assert_allclose(calc_dCeq_dS('He', 5, Q(3, 'percent'), Q(744.799893891099, 'mmHg'), magnitude=True), -1.0206106650336174e-11) # <- this will likely fail in future due to changing the default value of ret_quant; be sure to update appropriately
    assert_allclose(calc_dCeq_dS('He', 5, Q(3, 'percent'), Q(744.799893891099, 'mmHg'), units='ccSTP_g/g_w/permille', magnitude=True), -2.288808241950027e-10) # <- "
    assert_allclose(calc_dCeq_dS('He', 5, Q(3, 'percent'), Q(744.799893891099, 'mmHg'), units='g_g/mol_w/permille', magnitude=True), -7.359713077615333e-13) # <- "
    assert_allclose(calc_dCeq_dS('He', 5, Q(3, 'percent'), Q(744.799893891099, 'mmHg'), units='mol_g/m3_w/permille', magnitude=True), -9.034427609203887e-09) # <- "

    assert_allclose(calc_dCeq_dS('He', Q(278.15, 'K'), 30, Q(744.799893891099, 'mmHg')), Q(-1.0206106650336174e-11, 'mol_g/kg_w/permille'))
    assert_allclose(calc_dCeq_dS('He', Q(278.15, 'K'), 30, Q(744.799893891099, 'mmHg'), units='ccSTP_g/g_w/permille'), Q(-2.288808241950027e-10, 'ccSTP_g/g_w/permille'))
    assert_allclose(calc_dCeq_dS('He', Q(278.15, 'K'), 30, Q(744.799893891099, 'mmHg'), units='g_g/mol_w/permille'), Q(-7.359713077615333e-13, 'g_g/mol_w/permille'))
    assert_allclose(calc_dCeq_dS('He', Q(278.15, 'K'), 30, Q(744.799893891099, 'mmHg'), units='mol_g/m3_w/permille'), Q(-9.034427609203887e-09, 'mol_g/m3_w/permille'))

    assert_allclose(calc_dCeq_dS(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), 0.98, magnitude=True), np.array([-1.0206106650336174e-11, -4.6808298637798766e-11]))
    assert_allclose(calc_dCeq_dS(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), 0.98, units='mol_g/m3_w/permille', magnitude=True), np.array([-9.034427609203887e-09, -4.17786725313511e-08]))
    assert_allclose(calc_dCeq_dS(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), 0.98), Q([-1.0206106650336174e-11, -4.6808298637798766e-11], 'mol_g/kg_w/permille'))
    assert_allclose(calc_dCeq_dS(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), 0.98, units='mol_g/m3_w/permille'), Q([-9.034427609203887e-09, -4.17786725313511e-08], 'mol_g/m3_w/permille'))


# p-derivatives

def test_calc_dCeq_dp_all_floats():
    assert_allclose(calc_dCeq_dp('He', 5, 30, 0.98, magnitude=True), 1.8383069694756181e-09) # <- this will likely fail in future due to changing the default value of ret_quant; be sure to update appropriately
    assert_allclose(calc_dCeq_dp('He', 5, 30, 0.98, units='ccSTP_g/g_w/atm', magnitude=True), 4.122563370265567e-08) # <- "
    assert_allclose(calc_dCeq_dp('He', 5, 30, 0.98, units='g_g/mol_w/atm', magnitude=True), 1.3256192892590907e-10) # <- "
    assert_allclose(calc_dCeq_dp('He', 5, 30, 0.98, units='mol_g/m3_w/atm', magnitude=True), 1.881900190458122e-06) # <- "

    assert_allclose(calc_dCeq_dp('He', 5, 30, 0.98), Q(1.8383069694756181e-09, 'mol_g/kg_w/atm'))
    assert_allclose(calc_dCeq_dp('He', 5, 30, 0.98, units='ccSTP_g/g_w/atm'), Q(4.122563370265567e-08, 'ccSTP_g/g_w/atm'))
    assert_allclose(calc_dCeq_dp('He', 5, 30, 0.98, units='g_g/mol_w/atm'), Q(1.3256192892590907e-10, 'g_g/mol_w/atm'))
    assert_allclose(calc_dCeq_dp('He', 5, 30, 0.98, units='mol_g/m3_w/atm'), Q(1.881900190458122e-06, 'mol_g/m3_w/atm'))

    assert_allclose(calc_dCeq_dp(['He', 'Ne'], 5, 30, 0.98, magnitude=True), np.array([1.8383069694756181e-09, 7.983649582583963e-09]))
    assert_allclose(calc_dCeq_dp(['He', 'Ne'], 5, 30, 0.98, units='mol_g/m3_w/atm', magnitude=True), np.array([1.881900190458122e-06, 8.172972152905139e-06]))
    assert_allclose(calc_dCeq_dp(['He', 'Ne'], 5, 30, 0.98), Q([1.8383069694756181e-09, 7.983649582583963e-09], 'mol_g/kg_w/atm'))
    assert_allclose(calc_dCeq_dp(['He', 'Ne'], 5, 30, 0.98, units='mol_g/m3_w/atm'), Q([1.881900190458122e-06, 8.172972152905139e-06], 'mol_g/m3_w/atm'))

def test_calc_dCeq_dp_all_quants_default_units():
    assert_allclose(calc_dCeq_dp('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), magnitude=True), 1.8383069694756181e-09) # <- this will likely fail in future due to changing the default value of ret_quant; be sure to update appropriately
    assert_allclose(calc_dCeq_dp('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), units='ccSTP_g/g_w/atm', magnitude=True), 4.122563370265567e-08) # <- "
    assert_allclose(calc_dCeq_dp('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), units='g_g/mol_w/atm', magnitude=True), 1.3256192892590907e-10) # <- "
    assert_allclose(calc_dCeq_dp('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), units='mol_g/m3_w/atm', magnitude=True), 1.881900190458122e-06) # <- "

    assert_allclose(calc_dCeq_dp('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm')), Q(1.8383069694756181e-09, 'mol_g/kg_w/atm'))
    assert_allclose(calc_dCeq_dp('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), units='ccSTP_g/g_w/atm'), Q(4.122563370265567e-08, 'ccSTP_g/g_w/atm'))
    assert_allclose(calc_dCeq_dp('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), units='g_g/mol_w/atm'), Q(1.3256192892590907e-10, 'g_g/mol_w/atm'))
    assert_allclose(calc_dCeq_dp('He', Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), units='mol_g/m3_w/atm'), Q(1.881900190458122e-06, 'mol_g/m3_w/atm'))

    assert_allclose(calc_dCeq_dp(['He', 'Ne'], Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), magnitude=True), np.array([1.8383069694756181e-09, 7.983649582583963e-09]))
    assert_allclose(calc_dCeq_dp(['He', 'Ne'], Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), units='mol_g/m3_w/atm', magnitude=True), np.array([1.881900190458122e-06, 8.172972152905139e-06]))
    assert_allclose(calc_dCeq_dp(['He', 'Ne'], Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm')), Q([1.8383069694756181e-09, 7.983649582583963e-09], 'mol_g/kg_w/atm'))
    assert_allclose(calc_dCeq_dp(['He', 'Ne'], Q(5, 'degC'), Q(30, 'permille'), Q(0.98, 'atm'), units='mol_g/m3_w/atm'), Q([1.881900190458122e-06, 8.172972152905139e-06], 'mol_g/m3_w/atm'))

def test_calc_dCeq_dp_all_quants_custom_units():
    assert_allclose(calc_dCeq_dp('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), magnitude=True), 1.8383069694756181e-09) # <- this will likely fail in future due to changing the default value of ret_quant; be sure to update appropriately
    assert_allclose(calc_dCeq_dp('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), units='ccSTP_g/g_w/atm', magnitude=True), 4.122563370265567e-08) # <- "
    assert_allclose(calc_dCeq_dp('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), units='g_g/mol_w/atm', magnitude=True), 1.3256192892590907e-10) # <- "
    assert_allclose(calc_dCeq_dp('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), units='mol_g/m3_w/atm', magnitude=True), 1.881900190458122e-06) # <- "

    assert_allclose(calc_dCeq_dp('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg')), Q(1.8383069694756181e-09, 'mol_g/kg_w/atm'))
    assert_allclose(calc_dCeq_dp('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), units='ccSTP_g/g_w/atm'), Q(4.122563370265567e-08, 'ccSTP_g/g_w/atm'))
    assert_allclose(calc_dCeq_dp('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), units='g_g/mol_w/atm'), Q(1.3256192892590907e-10, 'g_g/mol_w/atm'))
    assert_allclose(calc_dCeq_dp('He', Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), units='mol_g/m3_w/atm'), Q(1.881900190458122e-06, 'mol_g/m3_w/atm'))

    assert_allclose(calc_dCeq_dp(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), magnitude=True), np.array([1.8383069694756181e-09, 7.983649582583963e-09]))
    assert_allclose(calc_dCeq_dp(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), units='mol_g/m3_w/atm', magnitude=True), np.array([1.881900190458122e-06, 8.172972152905139e-06]))
    assert_allclose(calc_dCeq_dp(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg')), Q([1.8383069694756181e-09, 7.983649582583963e-09], 'mol_g/kg_w/atm'))
    assert_allclose(calc_dCeq_dp(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), Q(744.799893891099, 'mmHg'), units='mol_g/m3_w/atm'), Q([1.881900190458122e-06, 8.172972152905139e-06], 'mol_g/m3_w/atm'))

def test_calc_dCeq_dp_mixed():
    assert_allclose(calc_dCeq_dp('He', 5, Q(3, 'percent'), Q(744.799893891099, 'mmHg'), magnitude=True), 1.8383069694756181e-09) # <- this will likely fail in future due to changing the default value of ret_quant; be sure to update appropriately
    assert_allclose(calc_dCeq_dp('He', 5, Q(3, 'percent'), Q(744.799893891099, 'mmHg'), units='ccSTP_g/g_w/atm', magnitude=True), 4.122563370265567e-08) # <- "
    assert_allclose(calc_dCeq_dp('He', 5, Q(3, 'percent'), Q(744.799893891099, 'mmHg'), units='g_g/mol_w/atm', magnitude=True), 1.3256192892590907e-10) # <- "
    assert_allclose(calc_dCeq_dp('He', 5, Q(3, 'percent'), Q(744.799893891099, 'mmHg'), units='mol_g/m3_w/atm', magnitude=True), 1.881900190458122e-06) # <- "

    assert_allclose(calc_dCeq_dp('He', Q(278.15, 'K'), 30, Q(744.799893891099, 'mmHg')), Q(1.8383069694756181e-09, 'mol_g/kg_w/atm'))
    assert_allclose(calc_dCeq_dp('He', Q(278.15, 'K'), 30, Q(744.799893891099, 'mmHg'), units='ccSTP_g/g_w/atm'), Q(4.122563370265567e-08, 'ccSTP_g/g_w/atm'))
    assert_allclose(calc_dCeq_dp('He', Q(278.15, 'K'), 30, Q(744.799893891099, 'mmHg'), units='g_g/mol_w/atm'), Q(1.3256192892590907e-10, 'g_g/mol_w/atm'))
    assert_allclose(calc_dCeq_dp('He', Q(278.15, 'K'), 30, Q(744.799893891099, 'mmHg'), units='mol_g/m3_w/atm'), Q(1.881900190458122e-06, 'mol_g/m3_w/atm'))

    assert_allclose(calc_dCeq_dp(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), 0.98, magnitude=True), np.array([1.8383069694756181e-09, 7.983649582583963e-09]))
    assert_allclose(calc_dCeq_dp(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), 0.98, units='mol_g/m3_w/atm', magnitude=True), np.array([1.881900190458122e-06, 8.172972152905139e-06]))
    assert_allclose(calc_dCeq_dp(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), 0.98), Q([1.8383069694756181e-09, 7.983649582583963e-09], 'mol_g/kg_w/atm'))
    assert_allclose(calc_dCeq_dp(['He', 'Ne'], Q(278.15, 'K'), Q(3, 'percent'), 0.98, units='mol_g/m3_w/atm'), Q([1.881900190458122e-06, 8.172972152905139e-06], 'mol_g/m3_w/atm'))
