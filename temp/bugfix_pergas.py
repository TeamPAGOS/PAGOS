from pagos.gas import Ar, molvol, calc_Ceq

assert Ar.molar_volume**2 == molvol("Ar") ** 2
assert Ar.calc_Ceq(10, 20, 1) == calc_Ceq("Ar", 10, 20, 1) ** 2
