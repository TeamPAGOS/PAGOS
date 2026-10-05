from cProfile import Profile

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from lmfit import Parameters, create_params, minimize
from tqdm import tqdm

from pagos.builtin_models import ce_model, ua_model
from pagos.core import set_warn_nonmult
from pagos.gas import abn, calc_Ceq
from pagos.modelling import TracerModel

# from pagos.newbuiltin_models import ua_model
set_warn_nonmult(False)

data = pd.read_csv("temp/meas_data.csv")

with Profile() as pr2:
    results = ce_model.fit_dataframe(
        data=data,
        regressors_to_fit={"T": 10, "A": 1e-5, "F": 1e-2},
        tracers=["He", "Ne", "Ar", "Kr", "Xe"],
        tqdm_bar=True,
        regr_to_fit_bounds={"T": [-2, 30], "A": [0, 1e-3], "F": [0, 1]},
        nmc=10,
        logging=False,
    )
pr2.dump_stats("temp/mc_profile")
