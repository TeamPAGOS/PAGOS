"""
PAGOS
=====

Python Analysis of Groundwater and Ocean Samples.

Provides
--------
    1. Q object, a number with a value, uncertainty and unit.
    2. Functions for calculating the properties of seawater and dissolved gases in seawater.
    3. Objects for fitting the parameters of pre- or user-defined gas exchange models to gas tracer data.

Notes on Quantities, units and the UnitRegistry `u`:
--------
Dimensioned quantites can be defined by the user using the `Q(<value>, <unit>, <error>)` constructor, which creates a Pint `Quantity` object:
    
    from pagos import Q
    myquantity1 = Q(15, 'mm')
    myquantity2 = Q(22.0, 'km/s', 0.3)
    myquantity3 = Q(np.inf, 'J')
    
Note that the above construction is a wrapper around the constructor `Quantity(<magnitude>, <unit>)` from Pint.
In Pint, all units come from a `UnitRegistry` object, and the same unit from different registries will be flagged as incompatible.
For this reason, PAGOS has its own registry, `u`, from which all units are derived (when a string `...` is passed as the unit argument to `Q`, the actual unit is `u.Unit(...)`)
"""


__version__ = '0.5.3'
__author__ = 'Stanley Scott and Chiara-Marlen Hubner'

# for ease of use, these could change later
from .core import u, Q
from .gas import calc_Ceq, calc_dCeq_dT, calc_Sc
from .water import calc_dens, calc_kinvisc, calc_vappres
from .modelling import GasExchangeModel

from . import core
from . import constants
from . import gas
from . import water
from . import water
from . import modelling
from . import builtin_models
from . import plotting