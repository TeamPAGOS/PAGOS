# Non-Multiplicative Quantities
It is possible to run into the issue of non-multiplicative quantities, particularly when dealing with temperature calculations. This is explained well in the [Pint documentation](https://pint.readthedocs.io/en/stable/user/nonmult.html).

PAGOS deals with this by assuming "delta-units" wherever necessary. Consider the following scenario:
```py
from pagos import pQ
sum_temp = pQ(10, 'degC') + pQ(20, 'degC')
```
Should the value of `sum_temp` be:
- (10 + 20) °C = 30 °C?
- (10 °C = 283.15 K) + (20 °C = 293.15 K) = 576.3 K = 303 °C?
- Some other combination?

The answer is ambiguous, so PAGOS must assume one. Namely, if offset-units like °C are involved in ambiguous arithmetic, it assumes that each offending unit is equivalent to a *difference* (°C -> Δ°C). PAGOS will warn the user as such:
```
>>> sum_temp = pQ(10, 'degC') + pQ(20, 'degC')
WARNING: While running your function, arithmetic involving non-multiplicative units came up:
        10 °C + 20 °C.
This is technically ambiguous, and PAGOS will replace the offending units with their delta-counterparts:
        10 Δ°C + 20 Δ°C = 30 Δ°C.
Please check that this is the intended behaviour of your function!
To disable this warning, run: `set_warn_nonmult(False)` before your code.
```
As detailed by the error message, `pagos.core.set_warn_nonmult` can be used to disable these warnings.

!!!Note
    Δ°C is basically the same as K, i.e. (x °C - y °C) := (x - y) Δ°C = (x - y) K.