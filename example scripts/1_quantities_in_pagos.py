"""
Here is a brief overview of how quantities work in PAGOS and how to deal with them.
"""

# Importing
from printlines import printlines
from pagos import Q

# The PAGOS Q() function is used to define quantities. Not all functions in PAGOS require the use
# of quantities defined in this way, and indeed fitting procedures are slower when using them.
# Nevertheless, they are excellent for checking if units agree at either end of calculations.

myMass = Q(15, 'kg')
mySpeed = Q(1.5, 'm/s')
myEnergy = Q(1.0, 'kJ')

# The Q() function directly calls the Quantity() constructor from Pint. All quantities in PAGOS
# define in this way are Quantity objects from Pint. Pint has an excellent unit-string parser and
# provides almost all of the useful functionality of quantities relevant to PAGOS.

printlines(('mass:', myMass, 'speed:', mySpeed, 'energy:', myEnergy), 2)

# New quantities can be created by combining old ones, and quantities with compatible units can be
# added and subtracted from each other. One can also see here that unit conversion is performed
# automatically:

myNewEnergy = myMass * mySpeed**2
addedEnergies = myEnergy + myNewEnergy
print(str(myMass) + ' * (' + str(mySpeed) + ')^2' + ' = ' + str(myNewEnergy))
print(str(myEnergy) + ' + ' + str(myNewEnergy) + ' = ' + str(addedEnergies))

# Check out the other example scripts (e.g. calculating_water_properties.py) for usages of these
# Quantity objects in PAGOS functions.

# Final point: attempting to add quantities of incompatible units will raise an error. Uncomment
# the following line to see:
#willFail = myMass + mySpeed # -> raises DimensionalityError due to incompatible units