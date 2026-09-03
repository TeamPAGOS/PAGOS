# strings with unit definitions. Will be imported using ureg.define in pagos.core

PAGOSUnits = {
    "gram_gas": "gram_gas = [mass_gas] = g_gas = g_g",
    "mole_gas": "mole_gas = [amount_gas] = mol_gas = mol_g",
}

PAGOSDims = {
    "[mass_gas]",
    "[amount_gas]",
}

PAGOSTransformations = {
    hash(("[amount_gas]", "[mass_gas]")): (
        "[amount_gas]",
        "[mass_gas]",
        lambda reg, x, gas: (
            {"He": 1, "Ar": 2}[gas] * x * reg.Quantity(1, "g_g/mol_g")
        ),  # PLACEHOLDER
    ),
    hash(("[mass_gas]", "[amount_gas]")): (
        "[mass_gas]",
        "[amount_gas]",
        lambda reg, x, gas: (
            x / {"He": 1, "Ar": 2}[gas] * reg.Quantity(1, "mol_g/g_g")
        ),  # PLACEHOLDER
    ),
}
