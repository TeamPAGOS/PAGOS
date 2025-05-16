"""
Here is a tutorial on how to fit gas exchange models in PAGOS.
"""

# Importing
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
UAModel = GasExchangeModel(ua_model, ['degC', 'permille', 'atm', 'cc/g'], None)

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
print(fit_UA[['T_recharge', 'A']])

# Note here that the init_guess arguments do NOT have to be Quantity objects, although they can be
# for clarity, if you want. When units are omitted, the default_units_in passed to the
# GasExchangeModel() constructor are used. So in this case, 1e-5 becomes 1e-5 cc/g.

# The ease of PAGOS's model definition means that we can easily define and fit a different model:
def ce_model(gas, T, S, p, A, F):
    Ceq = pgas.calc_Ceq(gas, T, S, p)
    z = pgas.abn(gas)
    return Ceq + (1 - F) * A * z / (1 + F * A * z / Ceq)
CEModel1 = GasExchangeModel(ce_model, ['degC', 'permille', 'atm', 'cc/g', ''], 'cc/g')
# Here we bypass the unit conversion altogether. It will not make too much of a difference on speed
# - perhaps only if there are thousands+ individual samples. This is not very safe though, as if we
# make a unit-related numerical mistake in our model, we would not be able to know. So only do this
# if you are 100% sure that your model is correct!
CEModel2 = GasExchangeModel(ce_model, [None, None, None, None, None], None)


fit_CE1 = CEModel1.fit(pangadata,
                       ['T', 'A', 'F'],
                       init_guess=[Q(273.15, 'K'), 1e-5, 0.1],              # <- here the K will be internally converted to degC before fitting
                       tracers_used=gases_used,
                       constraints=[[-1000, 1000], [-10, 10], [-1e4, 1e4]], # <- here no conversion takes place, as we have not declared any units, so the default units are assumed
                       tqdm_bar=True)

fit_CE2 = CEModel2.fit(pangadata,
                       ['T', 'A', 'F'],
                       init_guess=[0, 1e-5, 0.1],                           # <- here we cannot write in the temperature IG in K, because there are no default units to convert to, and we would make a numerical error
                       tracers_used=gases_used,
                       constraints=[[-1000, 1000], [-10, 10], [-1e4, 1e4]],
                       tqdm_bar=True)

print('Fit of CE model 1:')
print(fit_CE1[['T', 'A', 'F']])
print('Fit of CE model 2:')
print(fit_CE2[['T', 'A', 'F']])

# If you want to fit the data of one sample at a time (for instance if you are performing Monte
# Carlo analysis and wish to put a single fit procedure in a loop without deaing with creating
# thousands of DataFrames), you can do so according to this structure:
    # GasExchangeModel.fit(data=(<measured tracer values>, <measured tracer errors>, <measured tracer units>, <parameters set by observation>),
    #                      ...
    #                     )

# Here is an example, taking just the first row of our data:

data_vals = pangadata[gases_used].iloc[0].to_numpy()                            # [<valNe>, <valAr>, <valKr>, <valXe>]  the values of the measured tracers
data_errs = pangadata[['err %s' % ng for ng in gases_used]].iloc[0].to_numpy()  # [<errNe>, <errAr>, <errKr>, <errXe>]  the errors on those values
data_units = ['cc/g', 'cc/g', 'cc/g', 'cc/g']                                   # ['cc/g',  'cc/g',  'cc/g',  'cc/g']   the units of those values/errors
data_psbo = pangadata[['S', 'p']].iloc[0].to_numpy()                            # [<valS>,  <valp>]                     the values of parameters set by observation (S and p here; units are assumed to be default units of GasExchangeModel)

fit_CEsingle1 = CEModel1.fit((data_vals, data_errs, data_units, data_psbo),
                             ['T', 'A', 'F'],
                             init_guess=[0, 1e-5, 0.1],                           
                             tracers_used=gases_used,
                             constraints=[[-1000, 1000], [-10, 10], [-1e4, 1e4]],
                             tqdm_bar=True)

print('Single fit result:\n', fit_CEsingle1)

# We can also pass one unit string in as the units for the data, and it will assume all measurements take these units:
fit_CEsingle2 = CEModel1.fit((data_vals, data_errs, 'cc/g', data_psbo),
                             ['T', 'A', 'F'],
                             init_guess=[0, 1e-5, 0.1],                           
                             tracers_used=gases_used,
                             constraints=[[-1000, 1000], [-10, 10], [-1e4, 1e4]],
                             tqdm_bar=True)

print('Single fit result with one unit in:\n', fit_CEsingle2)

# We can see that the result is identical to the first row of the previous fits.