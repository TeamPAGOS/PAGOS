# Tests calc_kinvisc() from pagos.water.

from pagos.water import calc_kinvisc
from pagos import Q

Ts = [10, 0, 4, -2]
Ss = [30, 0, 0, 30]
nus = [Q(1.3516218130144556e-06, 'm^2/s'),
       Q(1.7917258528926718e-06, 'm^2/s'),
       Q(1.5672053001198507e-06, 'm^2/s'),
       Q(1.9771357589101157e-06, 'm^2/s')]

# all inputs floats
def test_calc_dens_all_floats():
    for temp, sal, nu in zip(Ts, Ss, nus):
        result = calc_kinvisc(temp, sal)
        assert result == nu, "incorrect value (%s) for kinematic viscosity of water at %i degC, %i permille" % (result, temp, sal)

# all inputs Quantity, units set to function default
def test_calc_dens_all_quants_default_units():
    for temp, sal, nu in zip(Ts, Ss, nus):
        temp, sal = Q(temp, 'degC'), Q(sal, 'permille')
        result = calc_kinvisc(temp, sal)
        assert result == nu, "incorrect value (%s) for kinematic viscosity of water at T=%s, S=%s" % (result, temp, sal)

# all inputs Quantity, units different to function default
def test_calc_dens_all_quants_custom_units():
    for temp, sal, nu in zip(Ts, Ss, nus):
        temp, sal = Q(temp + 273.15, 'K'), Q(sal/10, 'percent')
        result = calc_kinvisc(temp, sal)
        assert result == nu, "incorrect value (%s) for kinematic viscosity of water at T=%s, S=%s" % (result, temp, sal)

# inputs mixed floats/Quantity inputs
def test_calc_dens_mixed():
    for temp, sal, nu in zip(Ts, Ss, nus):
        tempf, salq = temp, Q(sal, 'permille')
        result = calc_kinvisc(tempf, salq)
        assert result == nu, "incorrect value (%s) for kinematic viscosity of water at [float] T=%s 'degC', [Quantity] S=%s" % (result, tempf, salq)

