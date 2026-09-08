from timeit import timeit

import numpy as np

from pagos.newconstants import (
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
from pagos.newcore import PAGOSQuantity, _set_fast
from pagos.newcore import pCalc as pC
from pagos.newwater import calc_kinvisc, calc_vappres

PREDEFINED_GASES = ["He", "Ne", "Ar", "Kr", "Xe", "N2", "CFC11", "CFC12", "SF6"]

# Gases grouped according to properties
STABLETRANSIENTGASES = ["CFC11", "CFC12", "SF6"]
NOBLEGASES = ["He", "Ne", "Ar", "Kr", "Xe"]
BIOLOGICALGASES = ["N2"]


class Gas:
    def __init__(self, name, *kwargs):
        self.msg = ""
        self._initialise_from_name(name)
        print(self.msg, end="")

    def _initialise_from_name(self, name):
        self.name = name

        if self.name not in PREDEFINED_GASES:
            self.msg += f"Tried to intialise {name} but the name of the gas is not implemented!\n"

        # initialise gas properties
        try:
            self.abundance = ABUNDANCES[self.name]
        except KeyError:
            self.abundance = NotImplementedError(
                f"{self.name} has no implemented atmospheric abundance."
            )

        try:
            self.molar_volume = MOLAR_VOLUMES[self.name]
        except KeyError:
            self.molar_volume = NotImplementedError(
                f"{self.name} has no implemented molar volume."
            )

        try:
            self.molar_mass = MOLAR_MASSES[self.name]
        except KeyError:
            self.molar_mass = NotImplementedError(
                f"{self.name} has no implemented molar mass."
            )

        # initialise methods
        # initialise Schmidt number calculation
        if self.name in STABLETRANSIENTGASES:
            self.calc_Sc = lambda T, S: self.__calc_Sc_W92(T, S)
        elif self.name in NOBLEGASES + ["N2"]:
            self.calc_Sc = lambda T, S: self.__calc_Sc_HE17(T, S)
        else:
            self.calc_Sc = NotImplementedError(
                f"calc_Sc is not defined for {self.name}"
            )
        self.calc_Sc = pC.make_mcmethod(self.calc_Sc, 0.0)

        # initialise C* calculation
        # NOTE some of the cases (e.g. noble gases) have an ab argument that does nothing!
        if self.name in NOBLEGASES:
            self.calc_Cstar = lambda T, S, ab="default": self.__calc_Cstar_J19(T, S)
        elif self.name in {"CFC11", "CFC12"}:
            self.calc_Cstar = lambda T, S, ab="default": self.__calc_Cstar_WW85(
                T, S, ab
            )
        elif self.name in {"SF6"}:
            self.calc_Cstar = lambda T, S, ab="default": self.__calc_Cstar_B02(T, S, ab)
        elif self.name in {"N2"}:
            self.calc_Cstar = lambda T, S, ab="default": self.__calc_Cstar_HE04(T, S)
        else:
            self.calc_Cstar = NotImplementedError(
                f"calc_Cstar is not defined for {self.name}"
            )
        self.calc_Cstar = pC.make_mcmethod(self.calc_Cstar, 0.0)

        # initialise Ceq calculation
        if self.name in NOBLEGASES + STABLETRANSIENTGASES + ["N2"]:
            self.calc_Ceq = lambda T, S, p, ab="default": self.__calc_Ceq(T, S, p, ab)
        else:
            self.calc_Ceq = NotImplementedError(
                f"calc_Ceq is not defined for {self.name}"
            )

    @pC.unit_aware((None, "degC", "permille"), "dimensionless")
    def __calc_Sc_W92(
        self,
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
        A, B, C, D = (WANNINKHOF_92_COEFFS[self.name][s] for s in ["A", "B", "C", "D"])
        Sc = saltfactor * (A - B * T + C * T**2 - D * T**3)
        return Sc

    @pC.unit_aware((None, "degC", "permille"), "dimensionless")
    def __calc_Sc_HE17(self, T: float, S: float) -> float:
        # Hamme & Emerson 2017 method
        # Eyring diffusivity calculation
        # units (cm2/s, kJ/mol)
        (A_coeff, activation_energy) = (
            EYRING_36_COEFFS[self.name][s] for s in ["A", "Ea"]
        )
        D0 = A_coeff * np.exp(-activation_energy / (MGC * T.to("K")))  # -> cm2/s
        # Saltwater correction used by R. Hamme in her Matlab script (https://oceangaseslab.uvic.ca/download.html)
        D = D0 * (1 - 0.049 * S / EYRING_36_HAMME_SALT_CORRECTION)  # PSS78 as Salinity
        # Kinematic viscosity calculation
        nu_sw = calc_kinvisc(T, S)
        Sc = nu_sw / D
        return Sc

    @pC.unit_aware((None, "degC", "permille"), "mol_g/kg")
    def __calc_Cstar_J19(self, T: float, S: float) -> float:
        T_K = T.to("K")
        T_N = T_K / K100
        A0, AR, AL, A1, B0, B1, B2, C0 = (
            NG_JENKINS_19_COEFFS[self.name][c]
            for c in ["A0", "AR", "AL", "A1", "B0", "B1", "B2", "C0"]
        )
        Cstar = np.exp(
            A0
            + AR / T_N
            + AL * np.log(T_N)
            + A1 * T_N
            + S * (B0 + B1 * T_N + B2 * T_N**2)
            + S**2 * C0
        ) * pQ(1, "mol_g/kg", self.name)
        return Cstar

    @pC.unit_aware((None, "degC", "permille", None), "mol_g/kg")
    def __calc_Cstar_WW85(self, T: float, S: float, ab: str = "default") -> float:
        T_K = T.to("K")
        T_N = T_K / K100
        a1, a2, a3, a4, b1, b2, b3 = CFC_WARNERWEISS_85_COEFFS[
            self.name
        ].values()  # needs S in parts per thousand
        # TODO adopt for absolute salinity??
        # abundance
        if ab == "default":
            ab = ABUNDANCES[self.name]
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
        ) * pQ(1, "mol_g/kg", self.name)
        return Cstar

    @pC.unit_aware((None, "degC", "permille", None), "mol_g/kg")
    def __calc_Cstar_B02(self, T: float, S: float, ab: str = "default") -> float:
        T_K = T.to("K")
        T_N = T_K / K100
        a1, a2, a3, b1, b2, b3 = SF6_BULLISTER_02_COEFFS[
            self.name
        ].values()  # don't know salinity unit
        # abundance
        if ab == "default":
            ab = ABUNDANCES[self.name]
        # C* = F*abundance, concentration calculated from Bullister et al. 2002
        Cstar = (
            np.exp(a1 + a2 / T_N + a3 * np.log(T_N) + S * (b1 + b2 * T_N + b3 * T_N**2))
            * ab
        ) * pQ(1, "mol_g/kg", self.name)
        return Cstar

    @pC.unit_aware((None, "degC", "permille"), "mol_g/kg")
    def __calc_Cstar_HE04(self, T: float, S: float) -> float:
        T_K = T.to("K")
        A0, A1, A2, A3, B0, B1, B2 = ArNeN2_HAMMEEMERSON_04_COEFFS[
            self.name
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
        ) * pQ(1e-6, "mol_g/kg", self.name)
        return Cstar

    @pC.unit_aware((None, "degC", "permille", "atm", None), "mol_g/kg")
    def __calc_Ceq(
        self,
        T: float,
        S: float,
        p: float,
        ab="default",
    ) -> float:
        # vapour pressure over the water, calculated according to Dyck and Peschke 1995 (atm)
        e_w = calc_vappres(T).to("atm")
        # calculation of C*, the gas solubility/water-side concentration expressed in units of mol/kg
        Cstar = self.calc_Cstar(T, S, ab)
        # factor to account for pressure
        pref = (p - e_w) / (PAT - e_w)

        return pref * Cstar


"""
Creation of Gas objects
"""
He = Gas("He")
Ne = Gas("Ne")
Ar = Gas("Ar")
Kr = Gas("Kr")
Xe = Gas("Xe")
N2 = Gas("N2")
CFC11 = Gas("CFC11")
CFC12 = Gas("CFC12")
SF6 = Gas("SF6")

gases_dict = {
    "He": He,
    "Ne": Ne,
    "Ar": Ar,
    "Kr": Kr,
    "Xe": Xe,
    "N2": N2,
    "CFC12": CFC12,
    "CFC11": CFC11,
    "SF6": SF6,
}

"""
Functional wrappers around Gas object methods
"""


def calc_Sc(
    gas: Gas | str, T: float | PAGOSQuantity, S: float | PAGOSQuantity
) -> PAGOSQuantity:
    """Calculates the Schmidt number Sc of given gas in seawater.\\
    **Default input units** --- `T`:°C, `S`:‰\\
    **Output units** --- dimensionless\\

    :param gas: Gas(es) for which Sc should be calculated
    :type gas: str
    :param T: Temperature
    :type T: float | PAGOSQuantity
    :param S: Salinity
    :type S: float | PAGOSQuantity
    :return: Calculated Schmidt number
    :rtype: PAGOSQuantity
    """
    try:
        return gas.calc_Sc(T, S)
    except AttributeError:
        try:
            return gases_dict[gas].calc_Sc(T, S)
        except KeyError:
            raise NotImplementedError(f"calc_Sc not defined for the gas {gas}.")


def calc_Cstar(
    gas: Gas | str,
    T: float | PAGOSQuantity,
    S: float | PAGOSQuantity,
    ab: str = "default",
) -> PAGOSQuantity:
    """Calculate the waterside equilibrium concentration Ceq of a given gas at water
    temperature T, salinity S and airside pressure p.\\
    **Default input units** --- `T`:°C, `S`:‰, `p`:atm\\
    **Default output units** --- mol_gas/kg_water

    :param gas: Gas(es) for which Ceq should be calculated
    :type gas: str | Iterable[str]
    :param T: Temperature
    :type T: float | PAGOSQuantity
    :param S: Salinity
    :type S: float | PAGOSQuantity
    :param p: Pressure
    :type p: float | PAGOSQuantity
    :param ab: Abundance of gas in atmosphere, defaults to "default"
    :type ab: float | PAGOSQuantity, optional
    :return: Waterside equilibrium concentration Ceq of the given gas
    :rtype: PAGOSQuantity
    """
    try:
        return gas.calc_Cstar(T, S, ab)
    except AttributeError:
        try:
            return gases_dict[gas].calc_Cstar(T, S)
        except KeyError:
            raise NotImplementedError(f"calc_Cstar not defined for the gas {gas}.")


# TIME TESTING

if __name__ == "__main__":
    from pagos.newcore import pQ
    from pagos.newcore import set_warn_nonmult

    set_warn_nonmult(False)

    totime = """He.calc_Sc(pQ(4, "degC"), pQ(8, "permille"))
He.calc_Sc(4, pQ(0.8, "percent"))
CFC12.calc_Sc(pQ(4, "degC"), pQ(8, "permille"))

He.calc_Cstar(4, 8), calc_Cstar("He", 4, 8)
CFC12.calc_Cstar(4, 8), calc_Cstar("CFC12", 4, 8)
SF6.calc_Cstar(4, 8), calc_Cstar("SF6", 4, 8)
Kr.calc_Cstar(4, 8), calc_Cstar("Kr", 4, 8)
Ar.calc_Cstar(4, 8), calc_Cstar("Ar", 4, 8)
Xe.calc_Cstar(4, 8), calc_Cstar("Xe", 4, 8)
Ne.calc_Cstar(4, 8), calc_Cstar("Ne", 4, 8)
N2.calc_Cstar(4, 8), calc_Cstar("N2", 4, 8)

He.calc_Ceq(4, 8, 0.9)
Ne.calc_Ceq(4, 8, 0.9)
Ar.calc_Ceq(4, 8, 0.9)
Kr.calc_Ceq(4, 8, 0.9)
Xe.calc_Ceq(4, 8, 0.9)
N2.calc_Ceq(4, 8, 0.9)
CFC12.calc_Ceq(4, 8, 0.9)
SF6.calc_Ceq(4, 8, 0.9)

calc_Sc(He, 4, 8),
calc_Sc("He", 4, 8),"""

    time1 = timeit(totime, globals=globals(), number=1)
    print("SLOW:", time1)
    _set_fast(True)
    time2 = timeit(totime, globals=globals(), number=1000)
    print("FAST:", time2)
