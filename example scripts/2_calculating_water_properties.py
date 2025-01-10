"""
Here are some examples of how to use the `water` module from PAGOS. 
"""

# Importing
from printlines import printlines
from pagos import water as pwater
from pagos import Q

# Calculating the density of water

myTemp1 = Q(10, 'degC')
mySal1 = Q(30, 'permille')
myDensity1 = pwater.calc_dens(myTemp1, mySal1)
print('myDensity1:', myDensity1)

# As with all functions in pagos.water, calc_dens() has default assumed units of degC and permille.
# Calling the function with no units in the input therefore assumes you meant these units:

myDensity2 = pwater.calc_dens(10, 30)
printlines(('myDensity2:', myDensity2, 'both densities are equal?:', myDensity1==myDensity2), 2)

# PAGOS will also automatically convert units of a different kind:
myTemp2 = Q(283.15, 'K')
mySal2 = Q(3, 'percent')
myDensity3 = pwater.calc_dens(myTemp2, mySal2)
printlines(('myDensity3:', myDensity3, 'conversion was successful?:', myDensity1==myDensity3), 2)

# Other quantities available for calculation are the vapour pressure above some water and the
# kinematic viscosity of water
myVapourPres = pwater.calc_vappres(myTemp1)
myKinVisc = pwater.calc_kinvisc(myTemp1, mySal1)
printlines(('myVapourPres:', myVapourPres, 'myKinVisc', myKinVisc), 2)