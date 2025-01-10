"""
Functions for fitting models, creating new ones and running existing ones.
"""
from pint import Quantity, Unit
from uncertainties import ufloat
from uncertainties.core import Variable, AffineScalarFunc
from collections.abc import Iterable
from typing import Callable
import inspect
import numpy as np
import pandas as pd
from lmfit import minimize, Parameters, Model, Minimizer
import wrapt
from tqdm import tqdm
from inspect import signature
import re

from pagos.core import u as _u, Q as _Q, snv as _snv, ssd as _ssd, sgu as _sgu, sto as _sto, units_are_equal as _uae
from pagos._pretty_gas_wrappers import oneormoregases


class GasExchangeModel:
    def __init__(self, model_function, default_units_in, default_units_out, jacobian=None, jacobian_units=None):
        # set instance variables
        # if default_units_in argument did not include None at the start for the gas parameter, add this in here
        self._model_function_in = model_function
        self.default_units_in = self._check_units_list_against_sig(model_function, default_units_in)
        self.default_units_out = default_units_out
        self.model_arguments = inspect.getfullargspec(self._model_function_in).args
        self.default_units_in_dict = {key:val for key, val in zip(self.model_arguments, self.default_units_in)}
        self._jacobian_in = jacobian
        self.jacobian_units = jacobian_units
        # the function and jacobian that will run if the user does not specify units_in or units_out when calling run()
        self.model_function = _u.wraps(self.default_units_out, self.default_units_in, strict=False)(self._model_function_in)
        self.model_func_sig = signature(self.model_function)
        if self._jacobian_in is None:
            self.runjac = None
        else:
            self.model_jacobian = _u.wraps(self.jacobian_units, self.default_units_in, strict=False)(self._jacobian_in)
            self.model_jac_sig = signature(self.model_jacobian)
    

    def run(self, *args_to_model_func, units_in='default', units_out='default', **kwargs_to_model_func):
        # prescribe units if units out or in differ from defaults
        if units_in == 'default':
            units_in = self.default_units_in_dict
        elif type(units_in) != dict:
            # set the units_in - append a None value to the units_in tuple for the "units" of the gas argument if this has not already been done by the user
            units_in = self._check_units_list_against_sig(self._model_function_in, units_in)
            # if units are provided in the form of an array instead of a dict, make it a dict
            units_in = {k:u for k, u in zip(self.model_func_sig.parameters, units_in)}
        else:
            units_in = self._check_units_dict_against_sig(self._model_function_in, units_in)
        args_to_model_func = self._convert_or_make_quants_list(args_to_model_func, units_in)
        kwargs_to_model_func = self._convert_or_make_quants_dict(kwargs_to_model_func, units_in)

        # TODO is wraps functionality lost here by passing in quantites?       
        result = self.model_function(*args_to_model_func, **kwargs_to_model_func)
        if units_out != 'default':
            result = _sto(result, units_out, strict=False)
        return result
    
    def runjac(self, *args_to_jac_func, units_in='default', units_out='default', **kwargs_to_jac_func):
        # NOTE I think due to the nature of this construction, jacobian should always have the same signature as model_function
        # prescribe units if units out or in differ from defaults
        if units_in == 'default':
            units_in = self.default_units_in_dict
        elif type(units_in) != dict:
            # set the units_in - append a None value to the units_in tuple for the "units" of the gas argument if this has not already been done by the user
            units_in = self._check_units_list_against_sig(self._jacobian_in, units_in)
            # if units are provided in the form of an array instead of a dict, make it a dict
            units_in = {k:u for k, u in zip(self.model_jac_sig.parameters, units_in)}
        else:
            units_in = self._check_units_dict_against_sig(self._jacobian_in, units_in)
        args_to_jac_func = self._convert_or_make_quants_list(args_to_jac_func, units_in)
        kwargs_to_jac_func = self._convert_or_make_quants_dict(kwargs_to_jac_func, units_in)
        

        result = self.model_jacobian(*args_to_jac_func, **kwargs_to_jac_func) 
        if units_out != 'default':
            result = _sto(result, units_out, strict=False)
        return result
    

    @staticmethod
    def _check_units_list_against_sig(func, units):
        if len(units) == len(signature(func).parameters) - 1:
            return (None,) + units
        else:
            return units
    

    @staticmethod
    def _check_units_dict_against_sig(func, units):
        sigparams = signature(func).parameters
        if len(units) == len(sigparams) - 1:
            ret = units
            gasparam = [p for p in sigparams if p not in units][0]
            ret[gasparam] = None
            return ret
        else:
            return units

    
    @staticmethod
    def _convert_or_make_quants_list(values, units):
        ret = [v if units[k] is None else _sto(v, units[k]) if isinstance(v, Quantity) else _Q(v, units[k]) for v, k in zip(values, units)]
        return ret
    

    @staticmethod
    def _convert_or_make_quants_dict(valsdict, units):
        ret = {k:(v if units[k] is None else _sto(v, units[k]) if isinstance(v, Quantity) else _Q(v, units[k]))
               for v, k in zip(valsdict.values(), valsdict.keys())}
        return ret
        
    
    def fit(self, data:pd.DataFrame, to_fit:Iterable[str], init_guess:Iterable[float], tracers_used:Iterable[str], custom_labels:dict=None, constraints:dict=None, **kwargs) -> pd.DataFrame:   # TODO init_guess is currently only a 1D list, perhaps should be allowed to take a second dimension the same length as data?
         # input to objective function: all parameters (fitted and set), tracers to calculate, observed data and their errors, parameter and tracer units
        def objfunc(parameters, tracers, observed_data, observed_errors, tracer_units):
            # separation of parameter names and values
            parameter_names = list(parameters.valuesdict().keys())
            parameter_values = list(parameters.valuesdict().values())
            paramsdict = {parameter_names[i]:parameter_values[i] for i in range(len(parameter_names))}
            """# re-assemble Quantity objects that were disassembled for usage in lmfit Parameter instances
            if any(not _uae(parameter_units[p], self.default_units_in_dict[p]) for p in parameter_units.keys()):
                for p in parameter_units.keys():
                    if not _uae(parameter_units[p], self.default_units_in_dict[p]):
                        paramsdict[p] = _Q(paramsdict[p], parameter_units[p])""" # TODO DELETE ME?
            modelled_data = self.run(tracers, **paramsdict)
            # perform conversion of units of result if necessary
            if hasattr(modelled_data, 'units'):
                modelled_data = _convertandgetmag(modelled_data, tracer_units)
            
            # if there is an error associated with every observation, weight by the errors
            if all(e is not None for e in observed_errors): #OLD CODE, if a problem arises here, check if reverting back to this fixes it: if observed_errors is not None:
                return (observed_data - modelled_data) / observed_errors
            else:
                return observed_data - modelled_data
        

        def jacfunc(parameters, tracers, observed_data, observed_errors, tracer_units):
            # separation of parameter names and values
            parameter_names = list(parameters.valuesdict().keys())
            parameter_values = list(parameters.valuesdict().values())
            paramsdict = {parameter_names[i]:parameter_values[i] for i in range(len(parameter_names))}
            """# re-assemble Quantity objects that were disassembled for usage in lmfit Parameter instances
            if any(not _uae(parameter_units[p], self.default_units_in_dict[p]) for p in parameter_units.keys()):
                for p in parameter_units.keys():
                    if not _uae(parameter_units[p], self.default_units_in_dict[p]):
                        paramsdict[p] = _Q(paramsdict[p], parameter_units[p])""" # TODO DELETE ME?

            modelled_jac = self.runjac(tracers, **paramsdict)

            # Jacobian term selection (different Jacobian depending on which parameters are to be fitted)
            # e.g. if only parameters T, S of a model C(T, S, p, A) are to be fitted, Jacobian should be [dC/dT, dC/dS] without p and A derivatives
            jindx = [i for i, p in enumerate(list(self.model_jac_sig.parameters)[1:]) if p in to_fit]
            # make non-array terms into full arrays, e.g. [a, b, [c1, c2, c3]] --> [[a, a, a], [b, b, b], [c1, c2, c3]]
            ntracers = len(tracers)
            jac_cut_to_fit = [0 for _ in range(len(jindx))]
            for c, i in enumerate(jindx):
                Ji = modelled_jac[i]
                if (isinstance(Ji, Iterable) and not isinstance(Ji, Quantity)) or (isinstance(Ji, Quantity) and isinstance(Ji.magnitude, Iterable)):
                    if len(Ji) != ntracers:
                        raise ValueError('There is an element (index %s) of the jacobian with length %s. It must be either length 1 or %s' % (i, len(Ji), ntracers))
                    else:
                        jac_cut_to_fit[c] = Ji
                else:
                    jac_cut_to_fit[c] = [Ji for _ in range(ntracers)]

            # perform conversion of units of result if necessary
            if hasattr(jac_cut_to_fit, 'units'):
                jac_cut_to_fit = _convertandgetmag(jac_cut_to_fit, tracer_units)
            elif any(hasattr(elt, 'units') for elt in modelled_jac):
                # TODO this is a slow and dirty fix for now... 
                # jacobian in future should always be in form [Q([J11, J12, ...]), Q([J21, J22, ...]), ...] 
                #                                   and never [[Q(J11), Q(J12), ...], [Q(J21), Q(J22), ...], ...]
                jac_cut_to_fit = [_convertandgetmag(Ji, tracer_units) if hasattr(Ji, 'units') 
                                  else _convertandgetmag(_Q([Jij.magnitude for Jij in Ji], Ji[0].units), tracer_units)
                                  for Ji in jac_cut_to_fit]
            
            return np.array(jac_cut_to_fit).transpose()
    
        model_arg_names = self.model_arguments
        data_headers = data.columns.values.tolist()
        output_list = []
        fitted_only_out = False
        nrows = range(len(data))

        dont_fit_these_args = [a for a in model_arg_names if a not in to_fit]
        if custom_labels is None:
            arg_tracer_labels = {x:x for x in tracers_used + dont_fit_these_args}
        else:
            arg_tracer_labels = {x:(custom_labels[x] if x in custom_labels else x) for x in tracers_used + dont_fit_these_args}
        # OLD CODE
        '''
        if arg_tracer_labels == None:
            # default behaviour for no input in tracer labels: take the user-given
            # names of the tracers used and the set names of the args of modelfunc
            # which are not to be fit.
            dont_fit_these_args = [a for a in model_arg_names if a not in to_fit]
            arg_tracer_labels = {x:x for x in tracers_used + dont_fit_these_args}'''

        # keyword argument handling
        for k in kwargs.keys():
            kv = kwargs[k]
            # terminal loading bar
            if k == 'tqdm_bar':
                if kv == True:
                    nrows = tqdm(range(len(data)))
            # whether to output all data + fitted parameters or only fitted parameters
            if k == 'fitted_only':
                if kv == True:
                    fitted_only_out = True
        
        # prepare data for fit
        data_obs, data_errs, data_units = _prepare_data(data, list(arg_tracer_labels.values()))
        # OLD CODE
        '''# checking for errors on tracers TODO this is still quite primitive, can be made more powerful
        if all(t + ' err' in data_headers for t in tracers_used):
            errs_present_as_col, errstructure = True, 'right'
        elif all('err ' + t in data_headers for t in tracers_used):
            errs_present_as_col, errstructure = True, 'left'
        else:
            errs_present_as_col = False'''

        # fit procedure for every row
        for r in nrows:
            # parameters to be fitted by lmfit initialised here.
            # lmfit's Parameter class cannot hold uncertainty/unit information that Pint Quantity objects can,
            # therefore we disassemble those objects into their magnitudes and units and then reassemble them
            # in the objective function (see also above).
            #param_units = {}    # dictionary of units of parameters to be used internally  # TODO DELETE ME?
            all_params = Parameters()
            model_sig_as_list = list(self.model_func_sig.parameters)
            for i in range(len(to_fit)):
                # convert units of the initial guess to the default_units_in of the function, so we can save on speed
                p = to_fit[i]
                igi = init_guess[i]
                def_unit = self.default_units_in_dict[p]
                if not isinstance(igi, Quantity):
                    igi = _u.Quantity(igi, def_unit)
                igi = _sto(igi, def_unit).magnitude # <- strip initial guesses of units, for further speed improvements
                
                if constraints is not None and p in constraints.keys():
                    # here the same story as for the initial guesses, but with their constraints
                    min_ = constraints[p][0]
                    max_ = constraints[p][1]
                    if not isinstance(min_, Quantity):
                        min_ = _u.Quantity(min_, def_unit)
                    if not isinstance(max_, Quantity):
                        max_ = _u.Quantity(max_, def_unit)
                    min_ = _sto(min_, def_unit).magnitude
                    max_ = _sto(max_, def_unit).magnitude
                    all_params.add(p, value=igi, vary=True, min=min_, max=max_)
                else:
                    all_params.add(p, value=igi, vary=True)
                #param_units[p] = u TODO DELETE ME?


            # parameters set by observation initialised here
            # similar logic regarding unit dissassembly applies here (see above)  
            for a in model_arg_names:
                if a in arg_tracer_labels and arg_tracer_labels[a] in data_headers:
                    # convert the units of values in data to the default_units_in, to save on speed
                    v = data[arg_tracer_labels[a]][r]
                    def_unit = self.default_units_in_dict[a]
                    if not isinstance(v, Quantity):
                        v = _u.Quantity(v, def_unit)
                    v = _sto(v, def_unit).magnitude # <- strip value of units, for further speed improvements
                    # extract nominal value if magnitude is an uncertainties Variable
                    if isinstance(v, (Variable, AffineScalarFunc)):
                        v = v.nominal_value
                    all_params.add(a, value=v, vary=False)
            
            # prepare the data for the minimisation process
            obs_tracerdata_in_row = np.array([data_obs[arg_tracer_labels[t]][r] for t in tracers_used])
            obs_tracerdata_errs_in_row = np.array([data_errs[arg_tracer_labels[t]][r] for t in tracers_used])
            obs_tracerdata_units_in_row = np.array([data_units[arg_tracer_labels[t]][r] for t in tracers_used])
            # OLD CODE
            '''
            obs_tracerdata_in_row = np.array([_snv(data[arg_tracer_labels[t]][r]) for t in tracers_used])
            if errs_present_as_col:
                if errstructure == 'right':
                    obs_tracerdata_errs_in_row = np.array([_snv(data[arg_tracer_labels[t] + ' err'][r]) for t in tracers_used])
                elif errstructure == 'left':
                    obs_tracerdata_errs_in_row = np.array([_snv(data['err ' + arg_tracer_labels[t]][r]) for t in tracers_used])
            else:
                obs_tracerdata_errs_in_row = np.array([_ssd(data[arg_tracer_labels[t]][r]) for t in tracers_used])
            obs_tracerdata_units_in_row = np.array([_sgu(data[arg_tracer_labels[t]][r]) for t in tracers_used])'''#

            # set Jacobian to None if none was provided in the model
            if self.runjac is None:
                jacfunc = None
            
            # remove nan values in row for fitting TODO can probably be made more efficient
            nan_indices_in_tracerdata = np.argwhere(np.isnan(obs_tracerdata_in_row)).flatten()
            nan_indices_in_errordata = np.argwhere(np.isnan(obs_tracerdata_errs_in_row)).flatten()
            nan_indices_in_data = np.union1d(nan_indices_in_tracerdata, nan_indices_in_errordata)
            obs_tracerdata_in_row = [obs_tracerdata_in_row[i] for i in range(len(obs_tracerdata_in_row)) if i not in nan_indices_in_data]
            obs_tracerdata_errs_in_row = [obs_tracerdata_errs_in_row[i] for i in range(len(obs_tracerdata_errs_in_row)) if i not in nan_indices_in_data]
            obs_tracerdata_units_in_row = [obs_tracerdata_units_in_row[i] for i in range(len(obs_tracerdata_units_in_row)) if i not in nan_indices_in_data]
            valid_tracers_used = [tracers_used[i] for i in range(len(tracers_used)) if i not in nan_indices_in_data]
                
            mzer = Minimizer(objfunc, all_params, fcn_args=(valid_tracers_used, obs_tracerdata_in_row, obs_tracerdata_errs_in_row, obs_tracerdata_units_in_row))
            M = mzer.leastsq(Dfun=jacfunc, col_deriv=0, factor=0.001)
            #M = mzer.least_squares(jac=jacfunc) # APPEARS NOT TO WORK
            #M = minimize(objfunc, all_params, args=(valid_tracers_used, obs_tracerdata_in_row, obs_tracerdata_errs_in_row, obs_tracerdata_units_in_row), method='leastsq', nan_policy='omit', Dfun=jacfunc)
            optimised_params = M.params
            result_chisqr, result_redchi, result_aic, result_bic = M.chisqr, M.redchi, M.aic, M.bic
            optimised_param_quants_and_statistics = {}
            for p in to_fit:
                v, e = optimised_params[p].value, optimised_params[p].stderr
                if v is None: # protection for if None values are returned by the fit
                    v = np.nan
                if e is None:
                    e = np.nan
                optimised_param_quants_and_statistics[p] = _u.Quantity(ufloat(v, e), self.default_units_in_dict[p])
            optimised_param_quants_and_statistics['chi2'] = result_chisqr
            optimised_param_quants_and_statistics['red chi2'] = result_redchi
            optimised_param_quants_and_statistics['aic'] = result_aic
            optimised_param_quants_and_statistics['bic'] = result_bic
            output_list.append(optimised_param_quants_and_statistics)
        
        output_dataframe = pd.DataFrame(output_list)
        if not fitted_only_out:
            output_dataframe = data.join(output_dataframe)

        return output_dataframe


