"""
PAGOS
=====

Python Analysis of Groundwater and Ocean Samples.

Provides
--------
    1. Q object, a number with a value, uncertainty and unit.
    2. Functions for calculating the properties of seawater and dissolved gases in seawater.
    3. Objects for fitting the parameters of pre- or user-defined gas exchange models to gas tracer data.

Notes on units and the UnitRegistry `u`:
--------
    * Any units provided by the user must come from the UnitRegistry `u` used by PAGOS, accessed with:
        >>> from pagos import u

    * Dimensioned quantities defined by the user are then defined using Pint (see <https://pint.readthedocs.io/en/stable/>):
        >>> myquantity1 = 15 * u.mm
    myquantity2 = 22 * u('m/s')
    myquantity3 = pint.Quantity(9, u.kg)

    * Quantities with both units and uncertainty can be defined with the Q() constructor:
        >>> import pagos
    myq1 = pagos.Q(9.0, u.kg, 0.2)
"""

__version__ = '0.4.0'
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