from pagos.newcore import pQ

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
