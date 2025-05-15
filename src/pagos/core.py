"""
Core functions for the PAGOS package. The Quantity shorthand `Q()` is included here, as well as
some internal functions/decorators.
"""

from pint import Quantity
from pint import Unit
from uncertainties import ufloat
from uncertainties import unumpy as unp
from uncertainties.core import Variable, AffineScalarFunc
import numpy as np
from collections.abc import Iterable
from typing import Callable
import wrapt
from pagos.units import u

"""
MISCELLANEOUS VARIABLES
"""
# this enables/disables the _possibly_iterable decorator
_ENABLE_POSSIT = True
def _is_possit_enabled():
    return _ENABLE_POSSIT

def _set_possit(value:bool):
    if type(value) != bool:
        raise TypeError('value must be boolean.')
    global _ENABLE_POSSIT
    _ENABLE_POSSIT = value

# this enables/disables the wraptpint decorator
_ENABLE_WP = True
def _is_wp_enabled():
    return _ENABLE_WP

def _set_wp(value:bool):
    if type(value) != bool:
        raise TypeError('value must be boolean.')
    global _ENABLE_WP
    _ENABLE_WP = value

"""
DECORATORS
"""
@wrapt.decorator(enabled=_is_possit_enabled) # wrapt decorator used so that function argument specification is preserved (see https://github.com/GrahamDumpleton/wrapt/blob/develop/blog/01-how-you-implemented-your-python-decorator-is-wrong.md)
def _possibly_iterable(func, instance:object, args, kwargs) -> Callable:
    """Decorator that can make a function operate on iterables as\\
    f(*x\u1d62*) >>> \u03b1*\u2c7c* \u23af\u23afmake args labelled w/ *k* iterable\u23af\u23af\u25BA f(*x\u1d62*\u03b4*\u1d62\u2096* + *x\u1d62*(1 − \u03b4*\u1d62\u2096*)) >>> \u03b1*\u2c7c\u2096*\\
    I.e.:\\
    f(x) >>> \u03b1 \u23af\u23af\u23af\u25BA f([x1, x2, x3]) >>> [\u03b11, \u03b12, \u03b13]\\
    f(x, y, z) >>> \u03b1 \u23af\u23af\u23af\u25BA f([x1, x2, x3], y, z) >>> [\u03b11, \u03b12, \u03b13]\\
    f(x, y, z) >>> \u03b1, \u03b2 \u23af\u23af\u23af\u25BA f([x1, x2, x3], y, z) >>> [\u03b11, \u03b12, \u03b13], [\u03b21, \u03b22, \u03b23]\\
    f(x, y, z) >>> \u03b1 \u23af\u23af`possit==1`\u23af\u23af\u25BA f(x, [y1, y2, y3], z) >>> [\u03b11, \u03b12, \u03b13]\\
    f(x, y, z) >>> \u03b1 \u23af\u23af`possit==(0, 1)`\u23af\u23af\u25BA f([x1, x2, x3], [y1, y2, y3], z) >>> [\u03b11, \u03b12, \u03b13]

    :param func: Function that should be made iterable.
    :type func: function
    :param instance: Necessary placeholder in wrapt
    :type instance: object
    :param args: Arguments passed to func
    :type args: Any
    :param kwargs: Keyword arguments passed to `func` - can contain keyword `possit=...` which determines which of the arguments of `func` are allowed to be iterable.
    Note that this can be tuple; e.g. `possit=(0, 2)` means the 1st and 3rd arguments to `func` may be iterable; `possit=('A', 'C') ` means the kwargs `A` and `C` may be iterable.
    :type kwargs: Any
    """
    # determination of argument to func which is possibly iterable. Defaults to first argument.
    if 'possit' in kwargs:
        possitkey = kwargs['possit']
        # remove 'possit' from keyword arguments passed to wrapped function
        kwargs_to_func = {k:kwargs[k] for k in kwargs if k != 'possit'}
        # option to suppress _possibly_iterable functionality by using possit=None in the arguments of the function 
        if possitkey == None:
            return func(*args, **kwargs_to_func)
    else:
        possitkey = 0
        kwargs_to_func = kwargs

    # option to sppress _possibly_iterable functionality for subsequent calls
    # EXPERIMENTAL
    # WARNING: ONLY USE IF YOU WILL MANUALLY RE-ENABLE STRAIGHT AWAY WHEN NECESSARY
    if 'disablenext' in kwargs:
        disablenext = kwargs['disablenext']
        if disablenext:
            kwargs_to_func = {k:kwargs[k] for k in kwargs if k != 'disablenext'}
            _set_possit(False)
    
    # different behaviour if the possibly iterable argument(s) is(are) in function's args or kwargs.
    # NOTE: so far mixed behaviour is not allowed - either the iterable arguments must all be args or all kwargs.
    if type(possitkey) == int:
        possit = args[possitkey]
        isiterable = _is_iterable_sq_safe(possit)
        def return_array():
            retarr = []
            for x in possit:
                newargs = list(args)
                newargs[possitkey] = x
                retarr.append(func(*newargs, **kwargs_to_func))
            return _tidy_iterable(retarr)
    
    elif type(possitkey) == tuple and all(type(p) == int for p in possitkey):
        possit_array = [args[p] for p in possitkey]
        isiterable = all(_is_iterable_sq_safe(possit) for possit in possit_array)
        def return_array():
            retarr = []
            for i in range(len(possit_array[0])):
                newargs = list(args)
                for j in possitkey:         # TODO is this really the best way to do this? Embedded for loops may slow down code
                    newargs[j] = args[j][i]
                retarr.append(func(*newargs, **kwargs_to_func))
            return _tidy_iterable(retarr)
    
    elif type(possitkey) == str:
        possit = kwargs[possitkey]
        isiterable = _is_iterable_sq_safe(possit)
        def return_array():
            retarr = []
            for x in possit:
                newkwargs = kwargs_to_func
                newkwargs[possitkey] = x
                retarr.append(func(*args, **newkwargs))
            return _tidy_iterable(retarr)
    
    elif type(possitkey) == tuple and all(type(p) == str for p in possitkey):
        possit_array = [kwargs[p] for p in possitkey]
        isiterable = all(_is_iterable_sq_safe(possit) for possit in possit_array)
        def return_array():
            retarr = []
            for i in range(len(possit_array[0])):
                newkwargs = kwargs_to_func
                for j in possitkey:
                    newkwargs[j] = kwargs[j][i]
                retarr.append(func(*args, **newkwargs))
            return _tidy_iterable(retarr)
    
    else:
        raise TypeError('possit must be an integer, tuple of integers, string or tuple of strings. \n\
                        WARNING: This should not have been triggered by the user! If this error has shown up, there is a bug in the code caused by incorrect use of pagos.core._possibly_iterable().')
    return_array.__is_possibly_iterable__ = True
    # Quantity objects are iterable, so this deals with the relevant cases
    if isiterable:
        return return_array()
    else:
        return func(*args, **kwargs_to_func)


