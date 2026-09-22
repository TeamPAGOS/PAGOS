"""
Tests for unit-awareness in mathematical functions involving annoying temperature units.
All cases here will raise a warning to the user if attempted.
"""

from pagos.newcore import pQ, _set_fast


def test_add():
    q1 = pQ(5, "K")
    q2 = pQ(3, "degC")
    q3 = pQ(2, "mK")

    # 5 K + 3 °C ambiguous, changes to 5 K + 3 Δ°C = (5 + 3) K
    assert q1 + q2 == pQ(8, "K")
    # 3 °C + 5 K ambiguous, changes to 3 Δ°C + 5 K = (3 + 5) Δ°C
    assert q2 + q1 == pQ(8, "delta_degC")
    # 3 °C + 3 °C ambiguous, changes to 3 Δ°C + 3 Δ°C = (3 + 3) Δ°C
    assert q2 + q2 == pQ(6, "delta_degC")
    # 3 °C + 2 mK ambiguous, changes to 3 Δ°C + 2 mK = (3 + 0.002) Δ°C
    assert q2 + q3 == pQ(3.002, "delta_degC")
    # 2 mK + 3 °C ambiguous, changes to 2 mK + 3 Δ°C = (2 + 3000) mK
    assert q3 + q2 == pQ(3002, "mK")

    # fast mode
    _set_fast(True)
    q1 = pQ(5, "K")
    q2 = pQ(3, "degC")
    q3 = pQ(2, "mK")
    assert q1 + q2 == pQ(8, "K")
    assert q2 + q1 == pQ(8, "delta_degC")
    assert q2 + q2 == pQ(6, "delta_degC")
    assert q2 + q3 == pQ(3.002, "delta_degC")
    assert q3 + q2 == pQ(3002, "mK")
    _set_fast(False)
