# Quantities and Magnitudes

## Basics
Quantities used in PAGOS may contain units. Functions in PAGOS are designed for use with `PAGOSQuantity` objects (extensions of `Quantity` from [Pint](https://pint.readthedocs.io/en/stable/)), but can also be used with regular Python datatypes. The following code produces such a quantity representing the speed 11.2 m/s.
```py
from pagos import pQ
mySpeed = pQ(11.2, 'm/s')
print(mySpeed)
# -> 11.2 meter / second
```
PAGOS quantities have a `value` and `units` property, which extract the value and units respectively:
```py
volume = pQ(1e-4, 'm^3')
print(volume)
# -> 0.0001 meter ** 3
print(volume.value)
# -> 0.0001
print(volume.units)
# -> meter ** 3
```

Quantities may be expressed in any units one wishes, as long as the unconverted and converted units are commensurable.
This is achieved with the `to` method.
```py
density = pQ(1e-4, 'g/cm^3')
print(density)
# -> 0.0001 gram / centimeter ** 3
print(density.to('ug/m^3'))
# -> 1e+08 microgram / meter ** 3
```

## Gas-specific quantities
For gas tracer applications, there are many different conventions for measured gas amounts/concentrations. PAGOS provides "suffixed" units for each built-in gas, and for a generic gas:

```py
amountHe = pQ(3, 'mol_He')
amountCFC12 = pQ(3, 'umol_CFC12')
amountAr = pQ(1.5, 'ccSTP_Ar')
amountKr = pQ(1.5, 'g_Kr')
amountGeneric = pQ(12, 'g_gas')
amountGeneric2 = pQ(10, 'ccSTP_g')
...
# -> 3 mole_He
# -> 3 micromole_CFC12
# -> 1.5 cubic_centimeter_STP_Ar
# -> 1.5 gram_Kr
# -> 12 gram_gas
# -> 10 cubic_centimeter_STP_gas
```
The currently implemented gas-specific unis are given in the table below
| Dimension  | Unit                           | String                   | Shorthand aliases |
|------------|--------------------------------|--------------------------|-------------------|
| Amount     | $$\mathrm{mol}$$               | `mole_gas`                 | `mol_g`             |
| Mass       | $$\mathrm{g}$$                 | `gram_gas`                 | `g_g`               |
| STP volume | $$\mathrm{cm}^3_\mathrm{STP}$$ | `cubic_centimeter_STP_gas` | `ccSTP_g`, `cm3STP_g` |

!!!Note
    Future versions of PAGOS should include more units for gas amounts/concentrations (e.g. mmHg, bar).

The neat thing about these units is that they can be converted between each other, so long as the gas type is the same (or generic):
```py
amountHe = pQ(3, 'mol_He')
print(amountHe.to('ccSTP_He'))
# -> 67277.611 cubic_centimeter_STP_He

# Generic gas suffix means PAGOS should infer the required gas from the PAGOSQuantity's units
print(amountHe.to('g_g'))
# -> 12.007806 gram_He
```
An exception is raised when trying to convert two generic quantities, because there is no specification for the gas type (program thinks: "which gas?!").
```py
pQ(10, 'mol_g').to('ccSTP_g')
# -> ValueError: Attempted a conversion between two generically-suffixed units (with '_gas', '_g').
```

## Arithmetic
Quantities with commensurable units can be combined with arithmetic, and the conversions are performed automatically.
```py
concentration1 = pQ(1e-4, 'mol_Ar/kg')
concentration2 = pQ(2000, 'umol_Ar/kg')

concentration3 = concentration1 + concentration2

print(concentration3)
# -> 0.0021 mole_Ar / kilogram
```

PAGOS quantities with incommensurable units can still be multiplied/divided (as will be their units), but not added/subtracted.
```py
concentration = pQ(1e-4, 'mol_Ar/kg')
velocity = pQ(0.5, 'm/s')

flux = concentration * velocity
print(flux)
# -> 5e-05 mole_Ar * meter / kilogram / second

bad_quantity = concentration + velocity
# -> pint.errors.DimensionalityError: Cannot convert from 'meter / second' ([length] / [time]) to 'mole_Ar / kilogram' ([amount_Ar] / [mass])
```

## The `UnitRegistry` [:material-flash-alert:](./#the-unitregistry "Advanced")
It is worth noting that Pint handles units by comparing them to other units inside a `UnitRegistry` object - 
all `PAGOSQuantity` objects are constructed from the `UnitRegistry`, and it contains all the units that Pint is
aware of in a given program. One problem that can arise is that Pint units only "know" about each other if
they come from the _same_ `UnitRegistry`. I.e. the following code:
```py
from pint import UnitRegistry, Quantity
from pagos import pQ
u1 = UnitRegistry()
mass1 = pQ(1, 'kg')
mass2 = u1.Quantity(2, 'kg')

mass_sum = mass1 + mass2
```
will fail. This is something you should be aware of if integrating PAGOS with programs that already use Pint `Quantity` objects.

The `UnitRegistry` defined by PAGOS can be accessed with `pagos.core.ureg`, if absolutely necessary.
