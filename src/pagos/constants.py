"""
Useful constants for the PAGOS package, all as Quantity objects.
"""
from pint import UnitRegistry, Context

"""
PHYSICAL CONSTANTS

These are generic quantities that will be used throughout the PAGOS package. They do not include
their units in the definition, i.e. they are not Quantity objects.
"""
# Triple point of water (K)
TPW = 273.15
# Molar mass of water (g/mol)
MMW = 18.016
# Absolute zero (°C)
ABZ = -273.15
# Atmospheric pressure (Pa)
PAT = 101325
# Molar gas constant (J/mol/K)
MGC = 8.31446
# Specific heat of water at 0°C (J/kg/K)
#https://www.engineeringtoolbox.com/specific-heat-capacity-water-d_660.html
CPW = 4219.9
# Latent heat of fusion of water (J/kg)
LFW = 333.55e3


"""
WATER FUNCTION CONSTANTS
"""
# Density coefficients
GILL_82_COEFFS = dict(
a0 = 999.842594,
a1 = 0.06793952,
a2 = -0.00909529,
a3 = 0.0001001685,
a4 = -0.000001120083,
a5 = 0.000000006536332,
b0 = 0.824493,
b1 = -0.0040899,
b2 = 0.000076438,
b3 = -0.00000082467,
b4 = 0.0000000053875,
c0 = -0.00572466,
c1 = 0.00010227,
c2 = -0.0000016546,
d0 = 0.00048314
)


"""
NON-NUMERICAL CONSTANTS
"""
# TODO do these belong here, or in core? Or in another file?
# names of gases, and groupings by properties
NOBLEGASES = ['He', 'Ne', 'Ar', 'Kr', 'Xe']
STABLETRANSIENTGASES = ['CFC11', 'CFC12', 'SF6']
BIOLOGICALGASES = ['N2']


"""
GAS FUNCTION CONSTANTS
"""
# gas abundances
ABUNDANCES = dict(He=5.24E-6, Ne=18.18E-6, Ar=0.934E-2, Kr=1.14E-6, Xe=0.087E-6, CFC11=218e-12, CFC12=488e-12, SF6=11.5e-12, N2=0.781)

# molar volumes in units of cm3/mol, referenced to 0 degC and 1 atm = 1013.25 mbar, except
# CFC11, whichreferenced to its boiling point of 297 K
# Sources: noble gases, Benson & Krause 1976; stable transient gases, NIST
# NOTE: cannot find them in Benson and Krause
# TODO more digits for CFCs
MOLAR_VOLUMES = dict(He=22425.8703182828, Ne=22424.8703182828, Ar=22392.5703182828, Kr=22352.8703182828, Xe=22256.9703182828,
                     SF6=22075.5738997, CFC11=23807, CFC12=21844,
                     N2=22403.8633496)

# molar masses of the gases (g/mol)
MOLAR_MASSES = dict(He=4.002602, Ne=20.1797, Ar=39.948, Kr=83.798, Xe=131.293, SF6=146.06, CFC11=137.37, CFC12=120.91, N2=28.0134)

# coefficients from Jenkins et al. 2019 solubility formula for noble gases
NG_JENKINS_19_COEFFS = dict(
    He={'A1': -178.1424, 'A2': 217.5991, 'A3': 140.7506, 'A4': -23.01954, 'B1': -0.038129, 'B2': 0.01919,
        'B3': -0.0026898, 'C1': -0.00000255157},
    Ne={'A1': -274.1329, 'A2': 352.6201, 'A3': 226.9676, 'A4': -37.13393, 'B1': -0.06386, 'B2': 0.035326,
        'B3': -0.0053258, 'C1': 0.0000128233},
    Ar={'A1': -227.4607, 'A2': 305.4347, 'A3': 180.5278, 'A4': -27.9945, 'B1': -0.066942, 'B2': 0.037201,
        'B3': -0.0056364, 'C1': -5.30325E-06},
    Kr={'A1': -122.4694, 'A2': 153.5654, 'A3': 70.1969, 'A4': -8.52524, 'B1': -0.049522, 'B2': 0.024434,
        'B3': -0.0033968, 'C1': 4.19208E-06},
    Xe={'A1': -224.51, 'A2': 292.8234, 'A3': 157.6127, 'A4': -22.66895, 'B1': -0.084915, 'B2': 0.047996,
        'B3': -0.0073595, 'C1': 6.69292E-06}
)

