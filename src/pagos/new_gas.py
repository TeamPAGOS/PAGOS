from __future__ import annotations

import ast

import numpy as np

from pagos.new_constants import (
    ABUNDANCES,
    CFC_WARNERWEISS_85_COEFFS,
    EYRING_36_COEFFS,
    EYRING_36_HAMME_SALT_CORRECTION,
    K100,
    MGC,
    MOLAR_MASSES,
    MOLAR_VOLUMES,
    NG_JENKINS_19_COEFFS,
    PAT,
    SF6_BULLISTER_02_COEFFS,
    WANNINKHOF_92_COEFFS,
    WANNINKHOF_92_SALTFACTOR_COEFFS,
    ArNeN2_HAMMEEMERSON_04_COEFFS,
)
from pagos.new_units import PAGOSQuantity, pQ
from pagos.new_core import unit_aware
from pagos.new_water import new_calc_kinvisc, new_calc_vappres

PREDEFINED_GASES = ["He", "Ne", "Ar", "Kr", "Xe", "N2", "CFC11", "CFC12", "SF6"]

# Gases grouped according to properties
STABLETRANSIENTGASES = ["CFC11", "CFC12", "SF6"]
NOBLEGASES = ["He", "Ne", "Ar", "Kr", "Xe"]
BIOLOGICALGASES = ["N2"]


@unit_aware({"gas": None, "T": "degC", "S": "permille"}, "dimensionless")
def __calc_Sc_W92(
    gas,
    T: float,
    S: float,
) -> float:
    # Wanninkhof 1992 method
    # salt factor for if the water is salty or not. Threshold is low, therefore this method is only recommended
    # for waters with salinity approx. equal to 34 g/kg.
    if S > 0.005:  # (> 5 permille)
        f0, f1, f2, f3 = (
            WANNINKHOF_92_SALTFACTOR_COEFFS[s] for s in ["f0", "f1", "f2", "f3"]
        )
        saltfactor = (f0 + f1 * T + f2 * T**2 + f3 * T**3) / 0.94
    elif 0 <= S <= 0.005:
        saltfactor = 1
    else:
        raise ValueError("S must be a number >= 0.")
    A, B, C, D = (WANNINKHOF_92_COEFFS[gas][s] for s in ["A", "B", "C", "D"])
    Sc = saltfactor * (A - B * T + C * T**2 - D * T**3)
    return Sc


@unit_aware({"gas": None, "T": "degC", "S": "permille"}, "dimensionless")
def __calc_Sc_HE17(gas, T: float, S: float) -> float:
    # Hamme & Emerson 2017 method
    # Eyring diffusivity calculation
    # units (cm2/s, kJ/mol)
    (A_coeff, activation_energy) = (EYRING_36_COEFFS[gas][s] for s in ["A", "Ea"])
    D0 = A_coeff * np.exp(-activation_energy / (MGC * T.to("K")))  # -> cm2/s
    # Saltwater correction used by R. Hamme in her Matlab script (https://oceangaseslab.uvic.ca/download.html)
    D = D0 * (1 - 0.049 * S / EYRING_36_HAMME_SALT_CORRECTION)  # PSS78 as Salinity
    # Kinematic viscosity calculation
    nu_sw = new_calc_kinvisc(T, S)
    Sc = nu_sw / D
    return Sc


@unit_aware({"gas": None, "T": "degC", "S": "permille"}, "mol_g/kg")
def __calc_Cstar_J19(gas, T: float, S: float) -> float:
    T_K = T.to("K")
    T_N = T_K / K100
    A0, AR, AL, A1, B0, B1, B2, C0 = [
        NG_JENKINS_19_COEFFS[gas][c]
        for c in ["A0", "AR", "AL", "A1", "B0", "B1", "B2", "C0"]
    ]
    Cstar = np.exp(
        A0
        + AR / T_N
        + AL * np.log(T_N)
        + A1 * T_N
        + S * (B0 + B1 * T_N + B2 * T_N**2)
        + S**2 * C0
    ) * pQ(1, f"mol_{gas}/kg")
    return Cstar


@unit_aware({"gas": None, "T": "degC", "S": "permille", "ab": None}, "mol_g/kg")
def __calc_Cstar_WW85(gas, T: float, S: float, ab: str = "default") -> float:
    T_K = T.to("K")
    T_N = T_K / K100
    a1, a2, a3, a4, b1, b2, b3 = CFC_WARNERWEISS_85_COEFFS[
        gas
    ].values()  # needs S in parts per thousand
    # TODO adopt for absolute salinity??
    # abundance
    if ab == "default":
        ab = ABUNDANCES[gas]
    # C* = F * abundance, concentration calculated from Warner and Weiss 1985
    Cstar = (
        np.exp(
            a1
            + a2 / T_N
            + a3 * np.log(T_N)
            + a4 * T_N**2
            + S * (b1 + b2 * T_N + b3 * T_N**2)
        )
        * ab
    ) * pQ(1, f"mol_{gas}/kg")
    return Cstar


@unit_aware({"gas": None, "T": "degC", "S": "permille", "ab": None}, "mol_g/kg")
def __calc_Cstar_B02(gas, T: float, S: float, ab: str = "default") -> float:
    T_K = T.to("K")
    T_N = T_K / K100
    a1, a2, a3, b1, b2, b3 = SF6_BULLISTER_02_COEFFS[
        gas
    ].values()  # don't know salinity unit
    # abundance
    if ab == "default":
        ab = ABUNDANCES[gas]
    # C* = F*abundance, concentration calculated from Bullister et al. 2002
    Cstar = (
        np.exp(a1 + a2 / T_N + a3 * np.log(T_N) + S * (b1 + b2 * T_N + b3 * T_N**2))
        * ab
    ) * pQ(1, f"mol_{gas}/kg")
    return Cstar


@unit_aware({"gas": None, "T": "degC", "S": "permille"}, "mol_g/kg")
def __calc_Cstar_HE04(gas, T: float, S: float) -> float:
    T_K = T.to("K")
    A0, A1, A2, A3, B0, B1, B2 = ArNeN2_HAMMEEMERSON_04_COEFFS[
        gas
    ].values()  # PSS salinity
    # T_s, temperature expression used in the calculation of C*
    T_s = np.log((pQ(298.15, "degC") - T) / T_K)
    # C*, concentration calculated from Hamme and Emerson 2004. Multiplication by 10^-6 to have units of mol/kg
    Cstar = (
        np.exp(
            A0
            + A1 * T_s
            + A2 * T_s**2
            + A3 * T_s**3
            + S * (B0 + B1 * T_s + B2 * T_s**2)
        )
    ) * pQ(1e-6, f"mol_{gas}/kg")
    return Cstar


"""@unit_aware(
    {"gas": None, "T": "degC", "S": "permille", "p": "atm", "ab": None}, "mol_g/kg"
)
def __calc_Ceq(
    gas,
    T: float,
    S: float,
    p: float,
    ab="default",
) -> float:
    # vapour pressure over the water, calculated according to Dyck and Peschke 1995 (atm)
    e_w = new_calc_vappres(T).to("atm")
    # calculation of C*, the gas solubility/water-side concentration expressed in units of mol/kg
    Cstar = gas.calc_Cstar(T, S, ab)
    # factor to account for pressure
    pref = (p - e_w) / (PAT - e_w)

    return pref * Cstar"""


if __name__ == "__main__":
    from pagos.visast_util import graph

    graph(__calc_Cstar_J19.ast)
