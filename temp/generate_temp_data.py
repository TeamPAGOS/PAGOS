import numpy as np
import pandas as pd

from pagos.builtin_models import ce_model, ce
from pagos.core import set_warn_nonmult

set_warn_nonmult(False)

rng = np.random.default_rng()
n_samples = 10
realT = rng.normal(loc=15, scale=2, size=n_samples)
realS = rng.uniform(low=0, high=3, size=n_samples)
realp = rng.normal(loc=1010, scale=5, size=n_samples) / 1013.25
realA = rng.uniform(low=0, high=1e-2, size=n_samples)
realF = rng.uniform(low=0, high=0.1, size=n_samples)

measHe = np.array(
    [
        ce_model.run(
            gas="He", T=realT[i], S=realS[i], p=realp[i], A=realA[i], F=realF[i]
        ).value
        for i in range(n_samples)
    ]
)
errHe = measHe * rng.gamma(shape=9, scale=0.5) * 0.01 / 4
measNe = np.array(
    [
        ce_model.run(
            gas="Ne", T=realT[i], S=realS[i], p=realp[i], A=realA[i], F=realF[i]
        ).value
        for i in range(n_samples)
    ]
)
errNe = measNe * rng.gamma(shape=9, scale=0.5) * 0.01 / 4
measAr = np.array(
    [
        ce_model.run(
            gas="Ar", T=realT[i], S=realS[i], p=realp[i], A=realA[i], F=realF[i]
        ).value
        for i in range(n_samples)
    ]
)
errAr = measAr * rng.gamma(shape=9, scale=0.5) * 0.01 / 4
measKr = np.array(
    [
        ce_model.run(
            gas="Kr", T=realT[i], S=realS[i], p=realp[i], A=realA[i], F=realF[i]
        ).value
        for i in range(n_samples)
    ]
)
errKr = measKr * rng.gamma(shape=9, scale=0.5) * 0.01 / 4
measXe = np.array(
    [
        ce_model.run(
            gas="Xe", T=realT[i], S=realS[i], p=realp[i], A=realA[i], F=realF[i]
        ).value
        for i in range(n_samples)
    ]
)
errXe = measXe * rng.gamma(shape=9, scale=0.5) * 0.01 / 4

measS = realS * rng.normal(loc=1, scale=0.005, size=n_samples)
measp = realp * rng.normal(loc=1, scale=0.005, size=n_samples)
errS = np.full(n_samples, 0.01)
errp = np.full(n_samples, 0.5)
unitsS = np.full(n_samples, "g/kg")
unitsp = np.full(n_samples, "atm")

meas_data_df = pd.DataFrame(
    data={
        "He": measHe,
        "He err": errHe,
        "Ne": measNe,
        "Ne err": errNe,
        "Ar": measAr,
        "Ar err": errAr,
        "Kr": measKr,
        "Kr err": errKr,
        "Xe": measXe,
        "Xe err": errXe,
        "S": measS,
        "S err": errS,
        "p": measp,
        "p err": errp,
        "S units": unitsS,
        "p units": unitsp,
        "real T": realT,
        "real A": realA,
        "real F": realF,
        "real p": realp,
        "real S": realS,
    }
)

pd.options.display.float_format = "{:,.2e}".format
print(meas_data_df)

meas_data_df.to_csv("temp/meas_data.csv", index=False)