# coefficients from Wanninkhof 1992 formula for Schmidt number. Xe values obtained by
# fitting curve from Jähne 1987 onto the Wanninkhof curve. These are values for Sc in
# freshwater.
WANNINKHOF_92_COEFFS = dict(
    He = {'A': 377.09, 'B': 19.154, 'C': 0.50137, 'D': 0.005669},
    Ne = {'A': 764.00, 'B': 42.234, 'C': 1.1581, 'D': 0.013405},
    Ar = {'A': 1759.7, 'B': 117.37, 'C': 3.6959, 'D': 0.046527},
    Kr = {'A': 2032.7, 'B': 127.55, 'C': 3.7621, 'D': 0.045236},
    Xe = {'A': 2589.7, 'B': 153.39, 'C': 3.9570, 'D': 0.039801},
    SF6 = {'A': 3255.3, 'B': 217.13, 'C': 6.8370, 'D': 0.086070},
    CFC11 = {'A': 3723.7, 'B': 248.37, 'C': 7.8208, 'D': 0.098455},
    CFC12 = {'A': 3422.7, 'B': 228.30, 'C': 7.1886, 'D': 0.090496},
    N2 = {'A': 1970.7, 'B': 131.45, 'C': 4.1390, 'D': 0.052106}
)

# coefficients from the Jähne 1987 formula (Eyring formula) for Schmidt number. Ar was
# interpolated from Jähne 1987 and N2 is from Ferrel and Himmelblau 1967.
EYRING_36_COEFFS = dict(
    He = {'A': .00818, 'Ea': 11.70},
    Ne = {'A': .01608, 'Ea': 14.84},
    Ar = {'A': .02227, 'Ea': 16.68},
    Kr = {'A': .06393, 'Ea': 20.20},
    Xe = {'A': .09007, 'Ea': 21.61},
    N2 = {'A': .03412, 'Ea': 18.50}
)
# coefficients from Weiss and Kyser 1978 solubility formula for Kr
Kr_WEISSKYSER_78_COEFFS = dict(
    Kr={'A1':-57.2596, 'A2':87.4242, 'A3':22.9332, 'B1':-0.008723, 'B2':-0.002793, 'B3':0.0012398}
)

# coefficients from Warner and Weiss solubility formula for CFC-11 and CFC-12
CFC_WARNERWEISS_85_COEFFS = dict(
    CFC11={'a1': -232.0411, 'a2': 322.5546, 'a3': 120.4956, 'a4': -1.39165, 'b1': -0.146531, 'b2': 0.093621,
           'b3': -0.0160693},
    CFC12={'a1': -220.2120, 'a2': 301.8695, 'a3': 114.8533, 'a4': -1.39165, 'b1': -0.147718, 'b2': 0.093175,
           'b3': -0.0157340}
)

# coefficients from Bullister et al. 2002 solubility formula for SF6
SF6_BULLISTER_02_COEFFS = dict(
    SF6={'a1': -82.1639, 'a2': 120.152, 'a3': 30.6372, 'b1': 0.0293201, 'b2': -0.0351974, 'b3': 0.00740056}
)

# coefficients from Hamme and Emerson 2004 solubility formula for Ar, Ne and N2
ArNeN2_HAMMEEMERSON_04 = dict(
    N2={'A0': 6.42931, 'A1': 2.92704, 'A2': 4.32531, 'A3': 4.69149, 'B0': -7.44129e-3, 'B1': -8.02566e-3, 'B2': -1.46775e-2},
    # these next two are not used, Jenkins 2019 is more up-to-date
    Ne={'A0': 2.18156, 'A1': 1.29108, 'A2': 2.12504, 'A3': 0, 'B0': -5.94737e-3, 'B1': -5.13896e-3, 'B2':0},
    Ar={'A0': 2.79150, 'A1': 3.17609, 'A2': 4.13116, 'A3': 4.90379, 'B0': -6.96233e-3, 'B1': -7.66670e-3, 'B2': -1.16888e-2}
)

# ice fractionation coefficients for dissolved gases undergoing freezing from seawater to
# sea ice. NGs are from Loose et al. 2023. For salt, 0.3 was assumed according to
# Loose 2016. Others assumed to be 0 for now.
# TODO update these after review of the literature
ICE_FRACTIONATION_COEFFS = dict(He=1.33, Ne=0.83, Ar=0.49, Kr=0.4, Xe=0.5, SF6=0, CFC11=0, CFC12=0, S=0.3)