def wraptpint(  # signature copied from pint wraps()
    ret_units: str | Unit | Iterable[str | Unit | None] | None,
    arg_units: str | Unit | Iterable[str | Unit | None] | None,
    strict: bool,
):
    """Alternative to pint wraps() functionality that preserves function signature.

    :param ret_units: units of value returned by function
    :type ret_units: str | Unit | Iterable[str | Unit | None] | None
    :param arg_units: units of input arguments to function
    :type arg_units: str | Unit | Iterable[str  |  Unit  |  None] | None
    :param strict: indicates that only `Quantity`s are to be accepted, defaults to True
    :type strict: bool, optional
    :return: the wrapper function
    """
    @wrapt.decorator()
    def wrapper(func, instance, args, kwargs):
        # option to bypass the wrapping if the user does not want it
        # EXPERIMENTAL
        if not _is_wp_enabled():
            try:                                    # TODO there are a few places in the code where kwarg popping is done like: kwargs_to_func = {k:kwargs[k] for k in kwargs if k != <kwarg to remove>}
                kwargs.pop('magnitude')             #   where possible (not always, see the block below for example) should all look like this instead, I think - it seems better
            finally:
                return func(*args, **kwargs)
        else:
            unitwrapped = u.wraps(ret=ret_units, args=arg_units, strict=strict)(func)
            # option to return the magnitude if the user desires (alternative to Quantity.magnitude)
            if 'magnitude' in kwargs and kwargs['magnitude']:
                kwargs.pop('magnitude')
                return unitwrapped(*args, **kwargs).magnitude
            else:
                return unitwrapped(*args, **kwargs)
    return wrapper

