# ASK KAI: how can I make sure the PAGOS version being tested is inside the repository and not the installed version?

# Tests calc_dens() from pagos.water and its associated derivatives

from pagos.water import calc_dens, calc_dens_Tderiv, calc_dens_Sderiv
from pagos import Q

Ts = [10, 0, 4, -2]
Ss = [30, 0, 0, 30]
rhos = [Q(1023.0511189339445, 'kg/m^3'),
        Q(999.842594, 'kg/m^3'),
        Q(999.974958175956, 'kg/m^3'),
        Q(1024.1185428978292, 'kg/m^3')]
drho_dTs = [Q(-0.16031187007507228, 'kg/m^3/K'),
            Q(0.06793952, 'kg/m^3/K'),
            Q(-0.0002930867430400018, 'kg/m^3/K'),
            Q(-0.00872035575824636, 'kg/m^3/K')]
drho_dSs = [Q(0.7794654690372231, 'kg/m^3/permille'),
            Q(0.824493, 'kg/m^3/permille'),
            Q(0.80930500832, 'kg/m^3/permille'),
            Q(0.8132059110359867, 'kg/m^3/permille')]

# all inputs floats
def test_calc_dens_all_floats():
    for temp, sal, rho in zip(Ts, Ss, rhos):
        result = calc_dens(temp, sal)
        assert result == rho, "incorrect value (%s) for density of water at %i degC, %i permille" % (result, temp, sal)

# all inputs Quantity, units set to function default
def test_calc_dens_all_quants_default_units():
    for temp, sal, rho in zip(Ts, Ss, rhos):
        temp, sal = Q(temp, 'degC'), Q(sal, 'permille')
        result = calc_dens(temp, sal)
        assert result == rho, "incorrect value (%s) for density of water at T=%s, S=%s" % (result, temp, sal)

# all inputs Quantity, units different to function default
def test_calc_dens_all_quants_custom_units():
    for temp, sal, rho in zip(Ts, Ss, rhos):
        temp, sal = Q(temp + 273.15, 'K'), Q(sal/10, 'percent')
        result = calc_dens(temp, sal)
        assert result == rho, "incorrect value (%s) for density of water at T=%s, S=%s" % (result, temp, sal)

# inputs mixed floats/Quantity inputs
def test_calc_dens_mixed():
    for temp, sal, rho in zip(Ts, Ss, rhos):
        tempf, salq = temp, Q(sal, 'permille')
        result = calc_dens(tempf, salq)
        assert result == rho, "incorrect value (%s) for density of water at [float] T=%s 'degC', [Quantity] S=%s" % (result, tempf, salq)



# T-derivatives

# all inputs floats
def test_calc_dens_Tderiv_all_floats():
    for temp, sal, drho_dT in zip(Ts, Ss, drho_dTs):
        result = calc_dens_Tderiv(temp, sal)
        assert result == drho_dT, "incorrect value (%s) for temperature-derivative of density of water at %i degC, %i permille" % (result, temp, sal)
    
# all inputs Quantity, units set to function default
def test_calc_dens_Tderiv_all_quants_default_units():
    for temp, sal, drho_dT in zip(Ts, Ss, drho_dTs):
        temp, sal = Q(temp, 'degC'), Q(sal, 'permille')
        result = calc_dens_Tderiv(temp, sal)
        assert result == drho_dT, "incorrect value (%s) for temperature-derivative of density of water at T=%s, S=%s" % (result, temp, sal)

# all inputs Quantity, units different to function default
def test_calc_dens_Tderiv_all_quants_custom_units():
    for temp, sal, drho_dT in zip(Ts, Ss, drho_dTs):
        temp, sal = Q(temp + 273.15, 'K'), Q(sal/10, 'percent')
        result = calc_dens_Tderiv(temp, sal)
        assert result == drho_dT, "incorrect value (%s) for temperature-derivative of density of water at T=%s, S=%s" % (result, temp, sal)
    
# inputs mixed floats/Quantity inputs
def test_calc_dens_Tderiv_mixed():
    for temp, sal, drho_dT in zip(Ts, Ss, drho_dTs):
        tempf, salq = temp, Q(sal, 'permille')
        result = calc_dens_Tderiv(tempf, salq)
        assert result == drho_dT, "incorrect value (%s) for temperature-derivative of density of water at [float] T=%s 'degC', [Quantity] S=%s" % (result, tempf, salq)
        


# S-derivatives

# all inputs floats
def test_calc_dens_Sderiv_all_floats():
    for temp, sal, drho_dS in zip(Ts, Ss, drho_dSs):
        result = calc_dens_Sderiv(temp, sal)
        assert result == drho_dS, "incorrect value (%s) for salinity-derivative of density of water at %i degC, %i permille" % (result, temp, sal)
    
# all inputs Quantity, units set to function default
def test_calc_dens_Sderiv_all_quants_default_units():
    for temp, sal, drho_dS in zip(Ts, Ss, drho_dSs):
        temp, sal = Q(temp, 'degC'), Q(sal, 'permille')
        result = calc_dens_Sderiv(temp, sal)
        assert result == drho_dS, "incorrect value (%s) for salinity-derivative of density of water at T=%s, S=%s" % (result, temp, sal)

# all inputs Quantity, units different to function default
def test_calc_dens_Sderiv_all_quants_custom_units():
    for temp, sal, drho_dS in zip(Ts, Ss, drho_dSs):
        temp, sal = Q(temp + 273.15, 'K'), Q(sal/10, 'percent')
        result = calc_dens_Sderiv(temp, sal)
        assert result == drho_dS, "incorrect value (%s) for salinity-derivative of density of water at T=%s, S=%s" % (result, temp, sal)
    
# inputs mixed floats/Quantity inputs
def test_calc_dens_Sderiv_mixed():
    for temp, sal, drho_dS in zip(Ts, Ss, drho_dSs):
        tempf, salq = temp, Q(sal, 'permille')
        result = calc_dens_Sderiv(tempf, salq)
        assert result == drho_dS, "incorrect value (%s) for salinity-derivative of density of water at [float] T=%s 'degC', [Quantity] S=%s" % (result, tempf, salq)