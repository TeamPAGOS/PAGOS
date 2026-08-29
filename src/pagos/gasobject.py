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
    SF6_BULLISTER_02_COEFFS,
    TPW,
    WANNINKHOF_92_COEFFS,
    WANNINKHOF_92_SALTFACTOR_COEFFS,
    ArNeN2_HAMMEEMERSON_04_COEFFS,
)
from pagos.newcore import pCalc as pC
from pagos.newwater import calc_kinvisc

PREDEFINED_GASES = ["He", "Ne", "Ar", "Kr", "Xe", "N2", "CFC11", "CFC12", "SF6"]

# Gases grouped according to properties
STABLETRANSIENTGASES = ["CFC11", "CFC12", "SF6"]
NOBLEGASES = ["He", "Ne", "Ar", "Kr", "Xe"]
BIOLOGICALGASES = ["N2"]


class Gas:
    def __init__(self, name, *kwargs):
        self.msg = ""
        self._initialise_from_name(name)
        print(self.msg)

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
            self.calc_sc = NotImplementedError(
                f"calc_Sc is not defined for {self.name}"
            )
        self.calc_Sc = pC.make_mcmethod(self.calc_Sc, 0.0)

        # initialise C* calculation
        if self.name in NOBLEGASES:
            self.calc_Cstar = lambda T, S: self.__calc_Cstar_J19(T, S)
        elif self.name in {"CFC11", "CFC12"}:
            self.calc_Cstar = lambda T, S, ab="default": self.__calc_Cstar_WW85(
                T, S, ab
            )
        elif self.name in {"SF6"}:
            self.calc_Cstar = lambda T, S, ab="default": self.__calc_Cstar_B02(T, S, ab)
        elif self.name in {"N2"}:
            self.calc_Cstar = lambda T, S: self.__calc_Cstar_HE04(T, S)
        else:
            self.calc_Cstar = NotImplementedError(
                f"calc_Cstar is not defined for {self.name}"
            )
        self.calc_Cstar = pC.make_mcmethod(self.calc_Cstar, 0.0)

    @pC.unit_aware((None, "degC", "permille"), "dimensionless")
    def __calc_Sc_W92(
        self,
        T: float,
        S: float,
    ) -> float:
        """Calculates the Schmidt number Sc of given gas in seawater.\\
        **Default input units** --- `T`:°C, `S`:‰\\
        **Output units** --- dimensionless\\
        Method of calculation:
        Hamme and Emerson 2017, combination of various methods.
        Based off of Roberta Hamme's Matlab scripts, available at
        https://oceangaseslab.uvic.ca/download.html.
        3. 'auto':
            - Default to HE17
            - Transient stable gases (CFCs and SF6) use W92 because required data for HE17
            with these gases are not available.

        :param gas: Gas(es) for which Sc should be calculated
        :type gas: str
        :param T: Temperature
        :type T: float
        :param S: Salinity
        :type S: float
        :param method: Sc calculation method, defaults to 'auto'
        :type method: str, optional
        :raises ValueError: if `S` < 0
        :raises ValueError: if invalid `method` is given
        :return: Calculated Schmidt number
        :rtype: float
        """

        # Wanninkhof 1992 method
        # salt factor for if the water is salty or not. Threshold is low, therefore this method is only recommended
        # for waters with salinity approx. equal to 34 g/kg.
        if S > 5:
            f0, f1, f2, f3 = (
                WANNINKHOF_92_SALTFACTOR_COEFFS[s] for s in ["f0", "f1", "f2", "f3"]
            )
            saltfactor = (f0 + f1 * T + f2 * T**2 + f3 * T**3) / 0.94
        elif 0 <= S <= 5:
            saltfactor = 1
        else:
            raise ValueError("S must be a number >= 0.")
        A, B, C, D = (WANNINKHOF_92_COEFFS[self.name][s] for s in ["A", "B", "C", "D"])
        Sc = saltfactor * (A - B * T + C * T**2 - D * T**3)
        return Sc

    @pC.unit_aware((None, "degC", "permille"), "dimensionless")
    def __calc_Sc_HE17(self, T: float, S: float) -> float:
        """Calculates the Schmidt number Sc of given gas in seawater.\\
        **Default input units** --- `T`:°C, `S`:‰\\
        **Output units** --- dimensionless\\
        Method of calculation:
        Wanninkhof 1992.
        Threshold between fresh and salty water chosen to be S = 5 g/kg, but isn't
        well defined, so this method is best used only for waters with salinities
        around 34 g/kg.

        :param gas: Gas(es) for which Sc should be calculated
        :type gas: str
        :param T: Temperature
        :type T: float
        :param S: Salinity
        :type S: float
        :param method: Sc calculation method, defaults to 'auto'
        :type method: str, optional
        :return: Calculated Schmidt number
        :rtype: float
        """
        # Hamme & Emerson 2017 method
        # Eyring diffusivity calculation
        # units (cm2/s, kJ/mol)
        (A_coeff, activation_energy) = (
            EYRING_36_COEFFS[self.name][s] for s in ["A", "Ea"]
        )
        D0 = A_coeff * np.exp(-activation_energy / (MGC * (T + TPW)))  # -> cm2/s
        # Saltwater correction used by R. Hamme in her Matlab script (https://oceangaseslab.uvic.ca/download.html)
        D = D0 * (1 - 0.049 * S / EYRING_36_HAMME_SALT_CORRECTION)  # PSS78 as Salinity
        # Kinematic viscosity calculation
        nu_sw = calc_kinvisc(T, S)
        Sc = nu_sw / D
        return Sc

    @pC.unit_aware((None, "degC", "permille"), "mol/kg")
    def __calc_Cstar_J19(self, T: float, S: float) -> float:
        T_K = T + TPW
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
        ) * pQ(1, "mol/kg")
        return Cstar

    @pC.unit_aware((None, "degC", "permille", None), "mol/kg")
    def __calc_Cstar_WW85(self, T: float, S: float, ab: str = "default") -> float:
        T_K = T + TPW
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
        ) * pQ(1, "mol/kg")
        return Cstar

    @pC.unit_aware((None, "degC", "permille", None), "mol/kg")
    def __calc_Cstar_B02(self, T: float, S: float, ab: str = "default") -> float:
        T_K = T + TPW
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
        ) * pQ(1, "mol/kg")
        return Cstar

    @pC.unit_aware((None, "degC", "permille"), "mol/kg")
    def __calc_Cstar_HE04(self, T: float, S: float) -> float:
        T_K = T + TPW
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
            * 1e-6
        ) * pQ(1, "mol/kg")
        return Cstar


