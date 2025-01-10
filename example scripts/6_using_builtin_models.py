"""
Here is a tutorial on how to employ the gas exchange models already built-in to PAGOS.
"""

from pagos import Q
import pandas as pd

# There are a few models already present in PAGOS, which have been used in research at the
# Institute for Environmental Physics, Heidelberg, Germany. Some were developed for the Ventilation
# and Anthropogenic Carbon in the Arctic Ocean (VACAO) project as part of the Synoptic Arctic
# Survey 2021, and model the exchange of noble gases at the surface of the Arctic Ocean due to
# various physical processes, such as bubble injection, sea-ice formation and rapid cooling.

# The dataset which we use these models on is not yet published, so for now, we will focus on the
# groundwater dataset and models which we have been using in the previous example scripts. In the
# near future, examples of our published data will be put here.

# Start by importing the relevant modules:

from pagos import builtin_models as pbim
from pagos.modelling import GasExchangeModel

# Let's select the UA model (see scripts 4 and 5 for more info), and make the GasExchangeModel:

ua_model = pbim.ua
UAModel = GasExchangeModel(ua_model, ('degC', 'permille', 'atm', 'cc/g'), 'cc/g')

# We can now use this model exactly as we did in the previous sections, the difference here being
# only that we didn't have to define the model function ourselvs. Neat!

pangadata = pd.read_csv('example scripts/Example Data/Complete_Input_Data_Samples_Belgium.CSV', sep=',')
fit_UA = UAModel.fit(pangadata,                                             # the data as a Pandas DataFrame
                     to_fit=['T', 'A'],                                     # the arguments of the model we would like to fit
                     init_guess=[Q(1, 'degC'), 1e-5],                       # the initial guesses for the parameters to be fit
                     tracers_used=['Ne', 'Ar', 'Kr', 'Xe'],                 # the tracers used for the fitting procedure
                     #constraints={'T_recharge':[-10, 50], 'A':[0, 1e-2]},  # any constraints we might want to place on our fitted parameters
                     tqdm_bar=True)                                         # whether to display a progress bar
print('Fit of UA model:')
print(fit_UA[['Sample', 'T', 'A']])
