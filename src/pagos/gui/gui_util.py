"""
Some utilities to be used in GUI handling that I did not want to clutter up the maingui.py file.
"""

import re
from pandas import Series


# NOTE This was made before I really looked into regex, and I had asked Perplexity to do this.. so there is a chance
# it is garbage. Lord forgive me for I have sinned. Proceed with caution!


# Simplify the text of built-in model code, to remove docstrings and type hints. This is used only once in gui_util
def remove_docstrings_and_type_hints(code):
    # Split string into lines
    lines = code.splitlines()
    cleaned = []
    in_docstring = False

    # Regex to remove type hints (both argument and return)
    type_hint_pattern = re.compile(r":\s*[^=,\)\s]+|->\s*[^\s:]+")

    for line in lines:
        stripped = line.strip()

        # Detect start or end of a docstring
        if stripped.startswith(("'''", '"""')):
            in_docstring = not in_docstring
            continue

        if in_docstring:
            continue

        # If line contains a function definition, remove type hints
        if stripped.startswith("def "):
            line = type_hint_pattern.sub("", line)

        cleaned.append(line)

    # Join back into a single string
    return "\n".join(l for l in cleaned if l.strip())


# shorthand complement function (same as a - b where and b are sets, except this preserves order and a and b are lists/tuples)
def ordc(a: tuple | list, b: tuple | list) -> list:
    ord_dict = dict.fromkeys(x for x in a if x not in b)
    return list(ord_dict.keys())


# making data exporting robust
def make_sure_export_path_valid(export_path, required_extension, default_if_none_given):
    if export_path is not None:
        if (
            len(export_path) < (n := len(required_extension))
            or export_path[-n:] != required_extension
        ):
            ret = export_path + required_extension
        else:
            ret = export_path
    else:
        ret = default_if_none_given + required_extension
    return ret
