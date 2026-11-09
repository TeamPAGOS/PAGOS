"""Base constants file which contains constants only as numerical values. constants.py contains constants stored as PAGOSQuantity objects,
which cannot be defined here (otherwise we would end up with circular imports). These numerical constants should not be imported by the user,
and only serve to provide gas-specific conversions in units.py without causing circular imports.
"""

import json

# gases json file
with open("src/pagos/gases.json", "r") as gases_file:
    gases_info = json.load(gases_file)["gases"]

# atmospheric abundances of gases in mol gas / mol air
_ABUNDANCES_MOL_G_PER_MOL = {
    gases_info[k]["name"]: gases_info[k]["abn [mol_g/mol]"] for k in gases_info
}

# molar volumes in units of cm3_STP/mol, referenced to 0 degC and 1 atm = 1013.25 mbar, except
# CFC11, which is referenced to its boiling point of 297 K
# Sources: noble gases, Benson & Krause 1976; stable transient gases, NIST
# NOTE: cannot find them in Benson and Krause
# TODO more digits for CFCs
_MOLAR_VOLUMES_CCSTP_G_PER_MOL_G = {
    gases_info[k]["name"]: gases_info[k]["vmol [ccSTP_g/mol_g]"] for k in gases_info
}

# molar masses of gases (g/mol)
_MOLAR_MASSES_G_G_PER_MOL_G = {
    gases_info[k]["name"]: gases_info[k]["mmol [g_g/mol_g]"] for k in gases_info
}
