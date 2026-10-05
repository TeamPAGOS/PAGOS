import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
from pagos.core import begin_new_mc_cycle, pQ, set_mc, _set_fast, mc, set_warn_nonmult
from pagos.gas import calc_Ceq, abn
from pagos.builtin_models import ua_model, ce_model
import pandas as pd
from cProfile import Profile

from pagos.modelling import TracerModel
from lmfit import minimize, Parameters, create_params

# from pagos.newbuiltin_models import ua_model
set_warn_nonmult(False)

data = pd.read_csv("temp/meas_data.csv", nrows=1)

with Profile() as pr:
    singleresult = ua_model.fit_dataframe(
        data=data,
        regressors_to_fit={"T": 10, "A": 1e-5},  # , "F": 0.01},
        tracers=["He", "Ne", "Ar", "Kr", "Xe"],
        tqdm_bar=True,
        regr_to_fit_bounds={"T": [-2, 30], "A": [0, 0.01]},  # , "F": [0, 1]},
        logging=False,
        nmc=100,
    )
pr.dump_stats("temp/single_profile_mc.prof")

fast_jk_coeffs = {
    "He": {
        "A0": -178.1424,
        "AR": 217.5991,
        "AL": 140.7506,
        "A1": -23.01954,
        "B0": -0.038129,
        "B1": 0.01919,
        "B2": -0.0026898,
        "C0": -0.00000255157,
    },
    "Ne": {
        "A0": -274.1329,
        "AR": 352.6201,
        "AL": 226.9676,
        "A1": -37.13393,
        "B0": -0.06386,
        "B1": 0.035326,
        "B2": -0.0053258,
        "C0": 0.0000128233,
    },
    "Ar": {
        "A0": -227.4607,
        "AR": 305.4347,
        "AL": 180.5278,
        "A1": -27.9945,
        "B0": -0.066942,
        "B1": 0.037201,
        "B2": -0.0056364,
        "C0": -5.30325e-06,
    },
    "Kr": {
        "A0": -122.4694,
        "AR": 153.5654,
        "AL": 70.1969,
        "A1": -8.52524,
        "B0": -0.049522,
        "B1": 0.024434,
        "B2": -0.0033968,
        "C0": 4.19208e-06,
    },
    "Xe": {
        "A0": -224.51,
        "AR": 292.8234,
        "AL": 157.6127,
        "A1": -22.66895,
        "B0": -0.084915,
        "B1": 0.047996,
        "B2": -0.0073595,
        "C0": 6.69292e-06,
    },
}
abns = {"He": 5.24e-6, "Ne": 18.18e-6, "Ar": 0.934e-2, "Kr": 1.14e-6, "Xe": 0.087e-6}


def fast_ua(gas, T, S, p, A):
    p0, c = 6.1078, 239.7  # mbar, delta_degC
    pv = p0 * 10 ** ((7.567 * T) / (T + c))  # mbar
    # vapour pressure over the water, calculated according to Dyck and Peschke 1995 (atm)
    e_w = pv / 1013.25  # atm
    # calculation of C*, the gas solubility/water-side concentration expressed in units of mol/kg

    T_K = T + 273.15
    T_N = T_K / 100
    A0, AR, AL, A1, B0, B1, B2, C0 = (
        fast_jk_coeffs[gas][c] for c in ["A0", "AR", "AL", "A1", "B0", "B1", "B2", "C0"]
    )
    Cstar = np.exp(
        A0
        + AR / T_N
        + AL * np.log(T_N)
        + A1 * T_N
        + S * (B0 + B1 * T_N + B2 * T_N**2)
        + S**2 * C0
    )

    # factor to account for pressure
    pref = (p - e_w) / (1 - e_w)
    Ceq = Cstar * pref
    return Ceq + A * abns[gas]


with Profile() as pr3:
    meas_S = data["S"].iloc[0]
    meas_p = data["p"].iloc[0]
    meas_He = data["He"].iloc[0]
    err_He = data["He err"].iloc[0]
    meas_Ne = data["Ne"].iloc[0]
    err_Ne = data["Ne err"].iloc[0]
    meas_Ar = data["Ar"].iloc[0]
    err_Ar = data["Ar err"].iloc[0]
    meas_Kr = data["Kr"].iloc[0]
    err_Kr = data["Kr err"].iloc[0]
    meas_Xe = data["Xe"].iloc[0]
    err_Xe = data["Xe err"].iloc[0]

    def objfunc(params, tracers, meas, weights):
        T = params["T"]
        S = params["S"]
        p = params["p"]
        A = params["A"]

        mod = np.array([fast_ua(tr, T, S, p, A) for tr in tracers])

        return (mod - meas) / weights

    pars = Parameters()
    pars.add("T", 10, True, -2, 30)
    pars.add("S", meas_S, False)
    pars.add("p", meas_p, False)
    pars.add("A", 1e-5, True, 0, 0.01)

    minimize(
        objfunc,
        pars,
        args=(
            ["He", "Ne", "Ar", "Kr", "Xe"],
            np.array([meas_He, meas_Ne, meas_Ar, meas_Kr, meas_Xe]),
            np.array([err_He, err_Ne, err_Ar, err_Kr, err_Xe]),
        ),
    )
pr3.dump_stats("temp/single_profile_fast.prof")

# results.plot_results()