def _convertandgetmag(modelled_data, tracer_units):
    modelled_units = modelled_data.units
    musinglet, tusinglet = isinstance(modelled_units, Unit), isinstance(tracer_units, Unit)
    def convertandgetmag1():
        nonlocal modelled_data
        return modelled_data.magnitude
    def convertandgetmag2():
        nonlocal modelled_data
        return np.array([_sto(modelled_data[i], tracer_units[i]).magnitude for i in range(len(tracer_units))])
    
                                                                                        # cases, where M, T are the modelled and tracer units:
    if musinglet and tusinglet:                                                             # M ; T
        if modelled_units == tracer_units:                                                      # M = T
            return convertandgetmag1()                                                              # M -> M
        else:                                                                                   # M ≠ T
            return convertandgetmag2()                                                              # M -> T

    elif musinglet:                                                                         # M ; T = {T₁, T₂, ...}
        if all(tu == modelled_units for tu in tracer_units):                                    # ∀i : Tᵢ = M
            return convertandgetmag1()                                                              # M -> M
        else:                                                                                   # ∃i : Tᵢ ≠ M
            return convertandgetmag2()                                                              # M -> Tᵢ
        
    elif tusinglet:                                                                         # M = {M₁, M₂, ...} ; T
        if all(mu == tracer_units for mu in modelled_units):                                    # ∀i : Mᵢ = T
            return convertandgetmag1()                                                              # M -> M
        else:                                                                                   # ∃i : Mᵢ ≠ T
            return convertandgetmag2()                                                              # Mᵢ -> T
        
    else:                                                                                   # M = {M₁, M₂, ...} ; T = {T₁, T₂, ...}
        if all(modelled_units[i] == tracer_units[i] for i in range(len(modelled_units))):       # ∀i : Mᵢ = Tᵢ
            return convertandgetmag1()                                                              # M -> M
        else:                                                                                   # ∃i : Mᵢ ≠ Tᵢ
            return convertandgetmag2()                                                              # Mᵢ -> Tᵢ
        

