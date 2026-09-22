from pagos.newcore import pQ
from pagos.newmodelling import TracerModel
from pagos.gasobject import calc_Ceq, abn
from numpy.testing import assert_approx_equal


# example model: unfractionated excess air model
def ua(gas, T, S, p, A):
    ceq = calc_Ceq(gas, T, S, p)
    excess_air = A * abn(gas)
    return ceq + excess_air


ua_model = TracerModel(
    model_function=ua,
    default_units_in={"T": "degC", "S": "permille", "p": "atm", "A": "mol/kg"},
    default_units_out="mol_g/kg",
)


def test_run_He():
    _He = ua_model.run("He", 10, 15, 0.96, 1e-5).to("ccSTP_g/g")
    assert_approx_equal(_He.value, 4.2960382728408675e-08)


def test_run_Ne():
    _Ne = ua_model.run("Ne", 10, 15, 0.96, 1e-5).to("ccSTP_g/g")
    assert_approx_equal(_Ne.value, 1.8238645918147615e-07)


def test_run_Ar():
    _Ar = ua_model.run("Ar", 10, 15, 0.96, 1e-5).to("ccSTP_g/g")
    assert_approx_equal(_Ar.value, 0.0003382038335337283)


def test_run_Kr():
    _Kr = ua_model.run("Kr", 10, 15, 0.96, 1e-5).to("ccSTP_g/g")
    assert_approx_equal(_Kr.value, 7.880187855334792e-08)


def test_run_Xe():
    _Xe = ua_model.run("Xe", 10, 15, 0.96, 1e-5).to("ccSTP_g/g")
    assert_approx_equal(_Xe.value, 1.1371187264911829e-08)


test_run_He()
