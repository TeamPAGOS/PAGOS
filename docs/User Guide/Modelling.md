# Modelling
The real power of PAGOS is in its gas exchange modelling capabilities. PAGOS comes packaged with a number of built-in
gas exchange models (found in the module `builtin_models`), but the user may also define whatever model they like (as long as it can be expressed in a Python function!).

## Functions and the `GasExchangeModel`
Here, we look at implementing a simple unfractionated excess air (UA) model (that is, equilibrium concentration
$C^\mathrm{eq}$ "topped up" with an excess air component). The details of this model can be found in [Jung & Aeschbach
2018](https://www.sciencedirect.com/science/article/pii/S1364815216307150). The model is written mathematically as

$$
C_\mathrm{gas}^\mathrm{UA}(T, S, p, A) = C_\mathrm{gas}^\mathrm{eq}(T, S, p) + A\cdot z,
$$

where $A$ is in the units of $C^\mathrm{eq}_\mathrm{gas}$ and $z$ is the atmospheric abundance of the gas. Using the
[functions](../Functions) provided by PAGOS we can express this as the following Python function:

```py
from pagos.gas import calc_Ceq, abn
def ua_model(gas, T, S, p, A):
    Ceq = calc_Ceq(gas, T, S, p)
    z = abn(gas)
    return Ceq + A * z
```

!!!info "Important"
    The first argument of _any_ function to be used in the modelling framework of PAGOS must be called `gas` and should
    take the string-name of the gas for which the model should be run. For example, in the function above, running
    `ua_model('Ne', 10, 30, 1, 2e-5)` calculates $C^\mathrm{UA}$ for **neon** at 10 &deg;C, 30 &permil;, 1 atm and 0.00002 cc/g of excess air.

So far, so boring. However, PAGOS provides an object, `GasExchangeModel`, that will handle this function for fitting,
automatically taking care things like unit conversion. The constructor looks like this:
```
GasExchangeModel(<function>, <default units in>, <units out>)
```
where `<function>` is the Python function expressing the model of interest, `<default units in>` are the units that will
be assumed are associated with the arguments of `<function>`, if none are provided by the user, and `<units out>` are
the units of the value returned by the model. Let's take the UA example again:
```py
from pagos import GasExchangeModel
ua_gem = GasExchangeModel(ua_model, ('degC', 'permille', 'atm', 'cc/g'), 'cc/g')
#                            ^         ^         ^         ^      ^        ^
#                            |         |         |         |      |        |
#                            |     unit of T     |     unit of p  |   output unit
#                         function           unit of S        unit of A
```
The default units in must match the signature of the original function. Here, it's `(T, S, p, A)`. Note that the `gas`
argument is not included, and is automatically ignored by PAGOS when setting up the default units (the argument `gas`
takes a string value, which of course has no units).

The `GasExchangeModel` can now be _run_ with user-provided input parameters:
```py linenums="1"
from pagos import Q
print(ua_gem.run('Ne', 10, 30, 1, 2e-5))
# -> 1.7030653005762064e-07 cubic_centimeter / gram
print(ua_gem.run('Ne', Q(283.15, 'K'), Q(30, 'permille'), Q(1013.25, 'hPa'), Q(2e-5, 'cc/g')))
# -> 1.7030653005762064e-07 cubic_centimeter / gram
print(ua_gem.run('Ne', 283.15, 30, 1013.25, 2e-5,
                 units_in=['K', 'permille', 'hPa', 'cc/g']))
# -> 1.7030653005762067e-07 cubic_centimeter / gram
print(ua_gem.run('Ne', 283.15, 30, 1013.25, 2e-5,
                 units_in=['K', 'permille', 'hPa', 'cc/g'],
                 units_out='m^3/kg'))
# -> 1.703065300576207e-10 meter ** 3 / kilogram
```
Above is demonstrated that `GasExchangeModel`s are automatically unit-aware, and the units can be handled
in a number of ways. On line 2, we see that the default units we provided when we defined `ua_gem` are
used. On line 4, we use quantities already laden with units, using the explicit `Q` constructor. On line
6, we specify the units of the input parameters in a separate argument, `units_in`. On line 8, we do the
same thing, and also convert the _output_ into units specified by us.
The differences in the last digits the results are due to floating point errors.

## Fitting Models
Of course, we do not want only to perform forward-models, but inverse too. This functionality is provided
by the `fit` method of `GasExchangeModel`. A better walkthrough can be found in the `example scripts` folder, but here is a brief explanation. The `GasExchangeModel.fit()` method can be used to fit a number of parameters of a gas exchange model using a least-squares minimisation. Here is an example using the Belgium data (from [Jung and Aeschbach 2018](https://doi.org/10.1016/j.envsoft.2018.02.004)) taken from the `example scripts/example data` folder:

```py
import pandas as pd
gases_used = ['Ne', 'Ar', 'Kr', 'Xe']

# Data import
# These data are from Jung and Aeschbach 2018 (https://www.sciencedirect.com/science/article/pii/S1364815216307150)
pangadata = pd.read_csv('example scripts/Example Data/Complete_Input_Data_Samples_Belgium.CSV', sep=',')

fit_UA = ua_gem.fit(pangadata,                          # the data as a Pandas DataFrame
                    to_fit=['T', 'A'],                  # the arguments of the model we would like to fit
                    init_guess=[Q(1, 'degC'), 1e-5],    # the initial guesses for the parameters to be fit
                    tracers_used=gases_used,            # the tracers used for the fitting procedure
                    constraints=[[-10, 50], [0, 1e-2]], # any (optional) constraints we might want to place on our fitted parameters
                    tqdm_bar=True)                      # whether to display a progress bar
print('Fit of UA model:')
print(fit_UA)

# -> Fit of UA model:
#                        T_recharge                                           A
#    0     7.1+/-0.9 degree_Celsius     0.0023+/-0.0006 cubic_centimeter / gram
#    1     5.0+/-0.4 degree_Celsius   0.00348+/-0.00029 cubic_centimeter / gram
#    2     5.0+/-0.4 degree_Celsius   0.00098+/-0.00022 cubic_centimeter / gram
#    ...
```
The arguments are explained in the method docstrings and on the right hand side above. Note here that the init_guess arguments do NOT have to be Quantity objects, although they can be for clarity/safety, if you want. When units are omitted, the `default_units_in` passed to the `GasExchangeModel()` constructor are used. So in this case, `1e-5` becomes `1e-5 cc/g`.