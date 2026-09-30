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
        He   He err       Ne   Ne err       Ar   Ar err       Kr   Kr err       Xe   Xe err        S    S err        p    p err S units p units
0 8.80e-09 9.15e-11 3.29e-08 1.77e-10 2.95e-05 4.88e-07 5.27e-09 6.64e-11 6.29e-10 8.71e-12 1.81e+00 1.00e-02 9.98e-01 5.00e-01    g/kg     atm
1 4.03e-09 4.20e-11 1.69e-08 9.06e-11 2.63e-05 4.34e-07 5.43e-09 6.84e-11 6.91e-10 9.57e-12 3.36e-01 1.00e-02 9.78e-01 5.00e-01    g/kg     atm
2 1.82e-08 1.89e-10 7.02e-08 3.77e-10 6.51e-05 1.08e-06 1.02e-08 1.29e-10 1.02e-09 1.41e-11 1.66e+00 1.00e-02 9.94e-01 5.00e-01    g/kg     atm
3 5.44e-09 5.66e-11 2.25e-08 1.21e-10 3.24e-05 5.35e-07 6.35e-09 8.00e-11 7.67e-10 1.06e-11 4.93e-02 1.00e-02 9.91e-01 5.00e-01    g/kg     atm
4 4.60e-09 4.79e-11 1.90e-08 1.02e-10 2.84e-05 4.69e-07 5.71e-09 7.19e-11 7.01e-10 9.70e-12 2.06e+00 1.00e-02 9.86e-01 5.00e-01    g/kg     atm
5 5.88e-09 6.11e-11 2.46e-08 1.32e-10 3.62e-05 5.98e-07 7.12e-09 8.96e-11 8.63e-10 1.20e-11 9.00e-02 1.00e-02 9.93e-01 5.00e-01    g/kg     atm
6 6.76e-09 7.04e-11 2.84e-08 1.52e-10 4.20e-05 6.94e-07 8.19e-09 1.03e-10 9.72e-10 1.35e-11 1.37e+00 1.00e-02 9.87e-01 5.00e-01    g/kg     atm
7 4.13e-09 4.30e-11 1.71e-08 9.18e-11 2.70e-05 4.46e-07 5.63e-09 7.09e-11 7.09e-10 9.81e-12 2.30e+00 1.00e-02 9.98e-01 5.00e-01    g/kg     atm
8 4.12e-09 4.28e-11 1.70e-08 9.12e-11 2.61e-05 4.32e-07 5.37e-09 6.77e-11 6.72e-10 9.30e-12 6.75e-01 1.00e-02 1.00e+00 5.00e-01    g/kg     atm
9 5.57e-09 5.79e-11 2.23e-08 1.19e-10 2.66e-05 4.39e-07 5.12e-09 6.45e-11 6.41e-10 8.87e-12 6.67e-01 1.00e-02 9.94e-01 5.00e-01    g/kg     atm
```
Notice that the amount of information we give here is incomplete: namely, we have not provided unit information for any of the tracer measurements.

We can fit these data in a Monte Carlo fashion by including the `nmc=...` argument, followed by the desired amount of MC loops. Let's try it with 100 loops:
```py
ua_model.fit_dataframe(data=mydata,
                       tracers=['He', 'Ne', 'Ar', 'Kr', 'Xe'],
                       regressors_to_fit={'T':10, 'A':0},
                       nmc=100)
```