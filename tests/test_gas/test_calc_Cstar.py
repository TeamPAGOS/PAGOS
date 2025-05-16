# Tests calc_Cstar() from pagos.gas.

from pagos.gas import calc_Cstar

def test_Cstar():
    assert calc_Cstar('He', 5, 30) == 1.8224870551058874e-09
    assert calc_Cstar('N2', 5, 30) == 0.0005774155446125664
    assert calc_Cstar('CFC12', 5, 30) == 0.005164867129992845
    assert calc_Cstar('SF6', 5, 30) == 3.9941917162926535e-15
    # future: other tracers that use different functions for their C* calculation