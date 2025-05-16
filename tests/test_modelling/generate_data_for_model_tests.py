# Here you can generate some artificial data to test the OD, PR and UA models.
# NOTE: I have tried implementing this for CE and PD models, but the artificial data generated does
# not seem to be easily fitted by them. Perhaps the models should have more restrictions on the
# randomised parameters.

import sys
sys.path.insert(0, 'C:/Users/scopi/source/repos/PAGOS/PAGOS/src')
from pagos import GasExchangeModel
from pagos.builtin_models import ua, pr, od
import numpy as np
from pagos.constants import NOBLEGASES
import pandas as pd

UAModel = GasExchangeModel(ua, ['degC', 'permille', 'atm', 'cc/g'], 'cc/g')
PRModel = GasExchangeModel(pr, ['degC', 'permille', 'atm', 'cc/g', '', ''], 'cc/g')
ODModel = GasExchangeModel(od, ['degC', 'permille', 'atm', 'cc/g', ''], 'cc/g')

# generate randomly distributed parameters T, S, p, A, FPR, POD
Ts = np.random.uniform(0, 35, 100)
Ss = np.random.uniform(0, 50, 100)
Ps = np.random.uniform(0.95, 1.05, 100)
As = np.random.uniform(0, 1e-4, 100)
FPRs = np.random.uniform(0.1, 0.9, 100)
PODs = np.random.uniform(0, 1, 100)

# generate noble gas concentrations based on the parameters
gen_data_UA = pd.DataFrame(columns=['T', 'S', 'p', 'A', 'He', 'Ne', 'Ar', 'Kr', 'Xe', 'He err', 'Ne err', 'Ar err', 'Kr err', 'Xe err'])
gen_data_PR = pd.DataFrame(columns=['T', 'S', 'p', 'A', 'FPR', 'He', 'Ne', 'Ar', 'Kr', 'Xe', 'He err', 'Ne err', 'Ar err', 'Kr err', 'Xe err'])
gen_data_OD = pd.DataFrame(columns=['T', 'S', 'p', 'A', 'POD', 'He', 'Ne', 'Ar', 'Kr', 'Xe', 'He err', 'Ne err', 'Ar err', 'Kr err', 'Xe err'])

for i in range(len(Ts)):
    T = Ts[i]
    S = Ss[i]
    p = Ps[i]
    A = As[i]
    FPR = FPRs[i]
    POD = PODs[i]

    # calculate noble gas concentrations
    UAHe, UANe, UAAr, UAKr, UAXe = [x.magnitude for x in UAModel.run(NOBLEGASES, T, S, p, A)]
    PRHe, PRNe, PRAr, PRKr, PRXe = [x.magnitude for x in PRModel.run(NOBLEGASES, T, S, p, A, FPR, 1)]
    ODHe, ODNe, ODAr, ODKr, ODXe = [x.magnitude for x in ODModel.run(NOBLEGASES, T, S, p, A, POD)]

    # generate random relative errors between 0.5 and 2 %
    He_err = np.random.uniform(0.005, 0.02)
    Ne_err = np.random.uniform(0.005, 0.02)
    Ar_err = np.random.uniform(0.005, 0.02)
    Kr_err = np.random.uniform(0.005, 0.02)
    Xe_err = np.random.uniform(0.005, 0.02)

    # add the data to the dataframe
    app_UA = pd.DataFrame({'T': T, 'S': S, 'p': p, 'A': A, 'He': UAHe, 'Ne': UANe, 'Ar': UAAr, 'Kr': UAKr, 'Xe': UAXe,
                          'He err': He_err*UAHe, 'Ne err': Ne_err*UANe, 'Ar err': Ar_err*UAAr, 'Kr err': Kr_err*UAKr, 'Xe err': Xe_err*UAXe}, index=[0])
    app_PR = pd.DataFrame({'T': T, 'S': S, 'p': p, 'A': A, 'FPR': FPR, 'beta': 1, 'He': PRHe, 'Ne': PRNe, 'Ar': PRAr, 'Kr': PRKr, 'Xe': PRXe,
                          'He err': He_err*PRHe, 'Ne err': Ne_err*PRNe, 'Ar err': Ar_err*PRAr, 'Kr err': Kr_err*PRKr, 'Xe err': Xe_err*PRXe}, index=[0])
    app_OD = pd.DataFrame({'T': T, 'S': S, 'p': p, 'A': A, 'POD': POD, 'He': ODHe, 'Ne': ODNe, 'Ar': ODAr, 'Kr': ODKr, 'Xe': ODXe,
                          'He err': He_err*ODHe, 'Ne err': Ne_err*ODNe, 'Ar err': Ar_err*ODAr, 'Kr err': Kr_err*ODKr, 'Xe err': Xe_err*ODXe}, index=[0])

    gen_data_UA = pd.concat([gen_data_UA, app_UA], ignore_index=True)
    gen_data_PR = pd.concat([gen_data_PR, app_PR], ignore_index=True)
    gen_data_OD = pd.concat([gen_data_OD, app_OD], ignore_index=True)

print(gen_data_OD)

# save the data to a csv file
gen_data_UA.to_csv('C:/Users/scopi/source/repos/PAGOS/PAGOS/tests/assets/data_for_UA.csv', index=False)
gen_data_PR.to_csv('C:/Users/scopi/source/repos/PAGOS/PAGOS/tests/assets/data_for_PR.csv', index=False)
gen_data_OD.to_csv('C:/Users/scopi/source/repos/PAGOS/PAGOS/tests/assets/data_for_OD.csv', index=False)
