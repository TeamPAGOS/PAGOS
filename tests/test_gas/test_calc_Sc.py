# Tests calc_Sc() from pagos.gas.

from pagos.gas import calc_Sc
from pagos import Q

# method == 'auto'
def test_Sc_all_floats_method_is_auto():
    assert calc_Sc('He', 5, 30, method='auto') == Q(314.5266945137353, 'dimensionless'), "He Schmidt number at (5 degC, 30 permille) with method=='auto' assertion failed."
    assert (calc_Sc(['He', 'Ar'], 5, 30, method='auto') == Q([314.5266945137353, 995.1351744225677], 'dimensionless')).all(), "Schmidt number of multiple gases at (5 degC, 30 permille) with method=='auto' assertion failed."

def test_Sc_all_quants_default_units_method_is_auto():
    assert calc_Sc('He', Q(5, 'degC'), Q(30, 'permille'), method='auto') == Q(314.5266945137353, 'dimensionless'), "He Schmidt number with quantities (5 degC, 30 permille) and method=='auto' assertion failed."
    assert (calc_Sc(['He', 'Ar'], Q(5, 'degC'), Q(30, 'permille'), method='auto') == Q([314.5266945137353, 995.1351744225677], 'dimensionless')).all(), "Schmidt number of multiple gases with quantities (5 degC, 30 permille) and method=='auto' assertion failed."

def test_Sc_all_quants_custom_units_method_is_auto():
    assert calc_Sc('He', Q(278.15, 'K'), Q(3, 'percent'), method='auto') == Q(314.5266945137353, 'dimensionless'), "He Schmidt number with quantities (278.15 K, 3 %) and method=='auto' assertion failed."
    assert (calc_Sc(['He', 'Ar'], Q(278.15, 'K'), Q(3, 'percent'), method='auto') == Q([314.5266945137353, 995.1351744225677], 'dimensionless')).all(), "Schmidt number of multiple gases with quantities (278.15 K, 3 %) and method=='auto' assertion failed."

def test_Sc_mixed_method_is_auto():
    assert calc_Sc('He', Q(278.15, 'K'), 30, method='auto') == Q(314.5266945137353, 'dimensionless'), "He Schmidt number with (quantity 278.15 K, 30 permille) and method=='auto' assertion failed."
    assert (calc_Sc(['He', 'Ar'], 5, Q(3, 'percent'), method='auto') == Q([314.5266945137353, 995.1351744225677], 'dimensionless')).all(), "Schmidt number of multiple gases with (quantity 5 degc, quantity 3 %) and method=='auto' assertion failed."

# method == 'W92'
def test_Sc_all_floats_method_is_W92():
    assert calc_Sc('He', 5, 30, method='W92') == Q(330.1201762383643, 'dimensionless'), "He Schmidt number at (5 degC, 30 permille) with method=='W92' assertion failed."
    assert (calc_Sc(['He', 'Ar'], 5, 30, method='W92') == Q([330.1201762383643, 1418.284137807513], 'dimensionless')).all(), "Schmidt number of multiple gases at (5 degC, 30 permille) with method=='W92' assertion failed."

def test_Sc_all_quants_default_units_method_is_W92():
    assert calc_Sc('He', Q(5, 'degC'), Q(30, 'permille'), method='W92') == Q(330.1201762383643, 'dimensionless'), "He Schmidt number with quantities (5 degC, 30 permille) and method=='W92' assertion failed."
    assert (calc_Sc(['He', 'Ar'], Q(5, 'degC'), Q(30, 'permille'), method='W92') == Q([330.1201762383643, 1418.284137807513], 'dimensionless')).all(), "Schmidt number of multiple gases with quantities (5 degC, 30 permille) and method=='W92' assertion failed."

def test_Sc_all_quants_custom_units_method_is_W92():
    assert calc_Sc('He', Q(278.15, 'K'), Q(3, 'percent'), method='W92') == Q(330.1201762383643, 'dimensionless'), "He Schmidt number with quantities (278.15 K, 3 %) and method=='W92' assertion failed."
    assert (calc_Sc(['He', 'Ar'], Q(278.15, 'K'), Q(3, 'percent'), method='W92') == Q([330.1201762383643, 1418.284137807513], 'dimensionless')).all(), "Schmidt number of multiple gases with quantities (278.15 K, 3 %) and method=='W92' assertion failed."

def test_Sc_mixed_method_is_W92():
    assert calc_Sc('He', Q(278.15, 'K'), 30, method='W92') == Q(330.1201762383643, 'dimensionless'), "He Schmidt number with (quantity 278.15 K, 30 permille) and method=='W92' assertion failed."
    assert (calc_Sc(['He', 'Ar'], 5, Q(3, 'percent'), method='W92') == Q([330.1201762383643, 1418.284137807513], 'dimensionless')).all(), "Schmidt number of multiple gases with (quantity 5 degc, quantity 3 %) and method=='W92' assertion failed."

# method == 'HE17'
def test_Sc_all_floats_method_is_HE17():
    assert calc_Sc('He', 5, 30, method='HE17') == Q(314.5266945137353, 'dimensionless'), "He Schmidt number at (5 degC, 30 permille) with method=='HE17' assertion failed."
    assert (calc_Sc(['He', 'Ar'], 5, 30, method='HE17') == Q([314.5266945137353, 995.1351744225677], 'dimensionless')).all(), "Schmidt number of multiple gases at (5 degC, 30 permille) with method=='HE17' assertion failed."

def test_Sc_all_quants_default_units_method_is_HE17():
    assert calc_Sc('He', Q(5, 'degC'), Q(30, 'permille'), method='HE17') == Q(314.5266945137353, 'dimensionless'), "He Schmidt number with quantities (5 degC, 30 permille) and method=='HE17' assertion failed."
    assert (calc_Sc(['He', 'Ar'], Q(5, 'degC'), Q(30, 'permille'), method='HE17') == Q([314.5266945137353, 995.1351744225677], 'dimensionless')).all(), "Schmidt number of multiple gases with quantities (5 degC, 30 permille) and method=='HE17' assertion failed."

def test_Sc_all_quants_custom_units_method_is_HE17():
    assert calc_Sc('He', Q(278.15, 'K'), Q(3, 'percent'), method='HE17') == Q(314.5266945137353, 'dimensionless'), "He Schmidt number with quantities (278.15 K, 3 %) and method=='HE17' assertion failed."
    assert (calc_Sc(['He', 'Ar'], Q(278.15, 'K'), Q(3, 'percent'), method='HE17') == Q([314.5266945137353, 995.1351744225677], 'dimensionless')).all(), "Schmidt number of multiple gases with quantities (278.15 K, 3 %) and method=='HE17' assertion failed."

def test_Sc_mixed_method_is_HE17():
    assert calc_Sc('He', Q(278.15, 'K'), 30, method='HE17') == Q(314.5266945137353, 'dimensionless'), "He Schmidt number with (quantity 278.15 K, 30 permille) and method=='HE17' assertion failed."
    assert (calc_Sc(['He', 'Ar'], 5, Q(3, 'percent'), method='HE17') == Q([314.5266945137353, 995.1351744225677], 'dimensionless')).all(), "Schmidt number of multiple gases with (quantity 5 degc, quantity 3 %) and method=='HE17' assertion failed."

