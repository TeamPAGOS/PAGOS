from pagos.newbuiltin_models import pr_model
from pagos.newcore import pQ


def test_run_pr_with_floats():
    prHe = pr_model.run("He", T=10, S=20, p=0.96, A=1e-5, FPR=0.5, beta=0.7)
    prNe = pr_model.run("Ne", T=10, S=20, p=0.96, A=1e-5, FPR=0.5, beta=0.7)

    assert prHe == pQ(1.8369240094895898e-09, "mol_He/kg")
    assert prNe == pQ(7.82307287194721e-09, "mol_Ne/kg")


def test_run_pr_with_quantities():
    prHe = pr_model.run(
        "He",
        T=pQ(10, "degC"),
        S=pQ(20, "permille"),
        p=pQ(0.96, "atm"),
        A=pQ(1e-5, "mol/kg"),
        FPR=pQ(0.5, "dimensionless"),
        beta=pQ(0.7, "dimensionless"),
    )
    prNe = pr_model.run(
        "Ne",
        T=pQ(10, "degC"),
        S=pQ(20, "permille"),
        p=pQ(0.96, "atm"),
        A=pQ(1e-5, "mol/kg"),
        FPR=pQ(0.5, "dimensionless"),
        beta=pQ(0.7, "dimensionless"),
    )

    assert prHe == pQ(1.8369240094895898e-09, "mol_He/kg")
    assert prNe == pQ(7.82307287194721e-09, "mol_Ne/kg")


def test_run_pr_with_mixed_inputs():
    prHe = pr_model.run(
        "He",
        T=10,
        S=pQ(20, "permille"),
        p=0.96,
        A=pQ(1e-5, "mol/kg"),
        FPR=0.5,
        beta=pQ(0.7, "dimensionless"),
    )
    prNe = pr_model.run(
        "Ne",
        T=pQ(10, "degC"),
        S=20,
        p=pQ(0.96, "atm"),
        A=1e-5,
        FPR=pQ(0.5, "dimensionless"),
        beta=0.7,
    )

    assert prHe == pQ(1.8369240094895898e-09, "mol_He/kg")
    assert prNe == pQ(7.82307287194721e-09, "mol_Ne/kg")


# TODO test fit and fit_dataframe
