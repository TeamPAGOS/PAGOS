import timeit

import numpy as np


def unitswrapper(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


class _Quantity:
    def __init__(self, value, other_stuff):
        self.value = value
        self.other_stuff = other_stuff

    @unitswrapper
    def __add__(self, other):
        return _Quantity(np.add(self, other), self.other_stuff)

    def __array_ufunc__(self, ufunc, method, *inputs, **kwargs):
        if method != "__call__":
            raise NotImplementedError(
                "ufunc methods other than '__call__' are not implemented"
            )

        if ufunc.__name__ == "add":
            print(f"ufunc adding {[inp.value for inp in inputs]}")
            return unitswrapper(ufunc)(*(inp.value for inp in inputs))


q1 = _Quantity(np.array([1, 2]), "cm")
q2 = _Quantity(np.array([1, 2]), "cm")

print((q1 + q2).value)
