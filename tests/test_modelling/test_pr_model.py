# Tests the PR model with preset data
import sys
sys.path.insert(0, 'C:/Users/scopi/source/repos/PAGOS/PAGOS/src')

import pandas as pd
import numpy as np
from pagos.builtin_models import pr
from pagos import GasExchangeModel
from pagos.constants import NOBLEGASES
from pagos.core import snv

preset_data = pd.read_csv('tests/assets/data_for_PR.csv')
PRModel = GasExchangeModel(pr, ['degC', 'permille', 'atm', 'cc/g', '', ''], 'cc/g')

def test_pr_model_with_preset_data():
    PR_fit = PRModel.fit(preset_data, ['T', 'A', 'FPR'], [15, 5e-5, 0.5], NOBLEGASES, tqdm_bar=False)
    PR_fit = PR_fit.applymap(lambda x: snv(x)) # convert to nominal values
    np.testing.assert_allclose(PR_fit, preset_data[['T', 'A', 'FPR']], rtol=1e-2)

def test_pr_model_with_single_preset_data():
    obs, errs, units, ops = preset_data[NOBLEGASES].iloc[4], preset_data[[ng + ' err' for ng in NOBLEGASES]].iloc[4], 'cc/g', preset_data[['S', 'p', 'beta']].iloc[4]
    PR_fit = PRModel.fit((obs, errs, units, ops), ['T', 'A', 'FPR'], [15, 5e-5, 0.5], NOBLEGASES, tqdm_bar=False)
    PR_fit = [snv(p) for p in PR_fit] # convert to nominal values
    np.testing.assert_allclose(PR_fit, preset_data[['T', 'A', 'FPR']].iloc[4], rtol=1e-2)