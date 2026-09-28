import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
from pagos.core import begin_new_mc_cycle, pQ, set_mc, _set_fast, mc
from pagos.gas import calc_Ceq, abn
import pandas as pd

from pagos.modelling import TracerModel

# from pagos.newbuiltin_models import ua_model

data = pd.read_csv("temp/tempdata.csv", nrows=5)


def ua(gas, T, S, p, A):
    ceq = mc(0.0, override=False)(calc_Ceq)(gas, T, S, p)
    excess_air = A * abn(gas)
    return ceq + excess_air


ua_model = TracerModel(
    ua, {"T": "degC", "S": "permille", "p": "atm", "A": "mol/kg"}, "mol_gas/kg"
)


results = ua_model.fit_dataframe(
    data=data,
    regressors_to_fit={"T": 10, "A": 0},
    tracers=["He", "Ne", "Ar", "Kr", "Xe"],
    tqdm_bar=True,
    nmc=100,
)

T_arr = results.get_result("T")
A_arr = results.get_result("A")
all_arr = results.get_result(("T", "A"))

fig, ax = plt.subplots(2, len(T_arr))
for i in range(len(T_arr)):
    ax[0, i].hist(x=T_arr[i], bins=30, color="green")
    ax[1, i].hist(x=A_arr[i], bins=30, color="green")
plt.show()

print(
    np.std(T_arr, axis=1) / np.mean(T_arr, axis=1),
    np.std(A_arr, axis=1) / np.mean(A_arr, axis=1),
)
