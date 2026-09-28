# Usage
This is a relatively abridged version of the information you can find in `example scripts`.
## How quantities are defined in PAGOS
This package is designed with a number of "numerical safeguards". Quantities used in PAGOS may contain units, and uncertainties. Functions in PAGOS are designed for use with `Quantity` objects from [Pint](https://pint.readthedocs.io/en/stable/), but can also be used with regular Python datatypes. The following code produces such a quantity representing the speed 11.2 m/s.
```py
from pagos import pQ
mySpeed = pQ(11.2, 'm/s')
print(mySpeed)
# -> 11.2000 meter / second
```
`pQ` is a shortcut to create a `PAGOSQuantity` object, which stores value and unit data, just as Pint `Quantity`s, but with optimisations for PAGOS.

## Water property calculations
The properties of seawater and various gases can be calculated with the `water` and `gas` modules. For example, calculating the density of water at a given temperature and salinity:
```py
from pagos import water as pwater
from pagos import pQ

myTemp1 = pQ(10, 'degC')
mySal1 = pQ(30, 'permille')

myDensity1 = pwater.calc_dens(myTemp1, mySal1)
myDensity2 = pwater.calc_dens(10, 30) # <- default units of degC and permille assumed

print(myDensity1)
print(myDensity2)
# -> 1023.05112 kilogram / meter ** 3
# -> 1023.05112 kilogram / meter ** 3
```
We can see that the water property function have default, assumed units for any given float arguments. You can see these by accessing the `default_units_in` and `units_out` methods:

```py
print(pwater.calc_dens.default_units_in)
# -> {'T': 'degC', 'S': 'permille'}
print(pwater.calc_dens.units_in)
```
or in the docstrings of the respective functions: 
```
console:

>>> help(pwater.calc_dens)
Help on function calc_dens in module pagos.water:

calc_dens(T: float | PAGOSQuantity, S: float | PAGOSQuantity) -> PAGOSQuantity
    Calculate density of seawater at a given temperature and salinity, according to Gill 1982.

    ## Units
        **default units in** — `T`:°C, `S`:‰
        **default units out** — kg/m³

    ...
```

PAGOS will also automatically convert units of a different kind:

```py
myTemp2 = pQ(283.15, 'K')
mySal2 = pQ(3, 'percent')

myDensity3 = pwater.calc_dens(myTemp2, mySal2)

print(myDensity3)
# -> 1023.05112 kilogram / meter ** 3

```

Other properties available to be calculated for water are vapour pressure over the water and kinematic viscosity of the water, given temperature and salinity:
```py
myVapourPres = pwater.calc_vappres(myTemp1)
myKinVisc = pwater.calc_kinvisc(myTemp1, mySal1)
print(myVapourPres)
print(myKinVisc)
# -> 12.2723706 millibar
# -> 1.35162181e-06 meter ** 2 / second
```
## Gas property calculations 
Much like the bulk water properties, properties of gases dissolved in water can also be calculated. These are dependent on the species of gas we are interested in:
```py
from pagos.gas import Ar, SF6

# Schmidt number of Ar at T = 10 degC, S = 20 permille
print(Ar.calc_Sc(10, 20))
# ->
# Same calculation for SF6
print(SF6.calc_Sc(pQ(283.15, 'K'), 20))
```
In the above example, `Ar` and `SF6` are built-in instances of the `Gas` object. `Gas` exposes methods, such as `calc_Sc`, associated with gas-dependent calculations. Like the functions from `water`, these methods have default units in and out, which can be similarly accessed (see [previous section](#water-property-calculations)).

The methods and properties of `Gas` can be accessed from outside:
```py
from pagos.gas import Ar, calc_Sc, calc_Ceq, abn, molvol
# Schmidt number (method)
assert Ar.calc_Sc(10, 20) == calc_Sc(Ar, 10, 20)
# Equilibrium concentration (method)
# Note: name of gas as string works in external function
assert Ar.calc_Ceq(10, 20, 1) == calc_Ceq('Ar', 10, 20, 1)
# Atmospheric abundance (property)
assert Ar.abundance == abn(Ar)
# Molar volume (property)
assert Ar.molar_volume == molvol(Ar)
```


## Creating and fitting models
### Designing a model
The real power of PAGOS is in its gas exchange modelling capabilities. PAGOS allows for simple user-definition of gas exchange models. Say we wanted to implement a simple unfractionated excess air (UA) model (that is, equilibrium concentration $C^\mathrm{eq}$ "topped up" with an excess air component):

$$
C_\mathrm{gas}^\mathrm{UA}(T, S, p, A) = C_\mathrm{gas}^\mathrm{eq}(T, S, p) + A\cdot z,
$$

where $A$ is in the units of $C^\mathrm{eq}_\mathrm{gas}$ and $z$ is the atmospheric abundance of the gas. We could implement it very simply like this:
```py
from pagos.gas import calc_Ceq, abn
from pagos.modelling import TracerModel
def ua_func(gas, T, S, p, A):
    Ceq = calc_Ceq(gas, T, S, p) # -> mol_gas / kg
    z = abn(gas) # -> mol_gas / mol
    return Ceq + A * z
```
Because `calc_Ceq` and `abn` have their own default output units, PAGOS will throw an error if the units of `A` are not compatible:
```
>>> ua_func('Ar', 10, 0, 1, 1e-5)
...
pint.errors.DimensionalityError: Cannot convert from 'mole_Ar / mole' ([amount_Ar] / [substance]) to 'mole_Ar / kilogram' ([amount_Ar] / [mass])
```
A `DimensionalityError` was thrown here because the `A * z` expression evaluated to a quantity with units of mol_Ar/mol, but `Ceq` is in mol_Ar/kg. Rightfully, the user is refused this calculation.

What we needed was `A` to have units compatible with mol/kg:
```
>>> ua_func('Ar', 10, 0, 1, pQ(1e-5, 'mol/kg'))
<PAGOSQuantity(1.74364437e-05, 'mole_Ar / kilogram')>
```
### Automatic unit handling
In the above example, we were able to just use `10`, `0`, `1` for the first arguments `T`, `S`, `p`, because these are passed into `calc_Ceq`, which has `default_units_in`. We can also provide our own `default_units_in` for all arguments:
```py
from pagos.core import unit_aware

@unit_aware(default_units_in={'gas':None, 'T':'degC', 'S':'permille', 'p':'atm', 'A':'mol/kg'}, units_out='mol_g/kg')
def ua_func(gas, T, S, p, A):
    Ceq = calc_Ceq(gas, T, S, p) # -> mol_gas / kg
    z = abn(gas) # -> mol_gas / mol
    return Ceq + A * z

print(ua_func('Ar', 10, 0, 1, 1e-5))
# -> 1.74364437e-05 mole_Ar / kilogram
```
The arguments to `ua_func` must all be accounted for (including `gas`, which of course has no units, so is designated `None`.) Note that the `units_out` argument has `_g` as a suffix, which is a _generic_ gas signifier (we may not just be interested in Ar, but any number of gases, and we don't want to write a separate function for each one.)

 With this, we can use our newly defined function as we do the built-ins from the `gas` or `water` modules.

### `TracerModel` objects
This is all well and good, but in the end we want to optimise our models. Such functionality is packaged in the `modelling` module and its `TracerModel` object.

```py
from pagos.modelling import TracerModel
uaModel = TracerModel(ua_func)
```

When we crate a `TracerModel` in this way, the `default_units_in` and `units_out` are inherited from the wrapped `unit_aware` function. If we had not done this in preparation, we can handle it directly in the constructor:

```py
def ua_func(gas, T, S, p, A):
    Ceq = calc_Ceq(gas, T, S, p) # -> mol_gas / kg
    z = abn(gas) # -> mol_gas / mol
    return Ceq + A * z

uaModel = TracerModel(ua_func, default_units_in={'gas':None, 'T':'degC', 'S':'permille', 'p':'atm', 'A':'mol/kg'}, default_units_out='mol_g/kg')
```

The function that the `TracerModel` was constructed with can be accessed with `run` and the argument structure of the supplied function:
```
>>> uaModel.run('Ar', 10, 0, 1, 1e-5)
<PAGOSQuantity(1.74364437e-05, 'mole_Ar / kilogram')>
```
### Fitting models
To fit the created `TracerModel`, we need to supply it with data. For now, let us imagine we have one sample in which we measured the following noble gas concentrations, salinity and atmospheric pressure:

$$
\begin{aligned}
\mathrm{He} &= (2.93\, \pm\, 0.02) \times10^{-9}\, \mathrm{mol/kg}\\
\mathrm{Ne} &= (1.16\, \pm\, 0.01) \times10^{-8}\, \mathrm{mol/kg}\\
\mathrm{Ar} &= (1.67\, \pm\, 0.01) \times10^{-5}\, \mathrm{mol/kg}\\
\mathrm{Kr} &= (3.68\, \pm\, 0.02) \times10^{-9}\, \mathrm{mol/kg}\\
\mathrm{Xe} &= (5.08\, \pm\, 0.06) \times10^{-10}\, \mathrm{mol/kg}\\
S &= 23.4\, \mathrm{g/kg}\\
p &= 1.00\, \mathrm{atm}
\end{aligned}
$$
We can use the `fit` method of `TracerModel` to find the set of remaining model parameters (in this case `A` and `T`) which best reproduce our measurements:
```py
fixed = {"S":23, "p":1}
init_guesses = {"T":10, "A":0}
noblegases = ['He', 'Ne', 'Ar', 'Kr', 'Xe']
obs_NGs = np.array([2.93e-9, 1.16e-8, 1.67e-5, 3.68e-9, 5.08e-10])
err_NGs = np.array([2e-11, 1e-10, 1e-7, 2e-11, 6e-12])

fit = uaModel.fit(fixed_regressors=fixed,
                  regressors_to_fit=init_guesses, 
                  tracers=noblegases,
                  obs_tr=obs_NGs, 
                  obs_tr_errs=err_NGs)
```
The result is a `MinimizerResult` object from [LMFIT](https://lmfit.github.io/lmfit-py/). The fitted values can be accessed via the `params` attribute, and can be nicely displayed thus:
```
>>> fit.params.pretty_print()
Name     Value   Min   Max    Stderr    Vary    Expr    Brute_Step
A    0.0002049  -inf   inf 2.425e-06    True    None          None
S           23  -inf   inf         0   False    None          None
T        10.14  -inf   inf    0.1271    True    None          None
p            1  -inf   inf         0   False    None          None
```

#TODO NEXT: fit_dataframe 