from pagos.newbuiltin_models import ua_model
from pagos.newcore import pQ


def test_run_ua_with_floats():

    uaHe = ua_model.run("He", T=10, S=20, p=0.96, A=1e-5)
    uaNe = ua_model.run("Ne", T=10, S=20, p=0.96, A=1e-5)

    assert uaHe == pQ(1.8656006358358675e-09, "mol_He/kg")
    assert uaNe == pQ(7.894605598011453e-09, "mol_Ne/kg")


def test_run_ua_with_quantities():

    uaHe = ua_model.run(
        "He",
        T=pQ(10, "degC"),
        S=pQ(20, "permille"),
        p=pQ(0.96, "atm"),
        A=pQ(1e-5, "mol/kg"),
    )
    uaNe = ua_model.run(
        "Ne",
        T=pQ(10, "degC"),
        S=pQ(20, "permille"),
        p=pQ(0.96, "atm"),
        A=pQ(1e-5, "mol/kg"),
    )

    assert uaHe == pQ(1.8656006358358675e-09, "mol_He/kg")
    assert uaNe == pQ(7.894605598011453e-09, "mol_Ne/kg")


def test_run_ua_with_mixed_inputs():

    uaHe = ua_model.run("He", T=10, S=pQ(20, "permille"), p=0.96, A=pQ(1e-5, "mol/kg"))
    uaNe = ua_model.run("Ne", T=pQ(10, "degC"), S=20, p=pQ(0.96, "atm"), A=1e-5)

    assert uaHe == pQ(1.8656006358358675e-09, "mol_He/kg")
    assert uaNe == pQ(7.894605598011453e-09, "mol_Ne/kg")


# TODO test fit and fit_dataframe
