# Tests the UA model with preset data

import pandas as pd
import numpy as np
from pagos.builtin_models import ua
from pagos import GasExchangeModel
from pagos.constants import NOBLEGASES

preset_data = pd.read_csv('tests/assets/data_for_UA.csv')
UAModel = GasExchangeModel(ua, ['degC', 'permille', 'atm', 'cc/g'], 'cc/g')

def test_ua_model_with_preset_data():
    UA_fit = UAModel.fit(preset_data, ['T', 'S', 'A'], [15, 25, 5e-5], NOBLEGASES, tqdm_bar=False)
    UA_fit = UA_fit.applymap(lambda x: x.nominal_value) # convert to nominal values
    np.testing.assert_allclose(UA_fit, preset_data[['T', 'S', 'A']], rtol=1e-2)

def test_ua_model_with_single_preset_data():
    obs, errs, units, ops = preset_data[NOBLEGASES].iloc[4], preset_data[[ng + ' err' for ng in NOBLEGASES]].iloc[4], 'cc/g', preset_data[['p']].iloc[4]
    UA_fit = UAModel.fit((obs, errs, units, ops), ['T', 'S', 'A'], [15, 25, 5e-5], NOBLEGASES, tqdm_bar=False)
    UA_fit = [p.nominal_value for p in UA_fit] # convert to nominal values
    np.testing.assert_allclose(UA_fit, preset_data[['T', 'S', 'A']].iloc[4], rtol=1e-2)
