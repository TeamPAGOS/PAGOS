"""
Some utilities to be used in GUI handling that I did not want to clutter up the maingui.py file.
"""

import re


# NOTE I suck at regex and asked Perplexity to do this.. so there is a chance it is garbage. Proceed with caution
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
