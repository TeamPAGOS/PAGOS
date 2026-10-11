"""
Functions for calculating the properties of water
"""

from __future__ import annotations

from visast import visualise

from pagos.new_constants import (
    GILL_82_COEFFS,
)
from pagos.new_core import unit_aware


@unit_aware({"T": "degC", "S": "permille"}, "kg/m^3")
def new_calc_dens(T: float, S: float) -> float:

    a0, a1, a2, a3, a4, a5, b0, b1, b2, b3, b4, c0, c1, c2, d0 = GILL_82_COEFFS.values()
    rho0 = a0 + a1 * T + a2 * T**2 + a3 * T**3 + a4 * T**4 + a5 * T**5
    rho = (
        rho0
        + S * (b0 + b1 * T + b2 * T**2 + b3 * T**3 + b4 * T**4)
        + (S ** (3 / 2)) * (c0 + c1 * T + c2 * T**2)
        + d0 * S**2
    )
    return rho


if __name__ == "__main__":
    visualise.graph(new_calc_dens.ast)
    print(new_calc_dens(30, 10))
    print(new_calc_dens)
