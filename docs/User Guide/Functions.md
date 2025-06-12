# Functions
## Gas and Water Calculations
PAGOS supplies a number of functions to calculate properties of water and dissolved gases therein,
in the `water` and `gas` modules. They are summarised below.

| Module     | Function              | Calculates                                                                   |
| ---------- | --------------------  | ---------------------------------------------------------------------------- |
| `water.py` | `calc_dens`           | Density $\rho(T, S)$ of water                                                |
|            | `calc_dens_Sderiv`    | $d\rho/ dS$                                                                  |
|            | `calc_dens_Tderiv`    | $d\rho/ dT$                                                                  |
|            | `calc_kinvisc`        | Kinematic viscosity $\nu(T, S)$ of water                                     |
|            | `calc_vappres`        | Vapour pressure $p_v(T)$ over water                                          |
|            | `calc_vappres_Tderiv` | $dv_p/ dT$                                                                   |
| `gas.py`   | `calc_Sc`             | Schmidt number $\mathrm{Sc}(T, S)$ of a gas in water                         |
|            | `calc_Ceq`            | Equilibrium concentration $C^\mathrm{eq}(T, S, p)$ of a gas in water         |
|            | `calc_dCeqdp`         | $dC^\mathrm{eq}/dp$                                                          |
|            | `calc_dCeqdS`         | $dC^\mathrm{eq}/dS$                                                          |
|            | `calc_dCeqdT`         | $dC^\mathrm{eq}/dT$                                                          |
|            | `calc_solcoeff`       | Solubility coefficient of a gas                                              |

PAGOS also provides some getters for gas _properties_:

| Module     | Function | Calculates                                 |
| ---------- | -------- | ------------------------------------------ |
| `gas.py`   | `abn`    | Abundance of gas in the atmosphere         |
|            | `ice`    | Ice-water partitioning coefficient of gas  |

These are the functions that provide the backbone for the builtin gas exchange models in PAGOS. They are all unit-aware
and "possibly iterable", explained in the next sections.

## Unit-aware
All of the above functions can handle unit-laden inputs (i.e. [`Quantity`](../Quantities and Magnitudes) objects), and can work just as well without units being specified, where a default set of units is assumed. For example, the following calculations all produce the same result:
```py
from pagos import Q
from pagos.gas import calc_kinvisc

nu1 = calc_kinvisc(10, 8)                               # <- default units of degC and permille assumed
nu2 = calc_kinvisc(Q(10, 'degC'), Q(8, 'permille'))     # <- units of degC and permille explicitly given
nu3 = calc_kinvisc(Q(283.15, 'K'), Q(8, 'permille'))    # <- units of Kelvin and permille explicitly given
nu4 = calc_kinvisc(10, Q(0.8, 'percent'))               # <- mixture of default and specified units
```

The result of a PAGOS function is usually also a `Quantity`, and its magnitude can be extracted following
[these instructions](../Quantities and Magnitudes#returning-magnitudes).

## Possibly Iterable
All of the above functions are wrapped in using a decorator, `@_possibly_iterable`. This means that the 
functions can take in iterables as their arguments as well as single values (one can imagine how this
becomes useful when dealing with sets of data rather than one observation). Take the Schmidt number
calculation:
```py
from pagos import Q
from pagos.gas import calc_Sc
from pagos.constants import NOBLEGASES # ['He', 'Ne', 'Ar', 'Kr', 'Xe']

temp, sal = Q(5, 'degC'), Q(8, 'permille')
print(calc_Sc('He', temp, sal))
# -> 297.61809773243925 dimensionless
print(calc_Sc(NOBLEGASES, temp, sal))
# -> [297.61809773243925 588.5528683811965 941.6378411255967 1502.8591951053966 1962.5736535043864] dimensionless
```

Note that the units (here "`dimensionless`") are preserved. We can also control _which_ parameter(s) should be iterated
over, with the `possit` keyword (meaning <ins>poss</ins>ibly <ins>it</ins>erable):
```py
temps_array = Q([5, 10, 15, 20, 25], 'degC')
print(calc_Sc('He', temps_array, sal, possit=1)) # <- possit=1 declares second argument is the one to be iterated over
print(calc_Sc(NOBLEGASES, temps_array, sal, possit=(0, 1))) # both first and second argument are iterated over
print(calc_Sc('He', T=temps_array, S=sal, possit='T')) # specification of iteration over keyword argument

# -> [297.61809773243925 234.4123488284571 187.5948551837817 152.21814937390133 125.02497969303147] dimensionless
# -> [297.61809773243925 452.5787391226707 550.7956064489289 636.8687708031207 618.482428796838] dimensionless
# -> [297.61809773243925 234.4123488284571 187.5948551837817 152.21814937390133 125.02497969303147] dimensionless
```

!!!warning
    As shown above, this functionality works when specifying iteration over arguments _or_ keyword arguments. However, it does not work with both! A future version of PAGOS may include such a system, where one could conceivably write something like `possit=(0, 1, 'S')`.