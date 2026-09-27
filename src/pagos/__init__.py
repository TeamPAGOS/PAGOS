"""
PAGOS
=====

Python Analysis of Groundwater and Ocean Samples.

Provides
--------
    1. `PAGOSQuantity` object, with value and unit. Units can be gas-specific.
    2. Functions for calculating the properties of water and dissolved gases.
    3. `TracerModel` object, for fitting the parameters of pre-defined or user-defined tracer models to data.
"""

__version__ = "1.0.0"
__author__ = "Stanley Scott and Chiara-Marlen Hubner"

# for ease of use, these could change later
from .core import pQ
from .gas import calc_Ceq, calc_Sc
from .modelling import TracerModel

from . import units
from . import core
from . import constants
from . import water
from . import gas
from . import modelling
from . import builtin_models

# Allow the warning for nonmultiplicative units on functions wrapped with pagos.core.unit_aware
# This happens here at the end of all these function definitions, because otherwise every time PAGOS
# was imported, a bunch of warnings would show up. This way, the warnings will only show for user-
# defined functions.
core._warn_nonmult_in_unit_aware = True
