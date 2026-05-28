from numpy.random import normal
from functools import wraps
from inspect import signature


def mc_possible(dist_std: str):
    def _mc_possible(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            reset_tag = False
            if self.enable_mc:
                self.enable_mc = False
                reset_tag = True

            ret = func(self, *args, **kwargs)

            if reset_tag:
                self.enable_mc = True
                reset_tag = False

            if self.enable_mc:
                if isinstance(dist_std, float):
                    ret = ret * normal(1, dist_std)
                elif isinstance(dist_std, str):
                    ret = self.errfuncs[dist_std](ret)
                else:
                    raise TypeError("Argument dist_std must be str or float")
            return ret

        return wrapper

    return _mc_possible


def _add_self_argument(func):
    """
    Utility to include add the argument 'self' to the front of a function's signature. ONLY to be used in make_mcmethod.
    """

    def wrapper(self, *args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


class PAGOSCalculator:
    def __init__(self):
        self.errfuncs = {
            "add": lambda base_value: base_value * normal(1, 0.01),
            "mult": lambda base_value: base_value * normal(1, base_value / 100),
            "combi": lambda base_value: base_value * normal(1, 0.001),
        }

        self.enable_mc = True

    def make_mcmethod(self, func, dist_std):
        # The func, coming from outside this class, does not have a `self` attribute and therefore must have it created here
        func_with_self = _add_self_argument(func)

        # mc_possible decorates the function, and we set it as an attribute in the class
        method_to_add = mc_possible(dist_std)(func_with_self)
        setattr(self.__class__, func.__name__, method_to_add)

    @mc_possible("add")
    def add_example(self, x1, x2):
        result = x1 + x2
        return result

    @mc_possible("mult")
    def mult_example(self, x1, x2):
        result = x1 * x2
        return result

    @mc_possible("combi")
    def combi_example(self, x1, x2, x3):
        y = self.add_example(x1, x2)
        z = self.mult_example(y, x3)
        return z

    @mc_possible(0.0001)
    def custom_combi_example(self, x1, x2, x3):
        y = self.add_example(x1, x2)
        z = self.mult_example(y, x3)
        return z


calc = PAGOSCalculator()

# Internal functions of PAGOSCalculator - represent the built-in functions of PAGOS and require no additional mc commands
print("Adding function, with 1 percent error (results should scatter with magnitude 1)")
for i in range(5):
    a = calc.add_example(50, 50)  # "calc." should be parsed out in the final version
    print(a)

print(
    "\nMultiplying function, with proportional error (results should scatter with magnitude 100)"
)
for i in range(5):
    a = calc.mult_example(50, 2)  # "calc." should be parsed out in the final version
    print(a)

print(
    "\nCombined function, with 0.1 percent error (results should scatter with magnitude 0.1)"
)
for i in range(5):
    a = calc.combi_example(
        20, 5, 4
    )  # "calc." should be parsed out in the final version
    print(a)


print(
    "\nCombined function, with custom 0.01 percent error (results should scatter with magnitude 0.01)"
)
for i in range(5):
    a = calc.custom_combi_example(
        20, 5, 4
    )  # "calc." should be parsed out in the final version
    print(a)


# Now the user creates their own function, which utilises PAGOS builtins (in this example it uses the example adding function)
# In order for MC to work for this function too, it must be made into a method of PAGOSCalculator, which is done by the
# calc.make_mcmethod function:
def external_add(x, y):
    return calc.add_example(x, y)


calc.make_mcmethod(external_add, 0.0001)
calc.make_mcmethod(calc.mult_example, 0.01)
print(
    "\nExternal add function, with custom 0.01 percent error (results should scatter with magnitude 0.01)"
)
for i in range(5):
    print(calc.external_add(10, 90))

print(
    "\nOverwritten multiplication, with custom 1 percent error (results should scatter with magnitude 1)"
)
for i in range(5):
    print(calc.mult_example(50, 2))
