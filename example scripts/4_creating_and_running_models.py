"""
Here is a tutorial on how to create and use gas exchange models in PAGOS.
"""

# Importing
from printlines import printlines
from pagos import gas as pgas
from pagos.modelling import GasExchangeModel
from pagos import Q

# PAGOS allows for simple user-definition of gas exchange models.

# Say we wanted to implement a simple unfractionated excess air model (that is, equilibrium
# concentration "topped up" with an excess air component):
# C(T, S, p, A) = Ceq(T, S, p) + A*z, where A is in the units of Ceq and z is the atmospheric
# abundance of the gas. We can implement it very simply like this:

def ua_model(gas, T, S, p, A):
    Ceq = pgas.calc_Ceq(gas, T, S, p)
    z = pgas.abn(gas)   # <- pagos.gas.abn(G) returns the dimensionless atmospheric abundance of G
    return Ceq + A * z
UAModel = GasExchangeModel(ua_model, ['degC', 'permille', 'atm', 'cc/g'], 'cc/g')

# The arguments to GasExchangeModel() are the user-defined function describing the model, a tuple
# of default input units and one default output unit. The default input units correspond to the
# assumed units of the arguments of the model function, here (T, S, p, A). The output units are
# those in which the result of the model is expressed. Note that they are DEFAULT units, but can be
# overridden:

myResult1 = UAModel.run('Ne', 10, 30, 1, 5e-4) # no given units, default units assumed
myResult2 = UAModel.run('Ne', Q(10, 'degC'), Q(30, 'permille'), Q(1, 'atm'), Q(5e-4, 'cc/g')) # units manually given but are the same as the defaults
myResult3 = UAModel.run('Ne', Q(283.15, 'K'), Q(3, 'percent'), 1, 5e-4) # non-default units included, default units of degC and permille overridden

printlines(('Result with no given units:', myResult1, 'Result with given units matching defaults:', myResult2, 'Result with overridden units:', myResult3), 2)

# After running the above script you should see that all the results are the same! If messing
# around with the Q() constructor isn't to your liking, one can also override units thus:

myResult4 = UAModel.run('Ne', 283.15, 3, 1, 5e-4, units_in=['K', 'percent', 'atm', 'cc/g'])
print('Result using units_in kwarg:', myResult4)

# The returned units may also be altered with the units_out keyword argument. Additionally, note
# here that the 'percent' in units_in is overridden by the explicit Quantity object with its
# already given 'permille' unit. This is a nice safeguard, but also a good reason NOT to use the
# units_in argument along with Q()-based model arguments, as units_in will always be silently
# overridden.

myResult5 = UAModel.run('Ne', 10, Q(30, 'permille'), 1, 5e-4, units_in=['degC', 'percent', 'atm', 'cc/g'], units_out='m^3/kg')
print('Result in using units_out kwarg:', myResult5)

# Here is an example of another, more complicated gas exchange model we might like to implement,
# the closed-system equilibration (CE) model:

def ce_model(gas, T, S, p, F, A):
    Ceq = pgas.calc_Ceq(gas, T, S, p)
    z = pgas.abn(gas)
    return (1 - F)*A*z / (1 + F*A*z/Ceq)
CEModel = GasExchangeModel(ce_model, ['degC', 'permille', 'atm', '', 'cc/g'], 'cc/g')

myResult6 = CEModel.run(['Ne', 'Ar', 'Kr', 'Xe'], 10, 30, 1, 0.15, 5e-4)
print('Result of CE model:', myResult6)

# One can see here the easy implementation of any function you like as a gas exchange model in
# PAGOS. The only constraint is that the first argument of any gas exchange model function to be
# used in PAGOS *must* be the argument storing the gas/gases for which the model is calculated!