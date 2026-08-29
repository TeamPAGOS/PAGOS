from pagos.newcore import pQ

# Triple point of water (K)
TPW = pQ(273.15, "K")
# Molar mass of water (g/mol)
MMW = pQ(18.016, "g/mol")
# Absolute zero (°C)
ABZ = pQ(-273.15, "degC")
# Atmospheric pressure (Pa)
PAT = pQ(101325, "Pa")
# Molar gas constant (J/mol/K)
MGC = pQ(8.31446, "J/mol/K")
# Specific heat of water at 0°C (J/kg/K)
# https://www.engineeringtoolbox.com/specific-heat-capacity-water-d_660.html
CPW = pQ(4219.9, "J/kg/K")
# Latent heat of fusion of water (J/kg)
LFW = pQ(333.55e3, "J/kg")

# constants for water.py calculations
GILL_82_COEFFS = {
    "a0": pQ(999.842594, "kg/m^3"),
    "a1": pQ(0.06793952, "kg/m^3/K"),
    "a2": pQ(-0.00909529, "kg/m^3/K^2"),
    "a3": pQ(0.0001001685, "kg/m^3/K^3"),
    "a4": pQ(-0.000001120083, "kg/m^3/K^4"),
    "a5": pQ(0.000000006536332, "kg/m^3/K^5"),
    "b0": pQ(0.824493, "kg/m^3/permille"),
    "b1": pQ(-0.0040899, "kg/m^3/permille/K"),
    "b2": pQ(0.000076438, "kg/m^3/permille/K^2"),
    "b3": pQ(-0.00000082467, "kg/m^3/permille/K^3"),
    "b4": pQ(0.0000000053875, "kg/m^3/permille/K^4"),
    "c0": pQ(-0.00572466, "kg/m^3/permille^(3/2)"),
    "c1": pQ(0.00010227, "kg/m^3/permille^(3/2)/K"),
    "c2": pQ(-0.0000016546, "kg/m^3/permille^(3/2)/K^2"),
    "d0": pQ(0.00048314, "kg/m^3/permille^2"),
}

DYCK_PESCHKE_95_COEFFS = {"p0": pQ(6.1078, "mbar"), "c": pQ(239.7, "delta_degC")}

SHARQAWY_10_COEFFS = {
    "m0": pQ(4.2844e-5, "kg/m/s"),
    "m1": pQ(1, "kg/m/s"),
    "m2": pQ(0.157, "delta_degC^-2"),
    "m3": pQ(64.993, "delta_degC"),
    "a1": pQ(0.01998, "delta_degC^-1"),
    "a2": pQ(9.52e-5, "delta_degC^-2"),
    "b1": pQ(0.07561, "delta_degC^-1"),
    "b2": pQ(4.724e-4, "delta_degC^-2"),
}


# constants for gas.py calculations
ABUNDANCES = {
    "He": 5.24e-6,
    "Ne": 18.18e-6,
    "Ar": 0.934e-2,
    "Kr": 1.14e-6,
    "Xe": 0.087e-6,
    "CFC11": 218e-12,
    "CFC12": 488e-12,
    "SF6": 11.5e-12,
    "N2": 0.781,
}

# molar volumes in units of cm3/mol, referenced to 0 degC and 1 atm = 1013.25 mbar, except
# CFC11, whichreferenced to its boiling point of 297 K
# Sources: noble gases, Benson & Krause 1976; stable transient gases, NIST
# NOTE: cannot find them in Benson and Krause
# TODO more digits for CFCs
MOLAR_VOLUMES = {
    "He": pQ(22425.8703182828, "cc/mol"),
    "Ne": pQ(22424.8703182828, "cc/mol"),
    "Ar": pQ(22392.5703182828, "cc/mol"),
    "Kr": pQ(22352.8703182828, "cc/mol"),
    "Xe": pQ(22256.9703182828, "cc/mol"),
    "SF6": pQ(22075.5738997, "cc/mol"),
    "CFC11": pQ(23807, "cc/mol"),
    "CFC12": pQ(21844, "cc/mol"),
    "N2": pQ(22403.8633496, "cc/mol"),
}

# molar masses of the gases (g/mol)
MOLAR_MASSES = {
    "He": pQ(4.002602, "g/mol"),
    "Ne": pQ(20.1797, "g/mol"),
    "Ar": pQ(39.948, "g/mol"),
    "Kr": pQ(83.798, "g/mol"),
    "Xe": pQ(131.293, "g/mol"),
    "SF6": pQ(146.06, "g/mol"),
    "CFC11": pQ(137.37, "g/mol"),
    "CFC12": pQ(120.91, "g/mol"),
    "N2": pQ(28.0134, "g/mol"),
}

