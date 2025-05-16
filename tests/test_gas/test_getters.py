# Tests the getter functions in gas.py.
from pagos.gas import jkc, wkc, erc, mv, mm, wwc, abn, blc, hec, ice
import numpy as np

def test_jkc():
    assert jkc('He') == {'A1':-178.1424, 'A2':217.5991, 'A3':140.7506, 'A4':-23.01954, 'B1':-0.038129, 'B2':0.019190, 'B3':-0.0026898, 'C1':-2.55157E-6}, "Helium Jenkins 2019 coefficients assertion failed"
    assert np.array_equal(jkc(['He', 'Ar']), np.array([{'A1':-178.1424, 'A2':217.5991, 'A3':140.7506, 'A4':-23.01954, 'B1':-0.038129, 'B2':0.019190, 'B3':-0.0026898, 'C1':-2.55157E-6},
                                                       {'A1':-227.4607, 'A2':305.4347, 'A3':180.5278, 'A4':-27.99450, 'B1':-0.066942, 'B2':0.037201, 'B3':-0.0056364, 'C1':-5.30325E-6}])
                         ), "Jenkins 2019 coefficients of multiple gases assertion failed."

def test_wkc():
    assert wkc('He') == {'A': 377.09, 'B': 19.154, 'C': 0.50137, 'D': 0.005669}, "Helium Wanninkhof 1992 coefficients assertion failed"
    assert np.array_equal(wkc(['He', 'Ar']), np.array([{'A': 377.09, 'B': 19.154, 'C': 0.50137, 'D': 0.005669},
                                                       {'A': 1759.7, 'B': 117.37, 'C': 3.6959, 'D': 0.046527}])
                         ), "Wannikhof 1992 coefficients of multiple gases assertion failed."

def test_erc():
    assert erc('He') == {'A': .00818, 'Ea': 11.70}, "Helium Eyring 1987 coefficients assertion failed"
    assert np.array_equal(erc(['He', 'Ar']), np.array([{'A': .00818, 'Ea': 11.70},
                                                       {'A': .02227, 'Ea': 16.68}])
                         ), "Eyring 1987 coefficients of multiple gases assertion failed."

def test_wwc():
    assert wwc('CFC11') == {'a1': -232.0411, 'a2': 322.5546, 'a3': 120.4956, 'a4': -1.39165, 'b1': -0.146531, 'b2': 0.093621, 'b3': -0.0160693}, "CFC11 Warner/Weiss 1985 coefficients assertion failed"
    assert np.array_equal(wwc(['CFC11', 'CFC12']), np.array([{'a1': -232.0411, 'a2': 322.5546, 'a3': 120.4956, 'a4': -1.39165, 'b1': -0.146531, 'b2': 0.093621, 'b3': -0.0160693},
                                                             {'a1': -220.2120, 'a2': 301.8695, 'a3': 114.8533, 'a4': -1.39165, 'b1': -0.147718, 'b2': 0.093175, 'b3': -0.0157340}])
                         ), "Warner/Weiss 1985 coefficients of multiple gases assertion failed."

def test_blc():
    assert blc('SF6') == {'a1': -82.1639, 'a2': 120.152, 'a3': 30.6372, 'b1': 0.0293201, 'b2': -0.0351974, 'b3': 0.00740056}, "SF6 Bullister 2002 coefficients assertion failed."

def test_hec():
    assert hec('N2') == {'A0': 6.42931, 'A1': 2.92704, 'A2': 4.32531, 'A3': 4.69149, 'B0': -7.44129e-3, 'B1': -8.02566e-3, 'B2': -1.46775e-2}, "N2 Hamme/Emerson 2004 coefficients assertion failed"
    assert np.array_equal(hec(['N2', 'Ar']), np.array([{'A0': 6.42931, 'A1': 2.92704, 'A2': 4.32531, 'A3': 4.69149, 'B0': -7.44129e-3, 'B1': -8.02566e-3, 'B2': -1.46775e-2},
                                                       {'A0': 2.79150, 'A1': 3.17609, 'A2': 4.13116, 'A3': 4.90379, 'B0': -6.96233e-3, 'B1': -7.66670e-3, 'B2': -1.16888e-2}])
                         ), "Hamme/Emerson 2004 coefficients of multiple gases assertion failed."

def test_mv():
    assert mv('He') == 22425.8703182828, "Helium molar volume assertion failed."
    assert np.array_equal(mv(['He', 'Ar']), np.array([22425.8703182828, 22392.5703182828])), "Molar volume assertion for multiple gases failed."

def test_mm():
    assert mm('He') == 4.002602, "Helium molar mass assertion failed."
    assert np.array_equal(mm(['He', 'Ar']), np.array([4.002602, 39.948])), "Molar mass assertion for multiple gases failed."

def test_abn():
    assert abn('He') == 5.24E-6, "Helium molar mass assertion failed."
    assert np.array_equal(abn(['He', 'Ar']), np.array([5.24E-6, 0.934E-2])), "Abundance assertion for multiple gases failed."

def test_ice():
    assert ice('He') == 1.33
    assert np.array_equal(ice(['He', 'Ar']), np.array([1.33, 0.49]))