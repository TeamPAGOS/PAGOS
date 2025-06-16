# Tests the possibly_iterable functionality from pagos.core.

# WIP
"""import sys
sys.path.insert(0, 'C:/Users/scopi/source/repos/PAGOS/PAGOS/src')"""
from pytest import raises
from pagos import calc_Ceq, GasExchangeModel
import numpy as np

"""print(calc_Ceq(['He', 'Ne', 'Ar'], T=10, S=20, p=1))
print(calc_Ceq('He', [10, 20, 30], S=20, p=1, possit=1))
print(calc_Ceq('He', T=[10, 20, 30], S=20, p=1, possit='T'))
print(calc_Ceq(gas='He', T=[10, 20, 30], S=20, p=1, possit='T'))
print(calc_Ceq(['He', 'Ne', 'Ar'], T=10, S=20, p=1, possit=0))
print(calc_Ceq(gas=['He', 'Ne', 'Ar'], T=10, S=20, p=1, possit='gas'))
print(calc_Ceq(gas='Ne', T=10, S=[20, 30], p=1, possit='S'))
print(calc_Ceq('Ne', 10, [20, 30], 1, possit=2))
print(calc_Ceq(gas=['He', 'Ne', 'Ar'], T=10, S=20, p=1, possit='gas'))
print(calc_Ceq(['He', 'Ne', 'Ar'], [20, 30, 10], S=20, p=1, possit=(0, 1)))
print(calc_Ceq(['He', 'Ne', 'Ar'], [20, 30, 10], [20, 30, 40], p=1, possit=(0, 1, 2)))
print(calc_Ceq(['He', 'Ne', 'Ar'], 10, [20, 30, 40], p=1, possit=(0, 2)))
print(calc_Ceq(gas=['He', 'Ne', 'Ar'], T=10, S=[20, 30, 40], p=1, possit=('gas', 'S')))
print(calc_Ceq(gas=['He', 'Ne', 'Ar'], T=10, S=20, p=1))"""


def test_calc_Ceq_possibly_iterable():
    np.testing.assert_allclose(calc_Ceq(['He', 'Ne', 'Ar'], 10, 20, 1), np.array([4.23785265e-08, 1.80257361e-07, 3.38277798e-04]))

# _possibly_iterable in pagos.core manipulates the global variable _ENABLE_POSSIT. If an exception
# occurs while the program is inside a function decorated with @_possibly_iterable, then correcting
# the offending error and running the program again could possibly run with a saved state of
# _ENABLE_POSSIT, which can lead to a scary TypeError with the message "<function> got an
# unexpected keyword argument 'disablenext'". THe following test passing should show that this
# error is prevented.
def test_possit_reset_after_error_caught():
    def will_throw_error(gas, T, S, p):
        raise ValueError("I am a ValueError")
    WTE_GEM = GasExchangeModel(will_throw_error, ('degC', 'permille', 'atm'), None)
    with raises(Exception):
        WTE_GEM.run('Ne', 10, 15, 1)
    
    def will_not_throw_error(gas, T, S, p):
        return calc_Ceq(gas, T, S, p)
    WNTE_GEM = GasExchangeModel(will_not_throw_error, ('degC', 'permille', 'atm'), None)
    assert(WNTE_GEM.run('Ne', 10, 15, 1))