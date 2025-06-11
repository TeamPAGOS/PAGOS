# Quantities and Magnitudes

## Basics
This package is designed with a number of "numerical safeguards". Quantities used in PAGOS may contain units, and uncertainties. Functions in PAGOS are designed for use with `Quantity` objects from [Pint](https://pint.readthedocs.io/en/stable/), but can also be used with regular Python datatypes. The following code produces such a quantity representing the speed 11.2 m/s.
```py
from pagos import Q
mySpeed = Q(11.2, 'm/s')
print(mySpeed)
# -> 11.2000 meter / second
```
Those familiar with Pint will recognise `Q()` as a shortcut for `pint.UnitRegistry.Quantity()`. This is the PAGOS-safe version though, as it will always refer to the universal `UnitRegistry` defined in `pagos.core`.

Quantities have a `magnitude` and `units` property, which extract the magnitude and units respectively:
```py
concentration = Q(1e-4, 'mol/kg')
print(concentration)
# -> 0.0001 mole / kilogram
print(concentration.magnitude)
# -> 0.0001
print(concentration.units)
# -> mole / kilogram
```

Quantities may be expressed in any units one wishes, as long as the unconverted and converted units are commensurable.
This is achieved with the `Quantity.to` method.
```py
concentration = Q(1e-4, 'mol/kg')
print(concentration)
# -> 0.0001 mole / kilogram
print(concentration.to('umol/kg'))
# -> 100.0 micromole / kilogram
print(concentration.to('mol / mm / s^2 / hPa'))
# -> 9.999999999999999e-06 mole / hectopascal / millimeter / second ** 2
```
We can see here that quantity conversion is not immune to the quirks of floating point arithmetic.

## Arithmetic
Quantities with commensurable units can be combined with arithmetic, and the conversions are performed automatically.
```py
concentration1 = Q(1e-4, 'mol/kg')
concentration2 = Q(2000, 'umol/kg')

concentration3 = concentration1 + concentration2

print(concentration3)
# -> 0.0021 mole / kilogram
```

Quantities with incommensurable units can still be multiplied/divided (as will be their units), but not added/subtracted.
```py
concentration = Q(1e-4, 'mol/kg')
velocity = Q(0.5, 'm/s')

flux = concentration * velocity
print(flux)
# -> 5e-05 meter * mole / kilogram / second

bad_quantity = concentration1 + velocity
# -> pint.errors.DimensionalityError: 
#    Cannot convert from 'mole / kilogram' ([substance] / [mass])
#    to 'meter / second' ([length] / [time])
```

## Functions in PAGOS with Quantity Inputs/Outputs
Many functions in PAGOS output `Quantity` objects by default and have the option to have `Quantity` inputs.
For example, let's look at the function to calculate the density of seawater, `pagos.water.calc_dens`. The
inputs to this function are the temperature $T$ and salinity $S$. These can be quantities bearing units of
our choice (provided they are indeed units of temperature and salinity - e.g. Kelvin is a valid unit for
$T$, but not Joules). Here we see an example with K and &permil;.
```py
from pagos.water import calc_dens
from pagos import Q
temp = Q(290, 'K')
sal = Q(20, 'permille')

density = calc_dens(temp, sal)
print(density)
# -> 1014.071552984602 kilogram / meter ** 3
``` 
Here we see the output is also a `Quantity` with units of kilogram per cubic metre.

### Default units
If the arguments to a PAGOS function are not given as `Quantity` objects, then their units will be _assumed_.
The default units assumed by a function are shown in the docstring. For example, running `help(calc_dens)`{:.py} will
output the following
```linenums="1"
Help on function calc_dens in module pagos.water:

calc_dens(T: float | pint.registry.Quantity, S: float | pint.registry.Quantity) -> pint.registry.Quantity
    Calculate density of seawater at given temperature and salinity, according to Gill 1982.\
    **Default input units** --- `T`:°C, `S`:\u2030\
    **Output units** --- kg/m³

...
```

The default input and output units are shown on lines 5 and 6. We can see a problem here where the
permille symbol (‰) does not render(1). Also, note that this is actually written for interpretation in markdown;
in a markdown-compatible tooltip in an IDE, it would look like this:
{ .annotate }

1. This should be changed in a future version of PAGOS to just have "permille" written instead of a non-ASCII character.

>Calculate density of seawater at given temperature and salinity, according to Gill 1982.<br>
>**Default input units** --- `T`:°C, `S`:‰<br>
>**Output units** --- kg/m³

Thus, any inputs to the function without explicit units will be assumed to have units of °C and ‰:
```py
print(calc_dens(15, 20))
# -> 1014.4433634457197 kilogram / meter ** 3
```

The outputs of PAGOS unit-aware functions can be converted to magnitudes in three different ways:
1. by explicitly calling the Pint `Quantity.magnitude` method as discussed above,
2. by including a `magnitude=True` keyword argument in the function call,
3. by using the `snv` function from `pagos.core`.
```py
from pagos.water import calc_dens
from pagos.core import snv

print(calc_dens(15, 20).magnitude)
print(calc_dens(15, 20, magnitude=True))
print(snv(calc_dens(15, 20)))
# -> all print 1014.4433634457197
```

!!!Note
    `snv` is mainly designed for
    situations where a variable could be a `Quantity`, a `Variable` from the uncertainties package or a
    `Quantity` whose magnitude is a `Variable`. For regular `Quantities` with `float`-like magnitudes it
    functions the same as `to`.

## The `UnitRegistry`
It is worth noting that Pint handles units by comparing them to other units inside a `UnitRegistry` object - 
all `Quantity` objects are constructed from the `UnitRegistry`, and it contains all the units that Pint is
aware of in a given program. One problem that can arise is that Pint units only "know" about each other if
they come from the _same_ `UnitRegistry`. I.e. the following code:
```py
from pint import UnitRegistry, Quantity
from pagos import Q
u1 = UnitRegistry()
mass1 = Q(1, 'kg')
mass2 = u1.Quantity(2, 'kg')

mass_sum = mass1 + mass2
```
will raise a `ValueError: Cannot operate with Quantity and Quantity of different registries.`. This is
something you should be aware of if integrating PAGOS with programs that already use Pint `Quantity`
objects.

The `UnitRegistry` defined by PAGOS can be accessed with `pagos.units.u`, if absolutely necessary.