def _convertandgetmag_jac(modelled_jac, tracer_units):
    # TODO: could there be cases where there are no units?
    modelled_units = modelled_jac.units
    musinglet, tusinglet = isinstance(modelled_units, Unit), isinstance(tracer_units, Unit)
    def convertandgetmag1():
        nonlocal modelled_jac
        return modelled_jac.magnitude
    def convertandgetmag2():
        nonlocal modelled_jac
        return np.array([_sto(modelled_jac[i], tracer_units[i]).magnitude for i in range(len(tracer_units))])
    
                                                                                        # cases, where M, T are the modelled and tracer units:
    if musinglet and tusinglet:                                                             # M ; T
        if modelled_units == tracer_units:                                                      # M = T
            return convertandgetmag1()                                                              # M -> M
        else:                                                                                   # M ≠ T
            return convertandgetmag2()                                                              # M -> T

    elif musinglet:                                                                         # M ; T = {T₁, T₂, ...}
        if all(tu == modelled_units for tu in tracer_units):                                    # ∀i : Tᵢ = M
            return convertandgetmag1()                                                              # M -> M
        else:                                                                                   # ∃i : Tᵢ ≠ M
            return convertandgetmag2()                                                              # M -> Tᵢ
        
    elif tusinglet:                                                                         # M = {M₁, M₂, ...} ; T
        if all(mu == tracer_units for mu in modelled_units):                                    # ∀i : Mᵢ = T
            return convertandgetmag1()                                                              # M -> M
        else:                                                                                   # ∃i : Mᵢ ≠ T
            return convertandgetmag2()                                                              # Mᵢ -> T
        
    else:                                                                                   # M = {M₁, M₂, ...} ; T = {T₁, T₂, ...}
        if all(modelled_units[i] == tracer_units[i] for i in range(len(modelled_units))):       # ∀i : Mᵢ = Tᵢ
            return convertandgetmag1()                                                              # M -> M
        else:                                                                                   # ∃i : Mᵢ ≠ Tᵢ
            return convertandgetmag2()                                                              # Mᵢ -> Tᵢ
        

