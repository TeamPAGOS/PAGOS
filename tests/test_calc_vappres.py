# ASK KAI: how can I make sure the PAGOS version being tested is inside the repository and not the installed version?

# Tests calc_vappres() from pagos.water

from pagos.water import calc_vappres, calc_vappres_Tderiv
from pagos import Q

Ts = [10, 60]
vps = [Q(12.272370555643239, 'millibar'),
        Q(199.89398342218266, 'millibar')]
dvp_dTs = [Q(0.8220511325683609, 'millibar/kelvin'),
            Q(9.294663970421336, 'millibar/kelvin')]

# regular function

# input float
def test_calc_vappres_float():
    for temp, vp in zip(Ts, vps):
        assert calc_vappres(temp) == vp, "incorrect value for vapour pressure above water at %i degC" % temp

# input Quantity, units set to function default
def test_calc_vappres_quant_default_units():
    for temp, vp in zip(Ts, vps):
        temp = Q(temp, 'degC')
        assert calc_vappres(temp) == vp, "incorrect value for vapour pressure above water at %s degC" % temp

# input Quantity, units different to function default
def test_calc_vappres_quant_default_units():
    for temp, vp in zip(Ts, vps):
        temp = Q(temp + 273.15, 'K')
        assert calc_vappres(temp) == vp, "incorrect value for vapour pressure above water at %s degC" % temp



# T-derivatives

# input float
def test_calc_vappres_Tderiv_float():
    for temp, dvp_dT in zip(Ts, dvp_dTs):
        result = calc_vappres_Tderiv(temp)
        assert result == dvp_dT, "incorrect value (%s) for the temperature-derivative of vapour pressure above water at %i degC" % (result, temp)

# input Quantity, units set to function default
def test_calc_vappres_Tderiv_quant_default_units():
    for temp, dvp_dT in zip(Ts, dvp_dTs):
        temp = Q(temp, 'degC')
        result = calc_vappres_Tderiv(temp)
        assert result == dvp_dT, "incorrect value (%s) for the temperature-derivative of vapour pressure above water at %s degC" % (result, temp)

# input Quantity, units different to function default
def test_calc_vappres_Tderiv_quant_default_units():
    for temp, dvp_dT in zip(Ts, dvp_dTs):
        temp = Q(temp + 273.15, 'K')
        result = calc_vappres_Tderiv(temp)
        assert result == dvp_dT, "incorrect value (%s) for the temperature-derivative of vapour pressure above water at %s degC" % (result, temp)