# useful normalising constant for solubility constans
K100 = pQ(100, "K")

# coefficients from Jenkins et al. 2019 solubility formula for noble gases
NG_JENKINS_19_COEFFS = {
    "He": {
        "A0": -178.1424,
        "AR": 217.5991,
        "AL": 140.7506,
        "A1": -23.01954,
        "B0": pQ(-0.038129, "permille^-1"),
        "B1": pQ(0.01919, "permille^-1"),
        "B2": pQ(-0.0026898, "permille^-1"),
        "C0": pQ(-0.00000255157, "permille^-2"),
    },
    "Ne": {
        "A0": -274.1329,
        "AR": 352.6201,
        "AL": 226.9676,
        "A1": -37.13393,
        "B0": pQ(-0.06386, "permille^-1"),
        "B1": pQ(0.035326, "permille^-1"),
        "B2": pQ(-0.0053258, "permille^-1"),
        "C0": pQ(0.0000128233, "permille^-2"),
    },
    "Ar": {
        "A0": -227.4607,
        "AR": 305.4347,
        "AL": 180.5278,
        "A1": -27.9945,
        "B0": pQ(-0.066942, "permille^-1"),
        "B1": pQ(0.037201, "permille^-1"),
        "B2": pQ(-0.0056364, "permille^-1"),
        "C0": pQ(-5.30325e-06, "permille^-2"),
    },
    "Kr": {
        "A0": -122.4694,
        "AR": 153.5654,
        "AL": 70.1969,
        "A1": -8.52524,
        "B0": pQ(-0.049522, "permille^-1"),
        "B1": pQ(0.024434, "permille^-1"),
        "B2": pQ(-0.0033968, "permille^-1"),
        "C0": pQ(4.19208e-06, "permille^-2"),
    },
    "Xe": {
        "A0": -224.51,
        "AR": 292.8234,
        "AL": 157.6127,
        "A1": -22.66895,
        "B0": pQ(-0.084915, "permille^-1"),
        "B1": pQ(0.047996, "permille^-1"),
        "B2": pQ(-0.0073595, "permille^-1"),
        "C0": pQ(6.69292e-06, "permille^-2"),
    },
}

# coefficients from Wanninkhof 1992 formula for Schmidt number. Xe values obtained by
# fitting curve from Jähne 1987 onto the Wanninkhof curve. These are values for Sc in
# freshwater.
WANNINKHOF_92_COEFFS = {
    "He": {
        "A": pQ(377.09, "dimensionless"),
        "B": pQ(19.154, "K^-1"),
        "C": pQ(0.50137, "K^-2"),
        "D": pQ(0.005669, "K^-3"),
    },
    "Ne": {
        "A": pQ(764.00, "dimensionless"),
        "B": pQ(42.234, "K^-1"),
        "C": pQ(1.1581, "K^-2"),
        "D": pQ(0.013405, "K^-3"),
    },
    "Ar": {
        "A": pQ(1759.7, "dimensionless"),
        "B": pQ(117.37, "K^-1"),
        "C": pQ(3.6959, "K^-2"),
        "D": pQ(0.046527, "K^-3"),
    },
    "Kr": {
        "A": pQ(2032.7, "dimensionless"),
        "B": pQ(127.55, "K^-1"),
        "C": pQ(3.7621, "K^-2"),
        "D": pQ(0.045236, "K^-3"),
    },
    "Xe": {
        "A": pQ(2589.7, "dimensionless"),
        "B": pQ(153.39, "K^-1"),
        "C": pQ(3.9570, "K^-2"),
        "D": pQ(0.039801, "K^-3"),
    },
    "SF6": {
        "A": pQ(3255.3, "dimensionless"),
        "B": pQ(217.13, "K^-1"),
        "C": pQ(6.8370, "K^-2"),
        "D": pQ(0.086070, "K^-3"),
    },
    "CFC11": {
        "A": pQ(3723.7, "dimensionless"),
        "B": pQ(248.37, "K^-1"),
        "C": pQ(7.8208, "K^-2"),
        "D": pQ(0.098455, "K^-3"),
    },
    "CFC12": {
        "A": pQ(3422.7, "dimensionless"),
        "B": pQ(228.30, "K^-1"),
        "C": pQ(7.1886, "K^-2"),
        "D": pQ(0.090496, "K^-3"),
    },
    "N2": {
        "A": pQ(1970.7, "dimensionless"),
        "B": pQ(131.45, "K^-1"),
        "C": pQ(4.1390, "K^-2"),
        "D": pQ(0.052106, "K^-3"),
    },
}
WANNINKHOF_92_SALTFACTOR_COEFFS = {
    "f0": pQ(1.052, "dimensionless"),
    "f1": pQ(1.3e-3, "K^-1"),
    "f2": pQ(5e-6, "K^-2"),
    "f3": pQ(-5e-7, "K^-3"),
}

