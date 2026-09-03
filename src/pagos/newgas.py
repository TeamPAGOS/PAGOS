"""
Functions for calculating the properties of gases dissolved in water
"""

import numpy as np

from pagos.newconstants import (
    ABUNDANCES,
    CFC_WARNERWEISS_85_COEFFS,
    EYRING_36_COEFFS,
    ICE_FRACTIONATION_COEFFS,
    MGC,
    MMW,
    MOLAR_MASSES,
    MOLAR_VOLUMES,
    NG_JENKINS_19_COEFFS,
    PAT,
    SF6_BULLISTER_02_COEFFS,
    TPW,
    WANNINKHOF_92_COEFFS,
    ArNeN2_HAMMEEMERSON_04,
)
from pagos.newcore import pCalc as pC
from pagos.newwater import (
    calc_dens,
    calc_dens_Sderiv,
    calc_dens_Tderiv,
    calc_kinvisc,
    calc_vappres,
    calc_vappres_Tderiv,
)


# Getters
def mv(gas):
    try:
        return MOLAR_VOLUMES[gas]
    except KeyError:
        raise KeyError(
            f"mv({gas}) failed because {gas} has no implemented molar volume."
        )


def mm(gas):
    try:
        return MOLAR_MASSES[gas]
    except KeyError:
        raise KeyError(f"mm({gas}) failed because {gas} has no implemented molar mass.")


def abn(gas):
    try:
        return ABUNDANCES[gas]
    except KeyError:
        raise KeyError(
            f"abn({gas}) failed because {gas} has no implemented atomspheric abundance."
        )


def calc_Sc(
    gas: str,
    T: float,
    S: float,
    method: str = "auto",
) -> float:
    """Calculates the Schmidt number Sc of given gas in seawater.\\
    **Default input units** --- `T`:°C, `S`:‰\\
    **Output units** --- dimensionless\\
    There are three methods of calculation:
        - 'HE17'
            - Hamme and Emerson 2017, combination of various methods.
            - Based off of Roberta Hamme's Matlab scripts, available at
              https://oceangaseslab.uvic.ca/download.html.
        - 'W92'
            - Wanninkhof 1992
            - Threshold between fresh and salty water chosen to be S = 5 g/kg, but isn't
              well defined, so this method is best used only for waters with salinities
              around 34 g/kg.
        - 'auto':
            - Default to HE17
            - Transient stable gases (CFCs and SF6) use W92 because required data for HE17
              with these gases are not available.

    :param gas: Gas(es) for which Sc should be calculated
    :type gas: str | Iterable[str]
    :param T: Temperature
    :type T: float | Quantity
    :param S: Salinity
    :type S: float | Quantity
    :param method: Sc calculation method, defaults to 'auto'
    :type method: str, optional
    :raises ValueError: if `S` < 0
    :raises ValueError: if invalid `method` is given
    :return: Calculated Schmidt number
    :rtype: float | Quantity | Iterable[float] | Iterable[Quantity]
    """

    if method == "auto":
        if gas in STABLETRANSIENTGASES:
            method = "W92"
        else:
            method = "HE17"

    # Wanninkhof 1992 method
    if method == "W92":
        # salt factor for if the water is salty or not. Threshold is low, therefore this method is only recommended
        # for waters with salinity approx. equal to 34 g/kg.
        if S > 5:
            saltfactor = (1.052 + 1.3e-3 * T + 5e-6 * T**2 - 5e-7 * T**3) / 0.94
        elif 0 <= S <= 5:
            saltfactor = 1
        else:
            raise ValueError("S must be a number >= 0.")
        (A, B, C, D) = (wkc(gas)[s] for s in ["A", "B", "C", "D"])
        Sc = saltfactor * (A - B * T + C * T**2 - D * T**3)
    # Hamme & Emerson 2017 method
    elif method == "HE17":
        # Eyring diffusivity calculation
        # units (cm2/s, kJ/mol)
        (A_coeff, activation_energy) = (erc(gas)[s] for s in ["A", "Ea"])
        # *1000 in exponent to convert kJ/J to J/J
        D0 = A_coeff * np.exp(-activation_energy / (MGC * (T + TPW)) * 1000)  # -> cm2/s
        # Saltwater correction used by R. Hamme in her Matlab script (https://oceangaseslab.uvic.ca/download.html)
        # *1e-4 to convert cm2/s to m2/s
        D = D0 * (1 - 0.049 * S / 35.5) * 1e-4  # PSS78 as Salinity
        # Kinematic viscosity calculation
        nu_sw = calc_kinvisc(T, S, magnitude=True)
        Sc = nu_sw / D
    else:
        raise ValueError(
            "%s is not a valid method. Try 'auto', 'HE17' or 'W92'" % (method)
        )
