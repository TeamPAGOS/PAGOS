# Tests calc_Cstar() from pagos.gas.

from pagos.gas import calc_Cstar

def test_Cstar():
    assert calc_Cstar('He', 5, 30) == 1.8224870551058874e-09
    assert calc_Cstar('N2', 5, 30) == 0.0005774155446125664
    assert calc_Cstar('CFC12', 5, 30) == 2.520455159436508e-12
    assert calc_Cstar('SF6', 5, 30) == 3.9941917162926535e-15

    # testing with different abundances
    assert calc_Cstar('CFC12', 5, 30, ab=4.5e-10) == 2.32419020849678e-12 # projected possible value for 2030
    assert calc_Cstar('SF6', 5, 30, ab=1.4e-11) == 4.862494263312796e-15   # projected possible value for 2030
    
    # future: other tracers that use different functions for their C* calculation
    