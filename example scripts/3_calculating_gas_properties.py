"""
Here are some examples of how to use the `gas` module from PAGOS. 
"""

# Importing
from printlines import printlines
from pagos import gas as pgas
from pagos import Q

# (For a more thorough explanation of the Q() function, see quantities_in_pagos.py)

# The gas module from PAGOS functions much in the same way as for the water module, except for
# calculating gas properties instead of water properties. Like the water module, each function's
# arguments have default units, which are assumed in the absence of user-given units. See here how
# all of these expressions return the same thing:
myTemp, myTempC, myTempK = 20, Q(20, 'degC'), Q(293.15, 'K')
mySal, mySalpm, mySalpc = 32, Q(32, 'permille'), Q(3.2, 'percent')
myPres, myPresatm, myPreshPa = 1, Q(1, 'atm'), Q(1013.25, 'hPa')
Ceq1 = pgas.calc_Ceq('Ne', myTemp, mySal, myPres)
Ceq2 = pgas.calc_Ceq('Ne', myTempC, mySalpm, myPresatm)
Ceq3 = pgas.calc_Ceq('Ne', myTempK, mySalpc, myPreshPa)

printlines(('Ceq1:', Ceq1, 'Ceq2:', Ceq2, 'Ceq3:', Ceq3), 2)

# This function, calc_Ceq(gas, T, S, p), calculates the equilibrium concentration of a gas in water
# at a given temperature T, salinity S and pressure p. Above we have calculated it for neon. But we
# can also calculate it for other gases, and multiple at once:

Ceqs = pgas.calc_Ceq(['Ne', 'Ar', 'N2', 'CFC12'], 20, 32, myPreshPa)
print('Ceq(Ne, Ar, N2, CFC12) =', Ceqs, 'ccSTP/g')

# Note how we can even combine dimensionless and dimensioned arguments! We can also optionally set
# the calc_Ceq function to return the concentration in different dimensions (default is ccSTP/g).
# It's also possible to return these units along with the quantity:

Ceqsmolkg = pgas.calc_Ceq(['Ne', 'Ar', 'N2', 'CFC12'], 20, 32, myPreshPa, 'mol/kg')
print('Ceq(Ne, Ar, N2, CFC12) =', Ceqsmolkg, 'mol/kg')
Ceqsmolcc = pgas.calc_Ceq(['Ne', 'Ar', 'N2', 'CFC12'], 20, 32, myPreshPa, 'mol/cc', ret_quant=True)
print('Ceq(Ne, Ar, N2, CFC12) =', Ceqsmolcc)

# Another calculation in the gas module is that of the Schmidt number:

Sc = pgas.calc_Sc('Ne', myTemp, mySal)
print('Sc(Ne) =', Sc)