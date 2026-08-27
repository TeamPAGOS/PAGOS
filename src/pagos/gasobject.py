import numpy as np

from pagos.newconstants import (
    ABUNDANCES,
    EYRING_36_COEFFS,
    EYRING_36_HAMME_SALT_CORRECTION,
    MGC,
    MOLAR_MASSES,
    MOLAR_VOLUMES,
    NG_JENKINS_19_COEFFS,
    TPW,
    WANNINKHOF_92_COEFFS,
    WANNINKHOF_92_SALTFACTOR_COEFFS,
)
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
        # Schmidt number calculation
        if name in STABLETRANSIENTGASES:
            self.calc_Sc = lambda T, S: self.__calc_Sc_W92(T, S)
        elif name in NOBLEGASES:
            self.calc_Sc = lambda T, S: self.__calc_Sc_HE17(T, S)
        else:
            self.calc_sc = NotImplementedError(
                f"calc_Sc is not defined for {self.name}"
            )

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


# TESTING
He = Gas("He")
CFC12 = Gas("CFC12")

from pagos.newcore import pQ
from pagos.newcore import set_warn_nonmult

set_warn_nonmult(False)

print(He.calc_Sc(pQ(4, "degC"), pQ(8, "permille")))
print(CFC12.calc_Sc(pQ(4, "degC"), pQ(8, "permille")))
