"""
Functions for calculating the properties of water
"""

from __future__ import annotations

from visast import visualise

from pagos.new_constants import GILL_82_COEFFS, DYCK_PESCHKE_95_COEFFS
from pagos.new_core import unit_aware


def old_calc_dens(T: float, S: float) -> float:

    a0, a1, a2, a3, a4, a5, b0, b1, b2, b3, b4, c0, c1, c2, d0 = [
        v.value for v in GILL_82_COEFFS.values()
    ]
    rho0 = a0 + a1 * T + a2 * T**2 + a3 * T**3 + a4 * T**4 + a5 * T**5
    print(S**2)
    rho = (
        rho0
        + S * (b0 + b1 * T + b2 * T**2 + b3 * T**3 + b4 * T**4)
        + (S ** (3 / 2)) * (c0 + c1 * T + c2 * T**2)
        + d0 * S**2
    )
    return rho


@unit_aware({"T": "degC", "S": "permille"}, "kg/m^3")
def new_calc_dens(T: float, S: float) -> float:

    a0, a1, a2, a3, a4, a5, b0, b1, b2, b3, b4, c0, c1, c2, d0 = GILL_82_COEFFS.values()
    rho0 = a0 + a1 * T + a2 * T**2 + a3 * T**3 + a4 * T**4 + a5 * T**5
    print(S**2)
    rho = (
        rho0
        + S * (b0 + b1 * T + b2 * T**2 + b3 * T**3 + b4 * T**4)
        + (S ** (3 / 2)) * (c0 + c1 * T + c2 * T**2)
        + d0 * S**2
    )
    return rho


@unit_aware({"T": "degC"}, "mbar")
def new_calc_vappres(T: float) -> float:
    p0, c = DYCK_PESCHKE_95_COEFFS["p0"], DYCK_PESCHKE_95_COEFFS["c"]
    pv = p0 * 10 ** ((7.567 * T) / (T + c))
    return pv


if __name__ == "__main__":
    visualise.graph(new_calc_dens.ast)
    visualise.graph(new_calc_vappres.ast)
    print(new_calc_dens(30, 10))
    print(old_calc_dens(30, 10))

    print(new_calc_vappres(40))

    # WORKS! DONE: @unit_aware functions that call other @unit_aware functions
    # TODO NEXT: looks like this is more or less done. Let's now see if this works with the gas functions that call these functions
    #            maybe we have to set up some simpler functions first, as the conversion step with gas context is hard...
