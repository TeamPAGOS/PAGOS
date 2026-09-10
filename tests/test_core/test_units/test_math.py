"""
Tests for unit-awareness in mathematical functions
"""

from pagos.newcore import pQ, _set_fast


def test_add():
    q1 = pQ(5, "kg")
    q2 = pQ(3, "kg")
    q3 = pQ(2, "g")
    q4 = pQ(7.0, "dimensionless")

    # u1 + u1
    assert q1 + q2 == pQ(8, "kg")
    # u1 + (u2 -> u1)
    assert q1 + q3 == pQ(5.002, "kg")
    # dimless + float
    assert q4 + 7.0 == pQ(14, "dimensionless")
    # float + dimless
    assert 7.0 + q4 == pQ(14, "dimensionless")
    # dimless + int
    assert q4 + 7 == pQ(14, "dimensionless")
    # int + dimless
    assert 7 + q4 == pQ(14, "dimensionless")

    # fast mode
    _set_fast(True)
    q1 = pQ(5, "kg")
    q2 = pQ(3, "kg")
    q3 = pQ(2, "g")
    q4 = pQ(7.0, "dimensionless")
    assert q1 + q2 == pQ(8, "kg")
    assert q1 + q3 == pQ(5.002, "kg")
    assert q4 + 7.0 == pQ(14, "dimensionless")
    assert 7.0 + q4 == pQ(14, "dimensionless")
    assert q4 + 7 == pQ(14, "dimensionless")
    assert 7 + q4 == pQ(14, "dimensionless")
    _set_fast(False)


def test_subtract():
    q1 = pQ(5, "kg")
    q2 = pQ(3, "kg")
    q3 = pQ(2, "g")
    q4 = pQ(7.0, "dimensionless")

    # u1 - u1
    assert q1 - q2 == pQ(2, "kg")
    # u1 - (u2 -> u1)
    assert q1 - q3 == pQ(4.998, "kg")
    # dimless - float
    assert q4 - 7.0 == pQ(0, "dimensionless")
    # float - dimless
    assert 7.0 - q4 == pQ(0, "dimensionless")
    # dimless - int
    assert q4 - 7 == pQ(0, "dimensionless")
    # int - dimless
    assert 7 - q4 == pQ(0, "dimensionless")

    # fast mode
    _set_fast(True)
    q1 = pQ(5, "kg")
    q2 = pQ(3, "kg")
    q3 = pQ(2, "g")
    q4 = pQ(7.0, "dimensionless")
    assert q1 - q2 == pQ(2, "kg")
    assert q1 - q3 == pQ(4.998, "kg")
    assert q4 - 7.0 == pQ(0, "dimensionless")
    assert 7.0 - q4 == pQ(0, "dimensionless")
    assert q4 - 7 == pQ(0, "dimensionless")
    assert 7 - q4 == pQ(0, "dimensionless")
    _set_fast(False)


def test_multiply():
    q1 = pQ(5, "kg")
    q2 = pQ(3, "kg")
    q3 = pQ(2, "g")
    q4 = pQ(7, "m")

    # u1 * u1
    assert q1 * q2 == pQ(15, "kg^2")
    # u1 * u2 (same dimensions)
    assert q1 * q3 == pQ(0.01, "kg^2")
    # u1 * u2 (different dimensions)
    assert q1 * q4 == pQ(35, "m*kg")
    # u1 * float
    assert q1 * 9.0 == pQ(45, "kg")
    # float * u1
    assert 9.0 * q1 == pQ(45, "kg")
    # u1 * int
    assert q1 * 9 == pQ(45, "kg")
    # int * u1
    assert 9 * q1 == pQ(45, "kg")

    # fast mode
    _set_fast(True)
    q1 = pQ(5, "kg")
    q2 = pQ(3, "kg")
    q3 = pQ(2, "g")
    q4 = pQ(7, "m")
    assert q1 * q2 == pQ(15, "kg^2")
    assert q1 * q3 == pQ(0.01, "kg^2")
    assert q1 * q4 == pQ(35, "m*kg")
    assert q1 * 9.0 == pQ(45, "kg")
    assert 9.0 * q1 == pQ(45, "kg")
    assert q1 * 9 == pQ(45, "kg")
    assert 9 * q1 == pQ(45, "kg")
    _set_fast(False)


def test_divide():
    q1 = pQ(24, "kg")
    q2 = pQ(12, "kg")
    q3 = pQ(6, "g")
    q4 = pQ(4, "m")

    # u1 / u1
    assert q1 / q2 == pQ(2, "dimensionless")
    # u1 / u2 (same dimensions)
    assert q1 / q3 == pQ(4000, "dimensionless")
    # u1 / u2 (different dimensions)
    assert q1 / q4 == pQ(6, "kg / m")
    # u1 / float
    assert q1 / 3.0 == pQ(8, "kg")
    # float / u1
    assert 3.0 / q1 == pQ(0.125, "kg^-1")
    # u1 / int
    assert q1 / 3 == pQ(8, "kg")
    # int / u1
    assert 3 / q1 == pQ(0.125, "kg^-1")

    # fast mode
    _set_fast(True)
    q1 = pQ(24, "kg")
    q2 = pQ(12, "kg")
    q3 = pQ(6, "g")
    q4 = pQ(4, "m")
    assert q1 / q2 == pQ(2, "dimensionless")
    assert q1 / q3 == pQ(4000, "dimensionless")
    assert q1 / q4 == pQ(6, "kg / m")
    assert q1 / 3.0 == pQ(8, "kg")
    assert 3.0 / q1 == pQ(0.125, "kg^-1")
    assert q1 / 3 == pQ(8, "kg")
    assert 3 / q1 == pQ(0.125, "kg^-1")
    _set_fast(False)


def test_mixed():
    q1 = pQ(24, "kg")
    q2 = pQ(12, "kg")
    q3 = pQ(6, "g")

    assert q1 + q2 * (q3 - q1) / q3 == pQ(-47964, "kg")
    _set_fast(True)
    q1 = pQ(24, "kg")
    q2 = pQ(12, "kg")
    q3 = pQ(6, "g")
    assert q1 + q2 * (q3 - q1) / q3 == pQ(-47964, "kg")
    _set_fast(False)


def test_abs():
    q1 = pQ(-9.81, "m/s^2")
    assert abs(q1) == pQ(9.81, "m/s^2")
    _set_fast(True)
    q1 = pQ(-9.81, "m/s^2")
    assert abs(q1) == pQ(9.81, "m/s^2")
    _set_fast(False)
