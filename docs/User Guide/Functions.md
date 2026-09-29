# Functions
## Gas and Water Calculations
PAGOS supplies a number of functions to calculate properties of water and dissolved gases therein,
in the `water` and `gas` modules. They are summarised below.

| Module     | Function              | Calculates                                                                           |
|------------| ----------------------|--------------------------------------------------------------------------------------|
| `water.py` | `calc_dens`           | Density $\rho(T, S)$ of water                                                        |
|            | `calc_dens_Sderiv`    | $d\rho/ dS$                                                                          |
|            | `calc_dens_Tderiv`    | $d\rho/ dT$                                                                          |
|            | `calc_kinvisc`        | Kinematic viscosity $\nu(T, S)$ of water                                             |
|            | `calc_vappres`        | Vapour pressure $p_v(T)$ over water                                                  |
|            | `calc_vappres_Tderiv` | $dv_p/ dT$                                                                           |
| `gas.py`   | `calc_Sc`             | Schmidt number $\mathrm{Sc}(T, S)$ of a gas in water                                 |
|            | `calc_Ceq`            | Equilibrium concentration $C^\mathrm{eq}(T, S, p)$ of a gas in water                 |
|            | `calc_Cstar`          | Concentration $C^\ast(T, S)$ of a given gas in water at 1 atm moist air pressure     |

PAGOS also provides some getters for gas _properties_:

| Module     | Function | Calculates                                 |
| ---------- | -------- | ------------------------------------------ |
| `gas.py`   | `abn`    | Abundance of gas in the atmosphere         |
|            | `molvol` | Molar volume of a gas                      |
|            | `molmass`| Molar mass of a gas                        |

These are the functions that provide the backbone for the builtin gas exchange models in PAGOS. They are all unit-aware, as explained in the next sections.

## Unit-aware
All of the above functions can handle unit-laden inputs (i.e. [`PAGOSQuantity`](../Quantities and Magnitudes) objects), and can work just as well without units being specified, where a default set of units is assumed. For example, the following calculations all produce the same result:
```py
from pagos import pQ
from pagos.gas import calc_kinvisc
# default units of degC and permille assumed
nu1 = calc_kinvisc(10, 8)
# units of degC and permille explicitly given
nu2 = calc_kinvisc(pQ(10, 'degC'), pQ(8, 'permille'))
# units of Kelvin and permille explicitly given
nu3 = calc_kinvisc(pQ(283.15, 'K'), pQ(8, 'permille'))
# mixture of default and specified units
nu4 = calc_kinvisc(10, pQ(0.8, 'percent'))               
```

The result of a PAGOS function is also a `PAGOSQuantity`, and its magnitude can be extracted with `.value`.

## Gas-specific functions
The functions provided by the `gas` module are actually wrappers around methods of built-in `Gas` objects. This is demonstrated in the following:
```py
from pagos.gas import calc_Ceq, Ar
print(type(Ar))
# -> <class 'pagos.gas.Gas'>
print(calc_Ceq('Ar', 5, 10, 1))
# -> 1.82538394e-05 mole_Ar / kilogram
print(calc_Ceq(Ar, 5, 10, 1))
# -> 1.82538394e-05 mole_Ar / kilogram
print(Ar.calc_Ceq(5, 10, 1))
# -> 1.82538394e-05 mole_Ar / kilogram
```
Below is a table of the different ways to access these functions:


| Function in `gas` module | Method/property of `Gas` object |
|--------------------------|---------------------------------|
| `calc_Sc(gas, T, S)`     | `Gas.calc_Sc(T, S)`             |
| `calc_Ceq(gas, T, S)`    | `Gas.calc_Ceq(T, S, p)`         |
| `calc_Cstar(gas, T, S)`  | `Gas.calc_Cstar(T, S)`          |
| `abn(gas)`               | `Gas.abundance`                 |
| `molvol(gas)`            | `Gas.molar_volume`              |
| `molmass(gas)`           | `Gas.molar_mass`                |

## Built-in gases
The current available gases in PAGOS are:
- Helium (`He`)
- Neon (`Ne`)
- Argon (`Ar`)
- Krypton (`Kr`)
- Xenon (`Xe`)
- CFC-12 (`CFC12`)
- SF<sub>6</sub> (`SF6`)
- N2 (`N2`)