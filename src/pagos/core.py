"""
Core functions for the PAGOS package. The universal UnitRegistry `u` is included here, as
well as the Quantity shorthand `Q()` and some internal functions.
"""

from pint import UnitRegistry
from pint import Quantity
from pint import Unit
from uncertainties import ufloat
from uncertainties import unumpy as unp
from uncertainties.core import Variable, AffineScalarFunc
import numpy as np
from collections.abc import Iterable
from typing import Callable
import wrapt

"""
THE UNIT REGISTRY u

This is the object from which ALL units within PAGOS and with which PAGOS should
interact will come from. If the user defines another UnitRegistry v in their program, and then
attempts to use PAGOS, it will fail and throw: "ValueError: Cannot operate with Quantity and 
Quantity of different registries."
"""
u = UnitRegistry()

"""
DECORATORS
"""
# TODO add optional keyword that suppresses the _possibly_iterable functionality
@wrapt.decorator # wrapt decorator used so that function argument specification is preserved (see https://github.com/GrahamDumpleton/wrapt/blob/develop/blog/01-how-you-implemented-your-python-decorator-is-wrong.md)
def _possibly_iterable(func, instance:object, args, kwargs) -> Callable:
    """Decorator that can make a function operate on iterables.
    I.e. f(x) >>> y -becomes-> f([x1, x2, x3]) >>> [y1, y2, y3].

    :param func: Function that should be made iterable.
    :type func: function
    :param instance: Necessary placeholder in wrapt
    :type instance: object
    :param args: arguments passed to func
    :param kwargs: keyword arguments passed to func
    :type kwargs: Callable
    """
    # determination of argument to func which is possibly iterable. Defaults to first argument.
    if 'possit' in kwargs:
        possitkey = kwargs['possit']
    else:
        possitkey = 0
    # different behaviour if the possibly iterable argument is in function's args or kwargs.
    if type(possitkey) == int:
        possit = args[possitkey]
        def return_array():
            retarr = []
            for x in possit:
                newargs = tuple([x]) + tuple(a for a in args if a is not possit)
                retarr.append(func(*newargs, **kwargs))
            return retarr
    else:
        possit = kwargs[possitkey]
        def return_array():
            retarr = []
            for x in possit:
                newkwargs = tuple([x]) + tuple(kwargs[k] for k in kwargs if k is not possitkey)
                retarr.append(func(*args, **newkwargs))
            return retarr
    # Quantity objects are iterable, so some janky if-statements are needed here.
    # Returns unchanged function if possibly iterable argument is in fact singular,
    # and returns the array-form of the function if it is in fact iterable. 
    if isinstance(possit, Iterable):
        if isinstance(possit, Quantity):
            if isinstance(possit.magnitude, Iterable):
                return return_array()
            else:
                return func(*args, **kwargs)
        else:
            return return_array()
    else:
        return func(*args, **kwargs)



"""
FUNCTIONS
"""
def safeexp(x:Quantity|Iterable[Quantity]) -> Quantity|Iterable[Quantity]:
    """Safe exponentiation function. Makes sure input to an exponential is dimensionless before
    performing exponentiation.

    :param x: Input to exponential.
    :type x: Quantity | Iterable[Quantity]
    :return: Result, e^(dimensionless x).
    :rtype: Quantity | Iterable[Quantity]
    """

    dimless_x = sto(x, 'dimensionless')
    return unp.exp(dimless_x)


def safeln(x:Quantity|Iterable[Quantity]) -> Quantity|Iterable[Quantity]:
    """Safe natural logarithm function. Makes sure input to a logarithm (base e) is
    dimensionless before performing calculation.

    :param x: Input to logarithm.
    :type x: Quantity | Iterable[Quantity]
    :return: Result, ln(dimensionless x).
    :rtype: Quantity | Iterable[Quantity]
    """

    dimless_x = sto(x, 'dimensionless')
    return unp.log(dimless_x)

@_possibly_iterable
def deriv(x:Quantity|Iterable[Quantity], wrt:Quantity) -> Quantity:
    """Calculates the derivative of x with respect to wrt, evaluated at the given value of wrt
    and whatever other parameters constituting x, returning a Quantity object.

    :param x: Input to derivative function.
    :type x: Quantity | Iterable[Quantity]
    :param wrt: Quantity with respect to which the differentiation will be performed. If wrt has
    a nonabsolute temperature unit, like degC or degF, it will be changed accordingly.
    :type wrt: Quantity
    :return: Result, dx/d(wrt) evaluated at given value of x and its arguments.
    :rtype: Quantity
    """
    derivquant = u.Quantity(x.derivatives[wrt.magnitude], x.units)
    # special handling for temperature
    if wrt.units == u('degC'):
        divunits = u('K')
    elif wrt.units == ('degF'):
        divunits = u('Rankine')
    else:
        divunits = wrt.units
    return derivquant / divunits

