"""
Decorators wrapping functions used in `gas.py`, for pretty code.
"""

import numpy as np
from typing import Callable
import wrapt

from pagos.core import u as _u


@wrapt.decorator # wrapt decorator used so that function argument specification is preserved (see https://github.com/GrahamDumpleton/wrapt/blob/develop/blog/01-how-you-implemented-your-python-decorator-is-wrong.md)
def oneormoregases(func, instance:object, args, kwargs) -> Callable:
    """Decorator that transforms a tracer-operating function so that it can take in an array of
    tracers. 

    :param func: Function to wrap
    :type func: function
    :param instance: Necessary placeholder in wrapt
    :type instance: object
    :param args: arguments passed to func
    :param kwargs: keyword arguments passed to func
    :return: Wrapped function
    :rtype: Callable
    """
    # arguments here given according to wrapt specification, see link above
    # dealing with argument 'gas', which must ALWAYS have this name (see https://wrapt.readthedocs.io/en/master/decorators.html#processing-function-arguments):
    def _execute(gas, *_args, **_kwargs):
        if type(gas) == str:
            return func(gas, *_args, **_kwargs)
        else:
            ret = np.array([func(g, *_args, **_kwargs) for g in gas], dtype=object) # TODO exception thrown if dtype argument not included: perhaps investigate this further?
            # if ret has structure like [Quantity(val1, unit), Quantity(val2, unit), Quantity(val3, unit), ...]
            # change to Quantity([val1, val2, val3, ...], unit), which makes further calculations easier later
            if [type(elt) for elt in ret] == [_u.Quantity for elt in ret]:  #\
                if len(set([elt.units for elt in ret])) == 1:               #/ -- these check for above-mentioned structure 
                    ret = _u.Quantity([elt.magnitude for elt in ret], ret[0].units)
            return ret
    return _execute(*args, **kwargs)
    

# OLD CODE
'''def oneormoregases(func):
    """Wraps function with a gas argument so that an list of gases can be passed instead.

    :param func: Function to wrap.
    :type func: function
    """
    def wrapper_oomt(gas, *args, **kwargs):
        if type(gas) == str:
            return func(gas, *args, **kwargs)
        else:
            ret = np.array([func(g, *args, **kwargs) for g in gas], dtype=object) # TODO exception thrown if dtype argument not included: perhaps investigate this further?
            # if ret has structure like [Quantity(val1, unit), Quantity(val2, unit), Quantity(val3, unit), ...]
            # change to Quantity([val1, val2, val3, ...], unit), which makes further calculations easier later
            if [type(elt) for elt in ret] == [_u.Quantity for elt in ret]:  #\
                if len(set([elt.units for elt in ret])) == 1:               #/ -- these check for above-mentioned structure 
                    ret = _u.Quantity([elt.magnitude for elt in ret], ret[0].units)
            return ret
    return wrapper_oomt'''