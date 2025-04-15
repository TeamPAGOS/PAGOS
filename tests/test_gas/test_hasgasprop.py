# Tests hasgasprop() from pagos.gas.

from pagos.gas import hasgasprop
import pytest

def test_hasgasprop_isnoble():
    assert hasgasprop('He', 'isnoble'), "'He is a noble gas' assertion failed."
    assert hasgasprop('N2', 'isnoble') is False, "'N2 is not a noble gas' assertion failed."

def test_hasgasprop_isstabletransient():
    assert hasgasprop('SF6', 'isst'), "'SF6 is a stable transient tracer' assertion failed."
    assert hasgasprop('Ne', 'isst') is False, "'Ne is not a stable transient tracer' assertion failed."

def test_hasgasprop_novalidcondition():
    with pytest.raises(Exception) as e_info:
        hasgasprop('Ar', 'invalid')
        assert e_info.type is ValueError