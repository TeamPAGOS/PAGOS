# Monte Carlo Fitting
## Foreword
Pagos provides a system whereby Monte Carlo fitting can be performed relatively simply. A balance has been struck between speed of the fitting itself and demands on the user. If you wish to perform lightning-fast MC fitting, PAGOS may not be the best tool. However, if you have, say, 10 models that all require comparison (including MC analysis), PAGOS provides a very easy interface which means you will not have to bother with setting up Monte Carlo boilerplate yourself, and still achieve good results on a relatively short time scale.

## Activating MC fitting
MC fitting can be performed with `TracerModel.fit_dataframe`, by using the `nmc` keyword, standing for the number of desired MC-loops. By default, `nmc` is `0`, which signifies no MC procedure should be performed.

```py
import pandas as pd
from pagos.builtin_models import ua_model

mydata = pd.read_csv('path/to/my/data.csv')
```
Let's imagine we have the following data for ten samples:
```
        He   He err       Ne   Ne err       Ar   Ar err       Kr   Kr err       Xe   Xe err        S    S err        p S units p units
0 9.11e-09 9.71e-11 3.33e-08 3.01e-10 2.86e-05 5.38e-07 5.22e-09 9.98e-11 6.42e-10 9.52e-12 8.09e-01 1.00e-02 1.00e+00    g/kg     atm
1 4.09e-09 4.36e-11 1.70e-08 1.53e-10 2.58e-05 4.85e-07 5.28e-09 1.01e-10 6.63e-10 9.83e-12 1.28e+00 1.00e-02 9.91e-01    g/kg     atm
2 3.53e-09 3.77e-11 1.49e-08 1.35e-10 2.49e-05 4.68e-07 5.36e-09 1.02e-10 7.02e-10 1.04e-11 5.57e-01 1.00e-02 9.88e-01    g/kg     atm
3 4.35e-09 4.63e-11 1.80e-08 1.63e-10 2.63e-05 4.95e-07 5.30e-09 1.01e-10 6.60e-10 9.80e-12 5.27e-01 1.00e-02 9.98e-01    g/kg     atm
4 6.42e-09 6.84e-11 2.66e-08 2.41e-10 3.87e-05 7.29e-07 7.55e-09 1.44e-10 8.91e-10 1.32e-11 1.57e-01 1.00e-02 9.81e-01    g/kg     atm
5 3.16e-09 3.36e-11 1.30e-08 1.18e-10 1.99e-05 3.74e-07 4.19e-09 8.01e-11 5.52e-10 8.19e-12 1.05e+00 1.00e-02 1.00e+00    g/kg     atm
6 1.29e-08 1.37e-10 4.95e-08 4.48e-10 4.50e-05 8.46e-07 7.47e-09 1.43e-10 8.19e-10 1.22e-11 1.87e-02 1.00e-02 9.94e-01    g/kg     atm
7 3.94e-09 4.20e-11 1.54e-08 1.39e-10 1.94e-05 3.65e-07 4.10e-09 7.82e-11 5.55e-10 8.24e-12 1.94e+00 1.00e-02 1.01e+00    g/kg     atm
8 3.76e-09 4.01e-11 1.56e-08 1.41e-10 2.44e-05 4.59e-07 5.08e-09 9.71e-11 6.47e-10 9.60e-12 4.47e-01 1.00e-02 9.94e-01    g/kg     atm
9 3.27e-09 3.48e-11 1.31e-08 1.19e-10 1.84e-05 3.47e-07 3.99e-09 7.63e-11 5.48e-10 8.13e-12 9.81e-01 1.00e-02 1.00e+00    g/kg     atm
```
Notice that the amount of information we give here is incomplete: namely, we have not provided unit information for any of the tracer measurements, and there is no error given for `p`. For this last point: in a single `fit` call this would be no problem, as the inner least squares algorithm (`scipy.leastsq` under the hood) cannot handle errors on the non-tracer parameters anyway. However, for MC, we want to vary around these parameters.

We can fit these data in a Monte Carlo fashion by including the `nmc=...` argument, followed by the desired amount of MC loops. Let's try it with 100 loops:
```py
my_fit = ua_model.fit_dataframe(data=mydata,
                                tracers=['He', 'Ne', 'Ar', 'Kr', 'Xe'],
                                regressors_to_fit={'T':10, 'A':0},
                                nmc=100) # <- MC argument
```
This outputs:
```
FIT WARNING: No columns found for the unit on He, Ne, Ar, Kr and Xe, assuming the default units of the function return (mol_gas/kg).
MC WARNING: No columns found for the error on p, setting all such errors to zero.
100%|██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 100/100 [00:55<00:00,  1.79it/s]
Completed fitting DataFrame with 0 ValueErrors and 0 OverflowErrors (100.0% success rate)
```
We got the same warning as with a normal fit (`FIT WARNING` because we provided no units for the tracer measurements), but we also got a new `MC WARNING` because we didn't provide an error on `p`, around which the MC process would draw. This means that it is assumed to be perfectly constrained and the error is set to zero.

Note also that this took quite a while to fit (about a minute for 10 samples x 100 MC fits = 1,000 fits in total). We can reasonably expect 1,000 MC fits to take 10 minutes, and 10,000 to take a few hours. Again, this is partly because PAGOS prioritises convenience of model creation over lightning-fast optimisation. However, these data happen to have been generated from a CE model, not a UA model, and slow fitting is also a symptom of the model perhaps being innapropriate to fit the data!

We may notice this, and decide to try fitting a different model:
```py
from pagos.builtin_models import ce_model

my_better_fit = ce_model.fit_dataframe(..., nmc=100)
```

TODO: carry on this section!