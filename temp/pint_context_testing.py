from pagos.core import pQ, _set_fast
from pint import UnitRegistry

X = pQ(2, "mol_g / K / m^2", "He")
X2 = pQ(2, "mol_g / K / m^2", "He")
X3 = pQ(2, "gram_g / K / m^2", "He")
X4 = pQ(2, "g_g / K / m^2", "He")
Y = pQ(2, "mol_g / K / m^2", "Ar")
Z = pQ(2, "mol_Ar * g_Ar / K / m^2")
W = X.to("kg_g / K / mm^2", gas="He")
U = Z.to("kg_gas**2 / K / m^2", gas="Ar")
V = Y.to("g_Ar / K / m^2")

U = X + W
A = X.to("ccSTP_g / K / m^2")

# DONE: add PAGOSQuantity conversion in add/subtract operation. Should be relatively easy now that to() has been implemented... ?
# DONE: do the same thing with other operations that require additive comparison, and check that other arithmetic still works
# DONE: fast mode
# DONE: ccSTP integration


"""print(U)

print(X, Y, Z, W)
print(Y == V, X == X2, X == X3, X3 == X4)

print(X**2 + X3 * X2)"""

_set_fast(True)

X = pQ(2, "mol_g / K / m^2", "He")
X2 = pQ(2, "mol_g / K / m^2", "He")
X3 = pQ(2, "gram_g / K / m^2", "He")
X4 = pQ(2, "g_g / K / m^2", "He")
Y = pQ(2, "mol_g / K / m^2", "Ar")
Z = pQ(2, "mol_Ar * g_Ar / K / m^2")
W = X.to("kg_g / K / mm^2", gas="He")
U = Z.to("kg_gas**2 / K / m^2", gas="Ar")
V = Y.to("g_Ar / K / m^2")

U = X + W

"""print(U)

print(X, Y, Z, W)
print(Y == V, X == X2, X == X3, X3 == X4)

print(X**2 + X3 * X2)
"""
