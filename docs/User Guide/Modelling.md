# Modelling
The real power of PAGOS is in its gas exchange modelling capabilities. PAGOS allows for easy user-definition of gas exchange models.

## Writing your own functions
 Say we wanted to implement a simple unfractionated excess air (UA) model (that is, equilibrium concentration $C^\mathrm{eq}$ "topped up" with an excess air component):

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
A `DimensionalityError` was thrown here because:
- `A` was passed as a float, and is thus _dimensionless_,
- `A * z` therefore evaluates to a quantity with units of $[A]\times[z]=[z]=\mathrm{mol_{Ar}/mol}$,
- but `Ceq` has units of $\mathrm{mol_{Ar}/kg}$,
- the $\mathrm{kg}$ and $\mathrm{mol}$ in the denominators of the units are incommensurable!

Rightfully, the user is refused this calculation. The user could get around this by always passing `A` with units compatible with `mol/kg`:
```py
correct1 = ua_func('Ar', 10, 0, 1, pQ(1e-5, 'mol/kg'))
print(correct1)
# -> 1.74364437e-05 mole_Ar / kilogram
correct2 = ua_func('Ar', 10, 0, 1, pQ(0.01, 'umol/g'))
print(correct2)
# -> 1.74364437e-05 mole_Ar / kilogram
```
However, this is quite tedious, both to type every time, and to remember! Instead, the user can wrap the function just once, and all calls to the function will thenceforth handle units automatically. This is detailed in the next section.
## Automatic unit handling
### `@unit_aware`
Notice that in the the above example, we were able to just use the literals `10`, `0`, `1` for the first arguments `T`, `S`, `p`, because these are passed into `calc_Ceq`, which has `default_units_in`—that is, we did not need to pass in `PAGOSQuantity`s. We can also provide our own `default_units_in` for _our_ arguments:
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

With this, we can use our newly defined function as we do the built-ins from the `gas` or `water` modules:
```py
# works with all literals, based on default_units_in
print(ua_func('Ar', 10, 0, 1, 1e-5))
# works with PAGOSQuantity arguments
print(ua_func('He', pQ(10, 'degC'), pQ(0, 'g/kg'), pQ(1, 'atm'), pQ(1e-5, 'mol/kg')))
# works with mixture of arguments
print(ua_func('CFC-12', 10, 0, 1, pQ(0.01, 'umol/g')))
```

### `None` vs. `"dimensionless"/""`
It is important to note the difference between `None` and `"dimensionless"` or simply an empty unit string `""`. `None` means that the object passed to the function, whether a `PAGOSQuantity` or regular literal, will have its units (or lack thereof) _ignored_. `"dimensionless"`/`""`, on the other hand, will convert the argument into a `PAGOSQuantity` with the units `"dimensionless"`. See the following examples:

/// html | div[style='float: left; width: 48%;']
```py
from pagos.core import unit_aware, pQ

@unit_aware({'gas':None, 'A':None}, None)
def f(gas, A):
    return A

print(f('Ar', 0.2))
# -> 0.2
print(f('Ar', pQ(0.2, 'dimensionless')))
# -> 0.2 dimensionless
print(f('Ar', pQ(20, 'percent')))
# -> 20 percent

@unit_aware({'gas':None, 'A':'dimensionless'}, None)
def g(gas, A):
    return A

print(g('Ar', 0.2))
# -> 0.2 dimensionless
print(g('Ar', pQ(0.2, 'dimensionless')))
# -> 0.2 dimensionless
print(g('Ar', pQ(20, 'percent')))
# -> 20 percent
```
///
/// html | div[style='float: right; width: 48%;']
```py
@unit_aware({'gas':None, 'A':None}, 'dimensionless')
def h(gas, A):
    return A

print(h('Ar', 0.2))
# -> pagos.exceptions.NoUnitsToConvertError
# Fails because the return value was never turned into a Quantity ('A':None), 
# but the units_out argument means that PAGOS attempts to find a to()-method
# that does not exist!
print(h('Ar', pQ(0.2, 'dimensionless')))
# -> 0.2 dimensionless
print(h('Ar', pQ(20, 'percent')))
# -> 0.2 dimensionless

@unit_aware({'gas':None, 'A':'dimensionless'}, 'dimensionless')
def i(gas, A):
    return A

print(i('Ar', 0.2))
# -> 0.2 dimensionless
print(i('Ar', pQ(0.2, 'dimensionless')))
# -> 0.2 dimensionless
print(i('Ar', pQ(20, 'percent')))
# -> 0.2 dimensionless
```
///

/// html | div[style='clear: both;']
///

## `TracerModel` objects
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

uaModel = TracerModel(ua_func, 
                      default_units_in={'gas':None, 'T':'degC', 'S':'permille', 'p':'atm', 'A':'mol/kg'}, 
                      default_units_out='mol_g/kg')
```

The function that the `TracerModel` was constructed with can be accessed with `run` and the argument structure of the supplied function:
```
>>> uaModel.run('Ar', 10, 0, 1, 1e-5)
<PAGOSQuantity(1.74364437e-05, 'mole_Ar / kilogram')>
```
## Fitting models
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

## Fitting models to `DataFrame`
Normally, you will have more than just one sample to fit, usually in the form of a table. `TracerModel`s can read [pandas](https://pandas.pydata.org/) `DataFrame` objects and fit all the rows using the `fit_dataframe` method.
Let's say we have the following data:

```
>>> import pandas as pd
>>> measdata = pd.read_csv('path/to/data/table')
>>> measdata.head()
         He   He err       Ne   Ne err ...       Xe   Xe err      S     p
0  3.67e-09 2.31e-10 1.41e-08 1.65e-09 ... 5.08e-10 9.97e-11  20.00  1.02
1  2.93e-09 2.38e-11 1.16e-08 8.04e-11 ... 5.09e-10 5.65e-12   6.54  1.00
2  3.59e-09 2.98e-11 1.42e-08 2.82e-10 ... 6.23e-10 1.22e-11   2.34  0.97
3  2.28e-09 3.21e-11 9.51e-09 1.73e-10 ... 5.61e-10 5.43e-12  13.69  0.99
4  2.78e-09 5.33e-11 1.12e-08 1.28e-10 ... 5.25e-10 2.87e-12  10.11  1.01
```

To fit all these samples (rows) with one command, we can use `fit_dataframe`, with much the same structure as `fit`:

```py
init_guesses = {"T":10, "A":0}
noblegases = ['He', 'Ne', 'Ar', 'Kr', 'Xe']

fitdf = uaModel.fit_dataframe(data=measdata,
                              regressors_to_fit=init_guesses, 
                              tracers=noblegases)
```
This produces the following output:
```
FIT WARNING: No columns found for the unit on He, Ne, Ar, Kr and Xe, assuming the default units of the function return (mol_g/kg).
FIT WARNING: No columns found for the unit of S and p, assuming the default units in for the function (permille and atm).
100%|████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 20/20
```
The warnings explain that the user did not explicitly give unit information in the columns of the DataFrame, but PAGOS will attempt to infer them from the `TracerModel` being fitted. The result of the fit is itself a `DataFrame`:
```
>>> fitdf.head()
           T     T err         A     A err
0   13.00937  0.136169  0.000335  0.000002
1  14.331123       0.0  0.000176       0.0
2   8.758895       0.0  0.000297       0.0
3   8.799489       0.0  0.000062       0.0
4  12.621208       0.0  0.000149       0.0
```
In this case, the example data was generated exactly from the UA model, and the first sample's data was then artificially edited - this is why the error is extremely small for samples 1-4, but more realistic for sample 0.