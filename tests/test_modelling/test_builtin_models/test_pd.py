from pagos.newbuiltin_models import pd_model
from pagos.newcore import pQ


def test_run_pd_with_floats():
    pdHe = pd_model.run("He", T=10, S=20, p=0.96, A=1e-5, FPD=0.5, beta=0.7)
    pdNe = pd_model.run("Ne", T=10, S=20, p=0.96, A=1e-5, FPD=0.5, beta=0.7)

    assert pdHe == pQ(8.446248277205455e-10, "mol_He/kg")
    assert pdNe == pQ(4.788320341532935e-09, "mol_Ne/kg")


def test_run_pd_with_quantities():
    pdHe = pd_model.run(
        "He",
        T=pQ(10, "degC"),
        S=pQ(20, "permille"),
        p=pQ(0.96, "atm"),
        A=pQ(1e-5, "mol/kg"),
        FPD=pQ(0.5, "dimensionless"),
        beta=pQ(0.7, "dimensionless"),
    )
    pdNe = pd_model.run(
        "Ne",
        T=pQ(10, "degC"),
        S=pQ(20, "permille"),
        p=pQ(0.96, "atm"),
        A=pQ(1e-5, "mol/kg"),
        FPD=pQ(0.5, "dimensionless"),
        beta=pQ(0.7, "dimensionless"),
    )

    assert pdHe == pQ(8.446248277205455e-10, "mol_He/kg")
    assert pdNe == pQ(4.788320341532935e-09, "mol_Ne/kg")


def test_run_pd_with_mixed_inputs():
    pdHe = pd_model.run(
        "He",
        T=10,
        S=pQ(20, "permille"),
        p=0.96,
        A=pQ(1e-5, "mol/kg"),
        FPD=0.5,
        beta=pQ(0.7, "dimensionless"),
    )
    pdNe = pd_model.run(
        "Ne",
        T=pQ(10, "degC"),
        S=20,
        p=pQ(0.96, "atm"),
        A=1e-5,
        FPD=pQ(0.5, "dimensionless"),
        beta=0.7,
    )

    assert pdHe == pQ(8.446248277205455e-10, "mol_He/kg")
    assert pdNe == pQ(4.788320341532935e-09, "mol_Ne/kg")


# TODO test fit and fit_dataframe
