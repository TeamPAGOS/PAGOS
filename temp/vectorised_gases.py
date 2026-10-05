# testing for vectorisation of "gas" argument

# Clearly this would have to be done by associating some numpy integer with each tracer. This is not a problem

# Say He = 1, Ne = 2, Ar = 3, Kr, = 4, Xe = 5

import timeit

import numpy as np
from numpy.typing import ArrayLike

# Here is an example of how we could implement a very simple getter function.
# Instead of returning from a Python dictionary, the gas abundances are already
# loaded in as a numpy array. Access would always have to happen by accessing
# through a number associated with each gas - but I argue that this could be done
# just ONCE at the beginning of a fitting procedure, and then all calls to the
# getter would have an array of integers as the 'gas' argument.
ABUNDANCES = np.array(
    [5.24e-6, 18.18e-6, 0.934e-2, 1.14e-6, 0.087e-6],
    dtype="d",
)


# Proposed new implementation of getter
def abn(gas_code: ArrayLike | int):
    return ABUNDANCES[gas_code]


# Numpy array of keys can be used, instead of a list comprehension
npindices = np.array([0, 1, 2, 3, 4], dtype="l")


# This is the current implementation: a dictionary which is called up as needed.
ABUNDANCES_DICT = {
    "He": 5.24e-6,
    "Ne": 18.18e-6,
    "Ar": 0.934e-2,
    "Kr": 1.14e-6,
    "Xe": 0.087e-6,
}


# Current implementation
def dictabn(gas: str):
    return ABUNDANCES_DICT[gas]


stringkeys = ["He", "Ne", "Ar", "Kr", "Xe"]


# Current implementation requires a comprehension
normalcode = """np.array([dictabn(gas) for gas in stringkeys])"""
normaltime = timeit.timeit(normalcode, globals=globals(), number=10000000)

# New implementation does not require comprehension
npcode = """abn(npindices)"""
nptime = timeit.timeit(npcode, globals=globals(), number=10000000)

print("Normal time:", normaltime)  # -> will vary on different machines - I get 8-9 s
print("Numpy time:", nptime)  # -> similarly, I get ~2 s
print("Improvement factor:", normaltime / nptime)  # -> I get ~ 4-5x speed improvement


# A nice alternative would be a Numpy data-structure that can be accessed by non-integer keys,
# e.g. char arrays of fixed width. I tried looking into Structured Arrays - but this did not
# seem to work; it allowed for association of each entry of an Array with more data, so
# something like:
#     ABUNDANCES_STRUCT_ARR = np.array([('He', 5.24e-6), ('Ne', 18.18e-6), ...])
# but this could not *access* the float value by passing in an array of strings.
# Ultimately, I don't even think this dictionary-like Numpy structure is even possible;

# as far as I understand, Numpy is fast because it is written in C underneath, and can
# push numbers onto the stack. Dicking about with key-value pairs would presumably erase
# this advantage anyway
