from pagos.newbuiltin_models import ce_model, ce
from pagos.newcore import pQ


def test_run_ce_with_floats():
    ceHe = ce_model.run("He", T=10, S=20, p=0.96, A=1e-5, F=0.5)
    ceNe = ce_model.run("Ne", T=10, S=20, p=0.96, A=1e-5, F=0.5)

    assert ceHe == pQ(1.8390274490560943e-09, "mol_He/kg")
    assert ceNe == pQ(7.802646766422251e-09, "mol_Ne/kg")


def test_run_ce_with_quantities():
    ceHe = ce_model.run(
        "He",
        T=pQ(10, "degC"),
        S=pQ(20, "permille"),
        p=pQ(0.96, "atm"),
        A=pQ(1e-5, "mol/kg"),
        F=pQ(0.5, "dimensionless"),
    )
    ceNe = ce_model.run(
        "Ne",
        T=pQ(10, "degC"),
        S=pQ(20, "permille"),
        p=pQ(0.96, "atm"),
        A=pQ(1e-5, "mol/kg"),
        F=pQ(0.5, "dimensionless"),
    )

    assert ceHe == pQ(1.8390274490560943e-09, "mol_He/kg")
    assert ceNe == pQ(7.802646766422251e-09, "mol_Ne/kg")


def test_run_ce_with_mixed_inputs():
    ceHe = ce_model.run(
        "He",
        T=10,
        S=pQ(20, "permille"),
        p=0.96,
        A=pQ(1e-5, "mol/kg"),
        F=0.5,
    )
    ceNe = ce_model.run(
        "Ne",
        T=pQ(10, "degC"),
        S=20,
        p=pQ(0.96, "atm"),
        A=1e-5,
        F=pQ(0.5, "dimensionless"),
    )

    assert ceHe == pQ(1.8390274490560943e-09, "mol_He/kg")
    assert ceNe == pQ(7.802646766422251e-09, "mol_Ne/kg")


# TODO test fit and fit_dataframe