"""
FUNCTIONS
"""
def _is_iterable_sq_safe(possit) -> bool:
    """Singular `Quantity` objects are instances of `Iterable`, as are strings. So, this function
    returns `False` if the argument is a `str`, a non-`Iterable` or a `Quantity` with
    non-`Iterable` magnitude, and `True` otherwise.

    :param possit: Possibly iterable argument
    :type possit: Any
    :return: `False` if `possit` is a `str`, non-`Iterable` or `Quantity` with non-`Iterable` magnitude, `True` otherwise.
    :rtype: bool
    """
    if isinstance(possit, Iterable):
        if isinstance(possit, Quantity):
            if isinstance(possit.magnitude, Iterable):  # Q([x1, x2, ...], units)
                return True
            else:                                       # Q(x, units)
                return False
        elif isinstance(possit, str):                   # string
            return False
        else:                                           # [x1, x2, ...]
            return True
    else:                                               # x
        return False


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
def snv(x, strict:bool=False):
    """snv <=> 'safe nominal value'. If x is an uncertainties Variable/AffineScalarFunc, its
    nominal_value is returned. Otherwise only x is returned. Quantities are handled to remove units.

    :param x: Input number.
    :type x: any
    :return: Nominal value of x.
    """
    if (isinstance(x, u.Quantity) and isinstance(x.magnitude, (Variable, AffineScalarFunc))) or isinstance(x, (Variable, AffineScalarFunc)):
        return x.nominal_value
    elif strict:
        raise TypeError('with strict==True, x must have property x.nominal_value')
    elif isinstance(x, u.Quantity):
        return x.magnitude
    else:
        return x

@_possibly_iterable
def ssd(x, strict:bool=False):
    """ssd <=> 'safe standard deviation'. If x is an uncertainties Variable/AffineScalarFunc, its
    std_dev is returned. Otherwise None is returned. Quantities are handled to remove units.

    :param x: Input number.
    :type x: any
    :return: Standard deviation of x.
    """
    if (isinstance(x, u.Quantity) and isinstance(x.magnitude, (Variable, AffineScalarFunc))) or isinstance(x, (Variable, AffineScalarFunc)):
        return x.std_dev
    elif strict:
        raise TypeError('with strict==True, x must have property x.std_dev')
    else:
        return None

@_possibly_iterable
def sgu(x, strict:bool=False):
    """sgu <=> 'safe get units'. If x is a Pint Quantity, its units are returned. Otherwise
    None is returned.

    :param x: Input quantity.
    :type x: any
    :return: Units of x.
    """
    if isinstance(x, u.Quantity):
        return x.units
    elif strict:
        raise TypeError('with strict==True, x must have property x.units')
    else:
        return None
    

def _tidy_iterable(it:Iterable) -> np.ndarray | Iterable:
    """Tidy up `[Q(x1, unit), Q(x2, unit), ...]` as `Q([x1, x2, ...], unit)`.
    Will perform no such conversion if units are not the same (i.e. `[Q(x1, u1), Q(x2, u2), ...]` where `ui != uj`).
    Always returns type np.array if possible.

    :param it: Iterable `[Q(x1, u1), Q(x2, u2), ...]`
    :type it: Iterable
    :return: `Q([x1, x2, ...], u)` if `ui == u` for all `i`, else `it`
    :rtype: ndarray
    """
    # perform tidying
    if all(isinstance(elt, Quantity) for elt in it):
        units0 = it[0].units
        if all(elt.units == units0 for elt in it):
            stripped = np.array([elt.magnitude for elt in it])
            return u.Quantity(stripped, units0)
    try:
        return np.array(it)
    except ValueError:
        return np.array(it, dtype=object)


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