@_possibly_iterable
def sto(x:Quantity|Iterable[Quantity], to:str|Unit, strict=True) -> Quantity|Iterable[Quantity]:
    """sto <=> 'safe to'. Derivative-safe alternative to Quantity.to(). This creates a new
    Quantity whose derivatives are different, unlike regular Quantity.to(), which will leave the
    derivatives of a Quantity's magnitude unchanged. Only Quantity objects with a magnitude
    parameter of type ufloat will be changed, otherwise behaves like Quantity.to().

    :param x: Quantity whose units should be changed.
    :type x: Quantity | Iterable[Quantity]
    :param to: Unit to convert the Quantity object to.
    :type to: str | Unit
    :param strict: Whether to return x [True] or an error [False] if x is not a Quantity object, defaults to True
    :type strict: bool, optional
    :return: Result similar to x.to(to), but with a newly initialised object.
    :rtype: Quantity | Iterable[Quantity]
    """
    if to is None:
        return x
    if type(x) == u.Quantity:
        convertq = x.to(to)
        if x.units == convertq.units:   # FIXME if I don't include this, everything breaks - must be investigated...
                                        # Notes on this: it appears to be an issue with creating new Quantity objects.
                                        # The big issue is that when we don't include this if statement, the core.deriv()
                                        # function no longer works. It throws an error saying that the specified derivative
                                        # does not exist in the ufloat object (specifically, a KeyError). However this key
                                        # does exist, with the same value T, but with a different location in memory, i.e.:
                                        # >>> .derivatives[T] == .derivatives[the key which is actually there]
                                        # but
                                        # >>> .derivatives[T] is not derivatives[thing key which is actually there].
                                        # Somehow, this ugly fix will solves the problem, I think by returning the same
                                        # pointer? I'm not quite sure.
                                        # If we remove this statement, the only other way to stop the error occurring that
                                        # I found was to replace all instances of _core.sto(T, 'K') in water.py with T.to('K').
                                        # This must then also return the same object when the unit is already 'K',
                                        # something to that effect... I am very stumped here!
            return x
        if type(x.magnitude) == Variable:
            mag_v = convertq.magnitude.nominal_value
            mag_e = convertq.magnitude.std_dev
            newquant = u.Quantity(ufloat(mag_v, mag_e), to)
        else:
            mag = convertq.magnitude
            newquant = u.Quantity(mag, to)
        return newquant
    elif x is None:
        return None
    else:
        if strict:
            raise ValueError('x must be of type pint.Quantity.')
        else:
            return u.Quantity(x, to)

@_possibly_iterable #TODO this could be implemented in LOTS of places around the code where we constantly have to go through the tedious process of checking if a quantity is a Quantity with Variable/AffineScalarFunc magnitude, if it's just got a normal magnitude or if it's not got a magnitude at all
# TODO implement strictness argument to return error if there is no nominal_value
def snv(x):
    """snv <=> 'safe nominal value'. If x is an uncertainties Variable/AffineScalarFunc, its
    nominal_value is returned. Otherwise only x is returned. Quantities are handled to remove units.

    :param x: Input number.
    :type x: any
    :return: Nominal value of x.
    """
    if (isinstance(x, u.Quantity) and isinstance(x.magnitude, (Variable, AffineScalarFunc))) or isinstance(x, (Variable, AffineScalarFunc)):
        return x.nominal_value
    elif isinstance(x, u.Quantity):
        return x.magnitude
    else:
        return x

@_possibly_iterable
# TODO implement strictness argument to return error if there is no std_dev
def ssd(x):
    """ssd <=> 'safe standard deviation'. If x is an uncertainties Variable/AffineScalarFunc, its
    std_dev is returned. Otherwise None is returned. Quantities are handled to remove units.

    :param x: Input number.
    :type x: any
    :return: Standard deviation of x.
    """
    if (isinstance(x, u.Quantity) and isinstance(x.magnitude, (Variable, AffineScalarFunc))) or isinstance(x, (Variable, AffineScalarFunc)):
        return x.std_dev
    else:
        return None

@_possibly_iterable
# TODO implement strictness argument to return error if there is no units
def sgu(x):
    """sgu <=> 'safe get units'. If x is a Pint Quantity, its units are returned. Otherwise
    None is returned.

    :param x: Input quantity.
    :type x: any
    :return: Units of x.
    """
    if isinstance(x, u.Quantity):
        return x.units
    else:
        return None
    
def units_are_equal(units1, units2):
    if type(units1) == type(units2) == str or type(units1) == type(units2) == None:
        if units1 == units2:
            return True
    if units1 is None:
        units1 = ''
    if units2 is None:
        units2 = ''
    if Unit(units1) == Unit(units2):
        return True
    else:
        return False

def Q(val:float, unit:str|Unit, err:float=None) -> Quantity:
    """Shorthand function for making a pint Quantity object with an uncertainties ufloat for a
    magnitude.

    :param val: Nominal value of the ufloat.
    :type val: float
    :param err: Error/standard deviation of the ufloat.
    :type err: float
    :param unit: Units of the Quantity.
    :type unit: str | Unit
    :return: Quantity with ufloat as magnitude.
    :rtype: Quantity
    """
    if err is None:
        return u.Quantity(val, unit)
    else:
        return u.Quantity(ufloat(val, err), unit)