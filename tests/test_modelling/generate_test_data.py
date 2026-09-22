import numpy as np
from pagos.gasobject import calc_Ceq, abn
from pagos.newcore import pQ
import pandas as pd

from pagos.newcore import set_warn_nonmult

set_warn_nonmult(False)

Ss = np.random.uniform(low=0, high=40, size=20)
Ts = np.random.uniform(low=8, high=15, size=20)
ps = np.random.uniform(low=0.95, high=1.05, size=20)
As = np.random.uniform(low=0, high=5e-4, size=20)

Hes = np.array(
    [
        calc_Ceq("He", Ts[i], Ss[i], ps[i]).value + As[i] * abn("He").value
        for i in range(20)
    ]
)
Nes = np.array(
    [
        calc_Ceq("Ne", Ts[i], Ss[i], ps[i]).value + As[i] * abn("Ne").value
        for i in range(20)
    ]
)
Ars = np.array(
    [
        calc_Ceq("Ar", Ts[i], Ss[i], ps[i]).value + As[i] * abn("Ar").value
        for i in range(20)
    ]
)
Krs = np.array(
    [
        calc_Ceq("Kr", Ts[i], Ss[i], ps[i]).value + As[i] * abn("Kr").value
        for i in range(20)
    ]
)
Xes = np.array(
    [
        calc_Ceq("Xe", Ts[i], Ss[i], ps[i]).value + As[i] * abn("Xe").value
        for i in range(20)
    ]
)

He_errs = Hes * np.random.uniform(0.005, 0.02, size=20)
Ne_errs = Nes * np.random.uniform(0.005, 0.02, size=20)
Ar_errs = Ars * np.random.uniform(0.005, 0.02, size=20)
Kr_errs = Krs * np.random.uniform(0.005, 0.02, size=20)
Xe_errs = Xes * np.random.uniform(0.005, 0.02, size=20)

# generate some noise around regressors
Ss = Ss * np.random.normal(loc=1, scale=0.3, size=20)
ps = ps * np.random.normal(loc=1, scale=0.3, size=20)

data_out = pd.DataFrame(
    np.array(
        [
            Hes,
            He_errs,
            Nes,
            Ne_errs,
            Ars,
            Ar_errs,
            Krs,
            Kr_errs,
            Xes,
            Xe_errs,
            Ss,
            ps,
            Ts,
            As,
        ]
    ).transpose(),
    columns=[
        "He",
        "He err",
        "Ne",
        "Ne err",
        "Ar",
        "Ar err",
        "Kr",
        "Kr err",
        "Xe",
        "Xe err",
        "S",
        "p",
        "T (true)",
        "A (true)",
    ],
)

data_out.to_csv("tests/test_modelling/test_data.csv")
