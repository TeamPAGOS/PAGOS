# Testing the OD model with preset data

import pandas as pd
import numpy as np
from pagos.builtin_models import od
from pagos import GasExchangeModel
from pagos.constants import NOBLEGASES
from pagos.core import snv

preset_data = pd.read_csv('tests/assets/data_for_OD.csv')
ODModel = GasExchangeModel(od, ['degC', 'permille', 'atm', 'cc/g', ''], 'cc/g')

def test_od_model_with_preset_data():
    OD_fit = ODModel.fit(preset_data, ['T', 'A', 'POD'], [15, 5e-5, 0.5], NOBLEGASES, tqdm_bar=False)
    OD_fit = OD_fit.applymap(lambda x: snv(x)) # convert to nominal values
    np.testing.assert_allclose(OD_fit, preset_data[['T', 'A', 'POD']], rtol=1e-2)

def test_od_model_with_single_preset_data():
    obs, errs, units, ops = preset_data[NOBLEGASES].iloc[4], preset_data[[ng + ' err' for ng in NOBLEGASES]].iloc[4], 'cc/g', preset_data[['S', 'p']].iloc[4]
    OD_fit = ODModel.fit((obs, errs, units, ops), ['T', 'A', 'POD'], [15, 5e-5, 0.5], NOBLEGASES, tqdm_bar=False)
    OD_fit = [snv(p) for p in OD_fit] # convert to nominal values
    np.testing.assert_allclose(OD_fit, preset_data[['T', 'A', 'POD']].iloc[4], rtol=1e-2)
