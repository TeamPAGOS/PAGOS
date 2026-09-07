import json
from functools import reduce
from operator import add

# gases json file
with open("src/pagos/gases.json", "r") as gases_file:
    gases_info = json.load(gases_file)["gases"]

# strings with unit definitions. Will be imported using ureg.define in pagos.core

PAGOSUnits = {}

PAGOSDims = set()

PAGOSDimPatterns = [
    ["[mass_", "gram", "g"],
    ["[amount_", "mole", "mol"],
    # ["[STPvolume_", "cubic_centimeter_STP", "cm3STP", "ccSTP"],
]

# These are generic function definitions that will be generatively called later
# For each transformation, there is a regular version with units and a "bare" version without them
# The bare version is called when fast calculations should be done.
GenericPAGOSTransformations = {
    hash(("[amount_gas]", "[mass_gas]")): (
        'def __amount_to_mass_[GAS](reg, x): return x * [MOLARMASS] * reg.Quantity(1, "gram_[GAS]/mole_[GAS]")',
        "def __bare_amount_to_mass_[GAS](reg, x): return x * [MOLARMASS]",
    ),
    hash(("[mass_gas]", "[amount_gas]")): (
        'def __mass_to_amount_[GAS](reg, x): return x / [MOLARMASS] * reg.Quantity(1, "mole_[GAS]/gram_[GAS]")',
        "def __bare_mass_to_amount_[GAS](reg, x): return x / [MOLARMASS]",
    ),
    # TODO CONTINUE
}
PAGOSTransformations = {}
BarePAGOSTransformations = {}

# generate Pint definitions of PAGOSUnits like mole_He, mole_Ne, ccSTP_He, gram_SF6, ...
# for example, we take ["amount_", "mole", "mol"] from PAGOSDimPatterns and create
# "mole_<GAS> = [amount_<GAS>] = mol_<GAS>" for <GAS> in the list of relevant gases
for pattern in PAGOSDimPatterns:
    for gas in gases_info:
        gdict = gases_info[gas]
        dimension = pattern[0] + gdict["name"] + "]"
        baseunit = pattern[1] + "_" + gdict["name"]
        aliases = [pattern[i] + "_" + gdict["name"] for i in range(2, len(pattern))]
        # add units to PAGOSUnits
        PAGOSUnits[baseunit] = reduce(
            add, (" = " + a for a in aliases), f"{baseunit} = {dimension}"
        )
        # add dimensions to PAGOSDims
        PAGOSDims.add(dimension)
        # add transformations to PAGOSTransformations
        generic_dimension = pattern[0] + "gas]"
        for target_pattern in PAGOSDimPatterns:
            if target_pattern != pattern:
                generic_target_dimension = target_pattern[0] + "gas]"
                # load string for definition of transform function from [dimension] -> [targetdimension]
                # do this for both regular and bare function definitions
                _id = hash((generic_dimension, generic_target_dimension))
                transf_func_str = GenericPAGOSTransformations[_id][0]
                bare_transf_func_str = GenericPAGOSTransformations[_id][1]
                transf_func_name = (
                    transf_func_str.split("[GAS]")[0].removeprefix("def ")
                    + gdict["name"]
                )
                bare_transf_func_name = (
                    bare_transf_func_str.split("[GAS]")[0].removeprefix("def ")
                    + gdict["name"]
                )
                # rename the generic functions with the specific gas
                transf_func_str = transf_func_str.replace("[GAS]", gdict["name"])
                bare_transf_func_str = bare_transf_func_str.replace(
                    "[GAS]", gdict["name"]
                )
                # replace instances of placeholder tags in string with actual representative numbers
                # MOLAR MASSES
                transf_func_str = transf_func_str.replace(
                    "[MOLARMASS]", str(gdict["mmol [g_g/mol_g]"])
                )
                bare_transf_func_str = bare_transf_func_str.replace(
                    "[MOLARMASS]", str(gdict["mmol [g_g/mol_g]"])
                )
                # MOLAR VOLUMES
                transf_func_str = transf_func_str.replace(
                    "[MOLARVOLUME]", str(gdict["vmol [ccSTP_g/mol_g]"])
                )
                bare_transf_func_str = bare_transf_func_str.replace(
                    "[MOLARVOLUME]", str(gdict["vmol [ccSTP_g/mol_g]"])
                )
                # ABUDANCES
                transf_func_str = transf_func_str.replace(
                    "[ABUNDANCE]", str(gdict["abn [mol_g/mol]"])
                )
                bare_transf_func_str = bare_transf_func_str.replace(
                    "[ABUNDANCE]", str(gdict["abn [mol_g/mol]"])
                )
                # create function objects
                exec(transf_func_str, globals(), locals())
                exec(bare_transf_func_str, globals(), locals())
                # create association between functions and hash key in PAGOSTransformations
                target_dimension = target_pattern[0] + gdict["name"] + "]"
                id = hash((dimension, target_dimension))
                exec(
                    f"PAGOSTransformations[id] = ('{dimension}', '{target_dimension}', {transf_func_name}, {bare_transf_func_name})",
                    globals(),
                    locals(),
                )

    # generic gas pattern
    dimension = pattern[0] + "gas]"
    baseunit = pattern[1] + "_gas"
    aliases = [pattern[i] + "_gas" for i in range(2, len(pattern))] + [
        pattern[i] + "_g" for i in range(1, len(pattern))
    ]
    PAGOSUnits[baseunit] = reduce(
        add, (" = " + a for a in aliases), f"{baseunit} = {dimension}"
    )
    PAGOSDims.add(dimension)

"""for p in PAGOSUnits:
    print(PAGOSUnits[p])

for d in PAGOSDims:
    print(d)

for k in PAGOSTransformations:
    print(PAGOSTransformations[k])
"""