def _prepare_data(data:pd.DataFrame, obs_labels:list):
    data_headers = data.columns.values.tolist()
    lendata = len(data)

    # parse observations
    # regex pattern for tracers in column headings
    pattern = r'\b(' + '|'.join(obs_labels) + r')\b'

    # filter columns that match the pattern, case insensitive
    selected_columns = [dh for dh in data_headers if re.search(pattern, dh, re.IGNORECASE)]

    # parse errors and units
    # define the regex patterns for errors and units on observations
    error_pattern = r'\b(err|errs|error|errors|uncertainty|uncertainties|sigma|sigmas|err\.|err\.s)\b'
    unit_pattern = r'\b(unit|units|dim|dims|dimension|dimensions|dim\.|dim\.s)\b'

    obs_col_names = []
    err_col_names = []
    unit_col_names = []

    # iterate over the column names with tracer information
    for col in selected_columns:
        # check if the name matches an error pattern
        if re.search(error_pattern, col, re.IGNORECASE):
            # if it's an error column, try to find the corresponding observation column
            # remove 'err' or similar keywords from the current column name
            base_name = re.sub(error_pattern, '', col, flags=re.IGNORECASE).strip()
            if base_name in selected_columns:
                obs_col_names.append(base_name)
                err_col_names.append(col)
            else:
                # if no corresponding observation is found, throw a warning
                raise Warning(f"The column '{col}' has been parsed as an error/uncertainty, but has no corresponding measurement. It has been ignored.")
        else:
            # if it's an observation column, check if it has a corresponding error column
            base_name = col
            error_col = None
            # search for the error column corresponding to this observation
            for err_col in selected_columns:
                if re.search(error_pattern, err_col, re.IGNORECASE):
                    # check if the base observation name appears in the error column
                    if base_name in err_col:
                        error_col = err_col
                        break
            if error_col:
                # if it does have a corresponding error, ignore it
                continue
            else:
                # if no corresponding error column exists, append with None as the error
                obs_col_names.append(base_name)
                err_col_names.append(None)
        
        # third parsing step for units
        # check if there is a corresponding column for units using the unit regex pattern
        unit_col = None
        for unit_candidate in selected_columns:
            if re.search(unit_pattern, unit_candidate, re.IGNORECASE):
                if base_name in unit_candidate:
                    unit_col = unit_candidate
                    break
        if unit_col:
            unit_col_names.append(unit_col)
        else:
            # if no corresponding unit column is found, append None as the unit
            unit_col_names.append(None)

    obs_out = {}
    errs_out = {}
    units_out = {}
    # construct observations and errors DataFrames to output
    for ocn, ecn, ucn in zip(obs_col_names, err_col_names, unit_col_names):
        # if the observations contain unit data, extract only the nominal values
        obs_out[ocn] = np.array([_snv(data[ocn][r]) for r in range(lendata)])
        # if the errors were given in a separate column, just take these values
        if ecn is not None:
            errs_out[ocn] = data[ecn]
        # if they weren't, try to extract them from the observations columns, and pad with None if necessary
        else:
            errs_out[ocn] = np.array([_ssd(data[ocn][r]) for r in range(lendata)])
        # if the units were given in a separate column, just take these values
        if ucn is not None:
            units_out[ocn] = data[ucn]
        # if they weren't, try to extract them from the observations columns, and pad with None if necessary
        else:
            units_out[ocn] = np.array([_sgu(data[ocn][r]) for r in range(lendata)])
    obs_out = pd.DataFrame(obs_out)
    errs_out = pd.DataFrame(errs_out)
    units_out = pd.DataFrame(units_out)
    # output the DataFrames
    return obs_out, errs_out, units_out