# TESTING
He = Gas("He")
CFC12 = Gas("CFC12")
SF6 = Gas("SF6")
Kr = Gas("Kr")
Ar = Gas("Ar")
Xe = Gas("Xe")
Ne = Gas("Ne")
N2 = Gas("N2")

from pagos.newcore import pQ
from pagos.newcore import set_warn_nonmult
from pagos.gas import calc_Cstar

set_warn_nonmult(False)

print(He.calc_Sc(pQ(4, "degC"), pQ(8, "permille")))
print(He.calc_Sc(4, pQ(0.8, "percent")))
print(CFC12.calc_Sc(pQ(4, "degC"), pQ(8, "permille")))

print(He.calc_Cstar(4, 8), calc_Cstar("He", 4, 8))
print(CFC12.calc_Cstar(4, 8), calc_Cstar("CFC12", 4, 8))
print(SF6.calc_Cstar(4, 8), calc_Cstar("SF6", 4, 8))
print(Kr.calc_Cstar(4, 8), calc_Cstar("Kr", 4, 8))
print(Ar.calc_Cstar(4, 8), calc_Cstar("Ar", 4, 8))
print(Xe.calc_Cstar(4, 8), calc_Cstar("Xe", 4, 8))
print(Ne.calc_Cstar(4, 8), calc_Cstar("Ne", 4, 8))
print(N2.calc_Cstar(4, 8), calc_Cstar("N2", 4, 8))