# coefficients from the Jähne 1987 formula (Eyring formula) for Schmidt number. Ar was
# interpolated from Jähne 1987 and N2 is from Ferrel and Himmelblau 1967.
EYRING_36_COEFFS = {
    "He": {"A": pQ(0.00818, "cm^2/s"), "Ea": pQ(11.70, "kJ/mol")},
    "Ne": {"A": pQ(0.01608, "cm^2/s"), "Ea": pQ(14.84, "kJ/mol")},
    "Ar": {"A": pQ(0.02227, "cm^2/s"), "Ea": pQ(16.68, "kJ/mol")},
    "Kr": {"A": pQ(0.06393, "cm^2/s"), "Ea": pQ(20.20, "kJ/mol")},
    "Xe": {"A": pQ(0.09007, "cm^2/s"), "Ea": pQ(21.61, "kJ/mol")},
    "N2": {"A": pQ(0.03412, "cm^2/s"), "Ea": pQ(18.50, "kJ/mol")},
}
EYRING_36_HAMME_SALT_CORRECTION = pQ(35.5, "permille")

# coefficients from Weiss and Kyser 1978 solubility formula for Kr
Kr_WEISSKYSER_78_COEFFS = {
    "Kr": {
        "A1": -57.2596,
        "A2": 87.4242,
        "A3": 22.9332,
        "B1": -0.008723,
        "B2": -0.002793,
        "B3": 0.0012398,
    }
}

# coefficients from Warner and Weiss solubility formula for CFC-11 and CFC-12
CFC_WARNERWEISS_85_COEFFS = {
    "CFC11": {
        "a1": -232.0411,
        "a2": 322.5546,
        "a3": 120.4956,
        "a4": -1.39165,
        "b1": pQ(-0.146531, "permille^-1"),
        "b2": pQ(0.093621, "permille^-1"),
        "b3": pQ(-0.0160693, "permille^-1"),
    },
    "CFC12": {
        "a1": -220.2120,
        "a2": 301.8695,
        "a3": 114.8533,
        "a4": -1.39165,
        "b1": pQ(-0.147718, "permille^-1"),
        "b2": pQ(0.093175, "permille^-1"),
        "b3": pQ(-0.0157340, "permille^-1"),
    },
}

# coefficients from Bullister et al. 2002 solubility formula for SF6
SF6_BULLISTER_02_COEFFS = {
    "SF6": {
        "a1": -82.1639,
        "a2": 120.152,
        "a3": 30.6372,
        "b1": pQ(0.0293201, "permille^-1"),
        "b2": pQ(-0.0351974, "permille^-1"),
        "b3": pQ(0.00740056, "permille^-1"),
    }
}

# coefficients from Hamme and Emerson 2004 solubility formula for Ar, Ne and N2
ArNeN2_HAMMEEMERSON_04_COEFFS = {
    "N2": {
        "A0": 6.42931,
        "A1": 2.92704,
        "A2": 4.32531,
        "A3": 4.69149,
        "B0": pQ(-7.44129e-3, "permille^-1"),
        "B1": pQ(-8.02566e-3, "permille^-1"),
        "B2": pQ(-1.46775e-2, "permille^-1"),
    },
    # these next two are not used, Jenkins 2019 is more up-to-date
    "Ne": {
        "A0": 2.18156,
        "A1": 1.29108,
        "A2": 2.12504,
        "A3": 0,
        "B0": pQ(-5.94737e-3, "permille^-1"),
        "B1": pQ(-5.13896e-3, "permille^-1"),
        "B2": pQ(0, "permille^-1"),
    },
    "Ar": {
        "A0": 2.79150,
        "A1": 3.17609,
        "A2": 4.13116,
        "A3": 4.90379,
        "B0": pQ(-6.96233e-3, "permille^-1"),
        "B1": pQ(-7.66670e-3, "permille^-1"),
        "B2": pQ(-1.16888e-2, "permille^-1"),
    },
}

# ice fractionation coefficients for dissolved gases undergoing freezing from seawater to
# sea ice. NGs are from Loose et al. 2023. For salt, 0.3 was assumed according to
# Loose 2016. Others assumed to be 0 for now.
# TODO update these after review of the literature
ICE_FRACTIONATION_COEFFS = {
    "He": 1.33,
    "Ne": 0.83,
    "Ar": 0.49,
    "Kr": 0.4,
    "Xe": 0.5,
    "SF6": 0,
    "CFC11": 0,
    "CFC12": 0,
    "S": 0.3,
}
