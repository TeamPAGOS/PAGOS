"""Unit tests for the AST manipulation performed in unit_aware."""

from pagos.new_core import unit_aware


def test_AST_with_to_inside_function():
    @unit_aware({"a": "kg", "b": "g"}, "kg")
    def myfunc1(a, b):
        b = to(b, "kg")
        a = to(a, "g")
        c = 2 * a - b
        return a + b + c

    assert myfunc1(1, 2) == 3


def test_AST_with_simple_multiplication():
    @unit_aware({"a": "m", "b": "s^-1"}, "km/hr")
    def myfunc2(a, b):
        return a * b

    assert myfunc2(1, 2) == 7.2


def test_AST_with_simple_comparison():
    @unit_aware({"a": "m", "b": "mm", "c": "cm"}, None)
    def myfunc3(a, b, c):
        return a < b <= c

    assert myfunc3(1, 2, 3) == False


def test_AST_with_conditional():
    @unit_aware({"a": "N", "b": "g*cm", "c": "hr^2"}, "kN^2")
    def myfunc4(a, b, c):
        d = a - b / c
        e = d**2
        if a < d:
            return e
        else:
            return a**2

    assert myfunc4(1, 2, 3) == 1e-6


def test_AST_with_nested_unit_aware_functions():
    @unit_aware({"a": "m", "b": "s^-1"}, "km/hr")
    def myfunc2(a, b):
        return a * b

    @unit_aware({"a": "km", "b": "s^-1", "d": "m/s"}, "km/hr")
    def my_compound_func(a, b, d):

        c = myfunc2(a, b)
        e = d + c
        return e + d

    assert my_compound_func(0.001, 2, 3) == 28.8


if __name__ == "__main__":
    test_AST_with_to_inside_function()
    test_AST_with_simple_multiplication()
    test_AST_with_simple_comparison()
    test_AST_with_conditional()
    test_AST_with_nested_unit_aware_functions()
