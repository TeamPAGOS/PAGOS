# unary operations that cannot change units of operand
unary_no_change = {
    "negative",
    "positive",
    "absolute",
    "fabs",
    "rint",
    "conj",
    "conjugate",
    "floor",
    "ceil",
    "trunc",
}

# unary operations that can change units of operand (most here can only operate on dimensionless, but could change e.g. % to dimensionless)
unary_change = {
    "exp",
    "exp2",
    "log",
    "log2",
    "log10",
    "sqrt",
    "square",
    "cbrt",
    "reciprocal",
    "sin",
    "cos",
    "tan",
    "arcsin",
    "arccos",
    "arctan",
    "sinh",
    "cosh",
    "tanh",
    "arcsinh",
    "arctanh",
    "degrees",
    "radians",
    "deg2rad",
    "rad2deg",
    "expm1",
    "log1p",
}

# unary operations that do not return units at all (instead bool, int, etc.)
unary_no_unit_return = {
    "sign",
    "isfinite",
    "isinf",
    "isnan",
    "signbit",
}

binary_no_unit_return = {
    "greater",
    "greater_equal",
    "less",
    "less_equal",
    "not_equal",
    "equal",
}

# binary operations
binary_unit_return = {
    "add",
    "subtract",
    "multiply",
    "divide",
    "logaddexp",
    "logaddexp2",
    "true_divide",
    "floor_divide",
    "power",
    "remainder",
    "mod",
    "fmod",
    "arctan2",
    "hypot",
    "maximum",
    "minimum",
    "nextafter",
    "ldexp",
}
