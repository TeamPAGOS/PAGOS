# Testing the CE model with preset data
import sys
sys.path.insert(0, 'C:/Users/scopi/source/repos/PAGOS/PAGOS/src')

import pandas as pd
import numpy as np
from pagos.builtin_models import ce
from pagos import GasExchangeModel
from pagos.constants import NOBLEGASES
from pagos.core import snv

preset_data = pd.read_csv('tests/assets/data_for_CE.csv')
CEModel = GasExchangeModel(ce, ['degC', 'permille', 'atm', 'cc/g', ''], 'cc/g')

def test_ce_model_with_preset_data():
    CE_fit = CEModel.fit(preset_data, ['T', 'A', 'F'], [15, 5e-5, 0.5], NOBLEGASES, tqdm_bar=True)
    CE_fit = CE_fit.applymap(lambda x: snv(x)) # convert to nominal values
    np.testing.assert_allclose(CE_fit, preset_data[['T', 'A', 'F']], rtol=1e-2)


def test_ce_model_with_single_preset_data():
    obs, errs, units, ops = preset_data[NOBLEGASES].iloc[4], preset_data[[ng + ' err' for ng in NOBLEGASES]].iloc[4], 'cc/g', preset_data[['S', 'p']].iloc[4]
    CE_fit = CEModel.fit((obs, errs, units, ops), ['T', 'A', 'F'], [15, 5e-5, 0.5], NOBLEGASES, tqdm_bar=False)
    CE_fit = [snv(p) for p in CE_fit] # convert to nominal values
    np.testing.assert_allclose(CE_fit, preset_data[['T', 'A', 'F']].iloc[4], rtol=1e-2)