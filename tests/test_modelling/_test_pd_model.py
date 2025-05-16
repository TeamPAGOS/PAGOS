# Tests the PD model with preset data

import pandas as pd
import numpy as np
from pagos.builtin_models import pd as _pd
from pagos import GasExchangeModel
from pagos.constants import NOBLEGASES
from pagos.core import snv

preset_data = pd.read_csv('tests/assets/data_for_PD.csv')
PDModel = GasExchangeModel(_pd, ['degC', 'permille', 'atm', 'cc/g', '', ''], 'cc/g')

def test_pd_model_with_preset_data():
    PD_fit = PDModel.fit(preset_data, ['T', 'A', 'FPD'], [15, 5e-5, 0.5], NOBLEGASES, tqdm_bar=False)
    PD_fit = PD_fit.applymap(lambda x: snv(x)) # convert to nominal values
    np.testing.assert_allclose(PD_fit, preset_data[['T', 'A', 'FPD']], rtol=1e-2)

def test_pd_model_with_single_preset_data():
    obs, errs, units, ops = preset_data[NOBLEGASES].iloc[0].to_list(), preset_data[[ng + ' err' for ng in NOBLEGASES]].iloc[0].to_list(), 'cc/g', preset_data[['S', 'p', 'beta']].iloc[0].to_list()
    PD_fit = PDModel.fit((obs, errs, units, ops), ['T', 'A', 'FPD'], [15, 5e-5, 0.5], NOBLEGASES, tqdm_bar=False)
    PD_fit = [snv(p) for p in PD_fit] # convert to nominal values
    np.testing.assert_allclose(PD_fit, preset_data[['T', 'A', 'FPD']].iloc[0], rtol=1e-2)
