"""
Here is a tutorial on the implementation of Jacobian matrices in models in PAGOS.
"""

# Importing
from pagos.gas import ice, abn, calc_Ceq, calc_dCeq_dT, calc_dCeq_dS, calc_dCeq_dp
from pagos.modelling import GasExchangeModel
from pagos import Q
import pandas as pd

# By default, lmfit, the module that PAGOS uses to fit models, must estimate the Jacobian matrix
# (the matrix whose columns are the derivatives of the residuals with respect to the fitted
# parameters of the model) in order to fit the model. This is because it implements the MINPACK
# algorithm of the Levenberg-Marquardt least-squares fitting method (see
# https://cds.cern.ch/record/126569/files/CM-P00068642.pdf for more technical details).

# The user may instead choose to provide the analytical function defining the Jacobian for speed
# improvement by saving the machine the trouble of having to estimate the Jacobian.
# NOTE: This is still work-in-progress. My current experiments have indicated that providing a
# user-defined Jacobian with certain models can actually lead to slower fitting. So this may be
# quite temperamental.

# Start by importing the relevant modules:

from pagos import builtin_models as pbim
from pagos.modelling import GasExchangeModel
import numpy as np

# We will use the UA model once again as an example:
ua_model = pbim.ua

# The functional definition of ua_model can be found in builtin_models.py. Mathematically, it is:
# Cᵢ = Cₑᵢ(T, S, p) + Aχᵢ
# where
# Cₑ(T, S, p) = equilibrium concentration at water recharge temperature T, salinity S and air pressure p
# A = excess air in same units as Cₑ
# χ = atmospheric abunance of given gas
# i indexes the gas (i = Ne, Ar, Kr, Xe in the below case)
#
# See Jung and Aeschbach 2018 (https://doi.org/10.1016/j.envsoft.2018.02.004) for more details.

# We can therefore define the Jacobian matrix thus:
# Jᵢⱼ = ∂Rᵢ/∂Pⱼ
# where
# R is the residual vector, Rᵢ = (modelledᵢ - observedᵢ) / obs_errorᵢ
# P is the vector of model parameters, in this case (T, S, p, A)
# i indexes the gas and j indexes the parameter
#
# In our case: Jᵢ = (∂Cₑᵢ/∂T, ∂Cₑᵢ/∂S, ∂Cₑᵢ/∂p, ∂(Aχᵢ)/∂A) = (∂Cₑᵢ/∂T, ∂Cₑᵢ/∂S, ∂Cₑᵢ/∂p, χᵢ)
# Writing this in code is done thus:
def ua_jacobian(gas, T, S, p, A):       # <- note that the signature of the jacobian must be IDENTICAL to that of the fitted function, even if some parameters are not used
    jT = calc_dCeq_dT(gas, T, S, p)     # <- here we make use of the derivative calculator for equilibrium concentration provided by PAGOS
    jS = calc_dCeq_dS(gas, T, S, p)
    jp = calc_dCeq_dp(gas, T, S, p)
    jA = abn(gas)
    return np.array([jT, jS, jp, jA])   # <- a list/array of derivatives w.r.t. parameters should be returned
# IMPORTANT: this Jacobian is actually that of the model function, NOT of the residual. All
# Jacobians passed to PAGOS GasExchangeModels should be like this.

# Now we create the GasExchangeModel object, as in 5_fitting_models.py, but now with an extra
# argument for the Jacobian function:
UAModel = GasExchangeModel(ua_model, ('degC', 'permille', 'atm', 'cc/g'), 'cc/g',
                           jacobian=ua_jacobian)

# We can run this model exactly as we did before:
pangadata = pd.read_csv('example scripts/Example Data/Complete_Input_Data_Samples_Belgium.CSV', sep=',')
fit_UA = UAModel.fit(pangadata,                                             # the data as a Pandas DataFrame
                     to_fit=['T', 'A'],                                     # the arguments of the model we would like to fit
                     init_guess=[1, 1e-5],                       # the initial guesses for the parameters to be fit
                     tracers_used=['Ne', 'Ar', 'Kr', 'Xe'],                 # the tracers used for the fitting procedure
                     tqdm_bar=True)                                         # whether to display a progress bar

# And we can compare the result to one obtained without the Jacobian:
UAModel_no_jacobian = GasExchangeModel(ua_model, ('degC', 'permille', 'atm', 'cc/g'), 'cc/g')
fit_UA_no_jacobian = UAModel_no_jacobian.fit(pangadata, to_fit=['T', 'A'], init_guess=[Q(1, 'degC'), 1e-5],
                                             tracers_used=['Ne', 'Ar', 'Kr', 'Xe'], tqdm_bar=True)

print(fit_UA.compare(fit_UA_no_jacobian))

# In the comparison, we can see that the results are identical when using the Jacobian or not. In
# this case, it actually takes longer to compute WITH the Jacobian, which is unexpected. This file
# therefore remains work-in-progress.