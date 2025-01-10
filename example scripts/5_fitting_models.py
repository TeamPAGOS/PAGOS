"""
Here is a tutorial on how to fit gas exchange models in PAGOS.
"""

# Importing
from printlines import printlines
from pagos import gas as pgas
from pagos.modelling import GasExchangeModel
from pagos import Q
import pandas as pd

# Here we will fit some models to a real-world dataset.

# Data import, parsing and preparation
# These data are from Jung and Aeschbach 2018 (https://www.sciencedirect.com/science/article/pii/S1364815216307150)
gases_used = ['Ne', 'Ar', 'Kr', 'Xe']
pangadata = pd.read_csv('example scripts/Example Data/Complete_Input_Data_Samples_Belgium.CSV', sep=',')
print('Data from Jung and Aeschbach 2018:')
print(pangadata)

# Let's now define a model we would like to fit. As we did in the creating_and_running_models.py
# example, we will start with an unfractionated excess air model:

def ua_model(gas, T_recharge, S, p, A):
    Ceq = pgas.calc_Ceq(gas, T_recharge, S, p)
    z = pgas.abn(gas)
    return Ceq + A * z
UAModel = GasExchangeModel(ua_model, ('degC', 'permille', 'atm', 'cc/g'), None)

# This model has four parameters, two of which are provided by our dataset. We will therefore use
# the noble gas concentrations in the dataset to calculate the recharge temperature and excess air
# parameter. The gases we are using as tracers are Neon, Argon, Krypton and Xenon.
# Fitting these parameters for each sample is done in a least-squares fashion with the library
# LMFIT, and is thus implemented in PAGOS:

fit_UA = UAModel.fit(pangadata,                                             # the data as a Pandas DataFrame
                     to_fit=['T_recharge', 'A'],                            # the arguments of the model we would like to fit
                     init_guess=[Q(1, 'degC'), 1e-5],                       # the initial guesses for the parameters to be fit
                     tracers_used=gases_used,                               # the tracers used for the fitting procedure
                     #constraints={'T_recharge':[-10, 50], 'A':[0, 1e-2]},   # any constraints we might want to place on our fitted parameters
                     tqdm_bar=True)                                         # whether to display a progress bar
print('Fit of UA model:')
print(fit_UA[['Sample', 'T_recharge', 'A']])

# Note here that the init_guess arguments do NOT have to be Quantity objects, although they can be
# for clarity, if you want. When units are omitted, the default_units_in passed to the
# GasExchangeModel() constructor are used. So in this case, 1e-5 becomes 1e-5 cc/g.

# The ease of PAGOS's model definition means that we can easily define and fit a different model:
def ce_model(gas, T, S, p, A, F):
    Ceq = pgas.calc_Ceq(gas, T, S, p)
    z = pgas.abn(gas)
    return Ceq + (1 - F) * A * z / (1 + F * A * z / Ceq)
CEModel1 = GasExchangeModel(ce_model, ('degC', 'permille', 'atm', 'cc/g', ''), None)
CEModel2 = GasExchangeModel(ce_model, (None, None, None, None, None), None)


fit_CE1 = CEModel1.fit(pangadata,
                       ['T', 'A', 'F'],
                       init_guess=[Q(273.15, 'K'), 1e-5, 0.1],
                       tracers_used=gases_used,
                       #constraints={'T':[-10, 50], 'A':[0, 1e-2], 'F':[0, 1]},
                       constraints={'F':[-5e4, 5e4], 'A':[-10, 10], 'T':[-1000, 1000]},
                       tqdm_bar=True)

fit_CE2 = CEModel2.fit(pangadata,
                       ['T', 'A', 'F'],
                       init_guess=[0, 1e-5, 0.1],  
                       tracers_used=gases_used,
                       #constraints={'T':[-10, 50], 'A':[0, 1e-2], 'F':[0, 1]},
                       constraints={'F':[-5e4, 5e4], 'A':[-10, 10], 'T':[-1000, 1000]},
                       tqdm_bar=True)

print('Fit of CE model 1:')
print(fit_CE1[['Sample', 'T', 'A', 'F']])
print('Fit of CE model 2:')
print(fit_CE2[['Sample', 'T', 'A', 'F']])