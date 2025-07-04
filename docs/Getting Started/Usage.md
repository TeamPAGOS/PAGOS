# Usage
This is a relatively abridged version of the information you can find in `example scripts`.
## How quantities are defined in PAGOS
This package is designed with a number of "numerical safeguards". Quantities used in PAGOS may contain units, and uncertainties. Functions in PAGOS are designed for use with `Quantity` objects from [Pint](https://pint.readthedocs.io/en/stable/), but can also be used with regular Python datatypes. The following code produces such a quantity representing the speed 11.2 m/s.
```py
from pagos import Q
mySpeed = Q(11.2, 'm/s')
print(mySpeed)
# -> 11.2000 meter / second
```
Those familiar with Pint will recognise `Q()` as a shortcut for `pint.UnitRegistry.Quantity()`. This is the PAGOS-safe version though, as it will always refer to the universal `UnitRegistry` defined in `pagos.core`.

## Water property calculations
The properties of seawater and various gases can be calculated with the `water` and `gas` modules. For example, calculating the density of, kinematic viscosity of and vapour pressure over water at a given temperature and salinity:
```py
from pagos import water as pwater
from pagos import Q

myTemp1 = Q(10, 'degC')
mySal1 = Q(30, 'permille')

myDensity1 = pwater.calc_dens(myTemp1, mySal1)
myDensity2 = pwater.calc_dens(10, 30) # <- default units of degC and permille assumed

print(myDensity1)
print(myDensity2)
# -> 1023.0511189339445 kilogram / meter ** 3
# -> 1023.0511189339445 kilogram / meter ** 3
```
We can see that the water property function have default, assumed units for any given float arguments (you can see these in the docstrings of the respective functions). PAGOS will also automatically convert units of a different kind:

```py
myTemp2 = Q(283.15, 'K')
mySal2 = Q(3, 'percent')

myDensity3 = pwater.calc_dens(myTemp2, mySal2)

print(myDensity3)
# -> 1023.0511189339445 kilogram / meter ** 3

```

Other properties available to be calculated for water are vapour pressure over the water and kinematic viscosity of the water, given temperature and salinity:
```py
myVapourPres = pwater.calc_vappres(myTemp1)
myKinVisc = pwater.calc_kinvisc(myTemp1, mySal1)
print(myVapourPres)
print(myKinVisc)
# -> 12.272370555643239 millibar
# -> 1.3516218130144556e-06 meter ** 2 / second
```
## Gas property calculations 
Much like the bulk water properties, properties of gases dissolved in water can also be calculated, namely the equilibrium concentration and the Schmidt number at given temperature, salinity and overlying pressure. Also like the functions in the  `water` module, the `gas` module functions have default assumed units which may be overriden by the user. See how all of the following calculations return the same result:
```py
from pagos import gas as pgas, Q
myTemp, myTempC, myTempK = 20, Q(20, 'degC'), Q(293.15, 'K')
mySal, mySalpm, mySalpc = 32, Q(32, 'permille'), Q(3.2, 'percent')
myPres, myPresatm, myPreshPa = 1, Q(1, 'atm'), Q(1013.25, 'hPa')

Ceq1 = pgas.calc_Ceq('Ne', myTemp, mySal, myPres)
Ceq2 = pgas.calc_Ceq('Ne', myTempC, mySalpm, myPresatm)
Ceq3 = pgas.calc_Ceq('Ne', myTempK, mySalpc, myPreshPa)
Sc = pgas.calc_Sc('Ne', myTemp, mySal)

print('Ceq1(Ne):', Ceq1)
print('Ceq2(Ne):', Ceq2)
print('Ceq3(Ne):', Ceq3)
print('Sc(Ne):', Sc)
# -> Ceq1(Ne): 1.5676847690725347e-07
# -> Ceq2(Ne): 1.5676847690725347e-07
# -> Ceq3(Ne): 1.567684769072535e-07
# -> Sc(Ne): 300.07687253959057 dimensionless
```
Multiple gas properties may be calculated all at once (this is also true of water properties):
```py
Ceqs = pgas.calc_Ceq(['Ne', 'Ar', 'N2', 'CFC12'], 20, 32, myPreshPa)
print('Ceq(Ne, Ar, N2, CFC12) =', Ceqs, 'ccSTP/g')
# -> Ceq(Ne, Ar, N2, CFC12) = [1.56768477e-07 2.54842193e-04 9.60586197e-03 2.68527581e-11] ccSTP/g
```

Note how `calc_Ceq` returns only a `float` by default, not a unit-bound `Quantity`. This is in contrast to most other functions in PAGOS, including `calc_Sc`, and is set up this way to increase speed when performing inverse modelling(1). The `float` returned is the value of the equilibrium concentration in units of cc/g, but without the units explicitly returned with it. The unit can be changed, and optionally returned, using the `unit` and `ret_quant` arguments:
{ .annotate }

1. This is set to be changed in a future version of PAGOS; after great speed improvements, this feature is no longer necessary.

```py
Ceqsmolkg = pgas.calc_Ceq('Ne', 20, 32, myPreshPa, 'mol/kg')
Ceqsmolcc = pgas.calc_Ceq('Ne', 20, 32, myPreshPa, 'mol/cc', ret_quant=True)
print('Ceq(Ne) =', Ceqsmolkg)
print('Ceq(Ne) =', Ceqsmolcc)
# -> Ceq(Ne) = 6.9908309248701225e-09
# -> Ceq(Ne) = 7.147959263640384e-12 mole / cubic_centimeter
```
Note also here that the different units that one can return are incommensurable with each other (mol/kg has different dimensions to mol/cc). This is another reason why `calc_Ceq` does not returned a dimensioned object by default - functions in PAGOS which do automatically return dimensioned quantities do so by way of a wrapper, but `calc_Ceq` cannot be wrapped due to the many incommensurable possibilities of return units.

## Creating and fitting models
The real power of PAGOS is in its gas exchange modelling capabilities. PAGOS allows for simple user-definition of gas exchange models. Say we wanted to implement a simple unfractionated excess air (UA) model (that is, equilibrium concentration $C^\mathrm{eq}$ "topped up" with an excess air component):

$$
C_\mathrm{gas}^\mathrm{UA}(T, S, p, A) = C_\mathrm{gas}^\mathrm{eq}(T, S, p) + A\cdot z,
$$

where $A$ is in the units of $C^\mathrm{eq}_\mathrm{gas}$ and $z$ is the atmospheric abundance of the gas. We can implement it very simply like this:
```py
from pagos import gas as pgas
from pagos.modelling import GasExchangeModel
def ua_model(gas, T, S, p, A):
    Ceq = pgas.calc_Ceq(gas, T, S, p)
    z = pgas.abn(gas)   # <- pagos.gas.abn(G) returns the dimensionless atmospheric abundance of G
    return Ceq + A * z
UAModel = GasExchangeModel(ua_model, ('degC', 'permille', 'atm', 'cc/g'), 'cc/g')
```
The arguments to `GasExchangeModel()` are the user-defined function describing the model (`ua_model` above), a tuple of default input units (`('degC', 'permille', 'atm', 'cc/g')` above) and one default output unit (`'cc/g'` above). The default input units correspond to the assumed units of the arguments of the model function (`(T, S, p, A)` above). The output units are those in which the result of the model is expressed. To calculate the result of a model for a given gas, use the `run()` method of `GasExchangeModel`. Note that they are **default** units, but can be overridden:
```py
# no given units, default units assumed
myResult1 = UAModel.run('Ne', 10, 30, 1, 5e-4)
# units manually given but are the same as the defaults
myResult2 = UAModel.run('Ne', Q(10, 'degC'), Q(30, 'permille'), Q(1, 'atm'), Q(5e-4, 'cc/g'))
# non-default units included, default units of degC and permille overridden
myResult3 = UAModel.run('Ne', Q(283.15, 'K'), Q(3, 'percent'), 1, 5e-4)

print('Result with no given units:', myResult1)
print('Result with given units matching defaults:', myResult2)
print('Result with overridden units:', myResult3)
# -> Result with no given units: 1.7903293005762066e-07 cubic_centimeter / gram
# -> Result with given units matching defaults: 1.7903293005762066e-07 cubic_centimeter / gram
# -> Result with overridden units: 1.7903293005762066e-07 cubic_centimeter / gram
```
If repeatedly typing the `Q()` constructor isn't to your liking, one can also override default units with the `units_in` argument thus:
```py
myResult4 = UAModel.run('Ne', 283.15, 3, 1, 5e-4, units_in=['K', 'percent', 'atm', 'cc/g'])
print('Result using units_in kwarg:', myResult4)
# -> Result using units_in kwarg: 1.7903293005762066e-07 cubic_centimeter / gram
```

The returned units may also be altered with the units_out keyword argument. Additionally, note in the example below that the `'percent'` in `units_in` is overridden by the explicit `Quantity` object with its already given `'permille'` unit. This is a nice safeguard, but also a good reason **not** to use the `units_in` argument along with `Q()`-based model arguments, as `units_in` will always be silently overridden.
```py
myResult5 = UAModel.run('Ne', 10, Q(30, 'permille'), 1, 5e-4, units_in=['degC', 'percent', 'atm', 'cc/g'], units_out='m^3/kg')
print('Result in using units_out kwarg:', myResult5)
# -> Result in using units_out kwarg: 1.790329300576207e-10 meter ** 3 / kilogram
```

## Inverse Modelling
Parameters of a `GasExchangeModel`'s function can be fitted using data. A better walkthrough can be found in the `example scripts` folder, but here is a brief explanation. The `GasExchangeModel.fit()` method can be used to fit a number of parameters of a gas exchange model using a least-squares minimisation. Here is an example using the Belgium data (from [Jung and Aeschbach 2018](https://doi.org/10.1016/j.envsoft.2018.02.004)) taken from the `example scripts/example data` folder:
```py
from pagos.modelling import fitmodel
import pandas as pd

# Data import
# These data are from Jung and Aeschbach 2018 (https://www.sciencedirect.com/science/article/pii/S1364815216307150)
gases_used = ['Ne', 'Ar', 'Kr', 'Xe']
pangadata = pd.read_csv('example scripts/Example Data/Complete_Input_Data_Samples_Belgium.CSV', sep=',')
print('Data from Jung and Aeschbach 2018:')
print(pangadata)

def ua_model(gas, T_recharge, S, p, A):
    Ceq = pgas.calc_Ceq(gas, T_recharge, S, p)
    z = pgas.abn(gas)
    return Ceq + A * z
UAModel = GasExchangeModel(ua_model, ('degC', 'permille', 'atm', 'cc/g'), None)

fit_UA = UAModel.fit(pangadata,                                             # the data as a Pandas DataFrame
                     to_fit=['T_recharge', 'A'],                            # the arguments of the model we would like to fit
                     init_guess=[Q(1, 'degC'), 1e-5],                       # the initial guesses for the parameters to be fit
                     tracers_used=gases_used,                               # the tracers used for the fitting procedure
                     constraints=[[-10, 50], [0, 1e-2]],                    # any (optional) constraints we might want to place on our fitted parameters
                     tqdm_bar=True)                                         # whether to display a progress bar
print('Fit of UA model:')
print(fit_UA)

# -> Fit of UA model
#                        T_recharge                                           A
#    0     7.1+/-0.9 degree_Celsius     0.0023+/-0.0006 cubic_centimeter / gram
#    1     5.0+/-0.4 degree_Celsius   0.00348+/-0.00029 cubic_centimeter / gram
#    2     5.0+/-0.4 degree_Celsius   0.00098+/-0.00022 cubic_centimeter / gram
#    .                 .                                 .
#    .                 .                                 .
#    .                 .                                 .
```
The arguments are explained in the method docstrings and on the right hand side above. Note here that the init_guess arguments do NOT have to be Quantity objects, although they can be for clarity/safety, if you want. When units are omitted, the `default_units_in` passed to the `GasExchangeModel()` constructor are used. So in this case, `1e-5` becomes `1e-5 cc/g`.