from pagos.newbuiltin_models import od_model
from pagos.newcore import pQ


def test_run_od_with_floats():
    odHe = od_model.run("He", T=10, S=20, p=0.96, A=1e-5, POD=0.5)
    odNe = od_model.run("Ne", T=10, S=20, p=0.96, A=1e-5, POD=0.5)

    assert odHe == pQ(9.590003179179337e-10, "mol_He/kg")
    assert odNe == pQ(4.038202799005727e-09, "mol_Ne/kg")


def test_run_od_with_quantities():
    odHe = od_model.run(
        "He",
        T=pQ(10, "degC"),
        S=pQ(20, "permille"),
        p=pQ(0.96, "atm"),
        A=pQ(1e-5, "mol/kg"),
        POD=pQ(0.5, "dimensionless"),
    )
    odNe = od_model.run(
        "Ne",
        T=pQ(10, "degC"),
        S=pQ(20, "permille"),
        p=pQ(0.96, "atm"),
        A=pQ(1e-5, "mol/kg"),
        POD=pQ(0.5, "dimensionless"),
    )

    assert odHe == pQ(9.590003179179337e-10, "mol_He/kg")
    assert odNe == pQ(4.038202799005727e-09, "mol_Ne/kg")


def test_run_od_with_mixed_inputs():
    odHe = od_model.run(
        "He",
        T=10,
        S=pQ(20, "permille"),
        p=0.96,
        A=pQ(1e-5, "mol/kg"),
        POD=0.5,
    )
    odNe = od_model.run(
        "Ne",
        T=pQ(10, "degC"),
        S=20,
        p=pQ(0.96, "atm"),
        A=1e-5,
        POD=pQ(0.5, "dimensionless"),
    )

    assert odHe == pQ(9.590003179179337e-10, "mol_He/kg")
    assert odNe == pQ(4.038202799005727e-09, "mol_Ne/kg")


# TODO test fit and fit_dataframe
