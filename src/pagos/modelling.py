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
    """
    Object that holds a function representing a gas exchange model and its methods, including
    fitting to data and forward-modelling given an input.
    """
    def __init__(self, model_function:Callable, default_units_in:tuple[str, ...], default_units_out:str, jacobian:Callable=None, jacobian_units:str=None):
        """
        :param model_function: function represented in the GasExchangeModel object.
        :type model_function: Callable
        :param default_units_in: strings specifying the units of the input arguments to `model_function` that will be **assumed** if none are given.
        Must be in the same order as the arguments to `model_function`.
        :type default_units_in: tuple[str, ...]
        :param default_units_out: single string specifying which units to **convert** the output of `model_function` to.
        Note that conversion happens **after** calculation.
        :type default_units_out: str
        :param jacobian: function returning a numpy array of derivatives of `model_function` with respect to its parameters, i.e. a jacobian matrix.
        Defaults to None.
        :type jacobian: Callable, optional
        :param jacobian_units: strings specifying which units to **convert** the output of the `jacobian` to.
        Note that this has **no effect** on the `fit` method.
        Defaults to None
        :type jacobian_units: tuple[str, ...], optional
        """
        # force default units into tuple:
        if default_units_in == None or type(default_units_in) == str:
            default_units_in = (default_units_in,)
        else:
            default_units_in = tuple(default_units_in)
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
            if self.jacobian_units is None:
                self.jacobian_units = tuple([default_units_out if dui == '' else default_units_out + '/(' + dui + ')' for dui in default_units_in]) #NOTE maybe there is a better way to do this
                self.model_jacobian = _u.wraps(self.jacobian_units, self.default_units_in, strict=False)(self._jacobian_in)
                self.model_jac_sig = signature(self.model_jacobian)
            elif all((_u.Unit(default_units_out) / _u.Unit(ju)).is_compatible_with(_u.Unit(dui)) for dui, ju in zip(default_units_in, jacobian_units)):
                self.model_jacobian = _u.wraps(self.jacobian_units, self.default_units_in, strict=False)(self._jacobian_in)
                self.model_jac_sig = signature(self.model_jacobian)
            else:
                raise ValueError('Jacobian output units are incommensurable with the model function input and output units.\nShould follow dim[jacobian_i] = dim[output] / dim[input_i].')
    

    def run(self, *args_to_model_func, units_in='default', units_out='default', **kwargs_to_model_func):
        # prescribe units if units out or in differ from defaults
        if units_in == 'default':
            units_in = self.default_units_in_dict
        elif type(units_in) != dict:
            print('NOT DEFAULT NOT DICT')
            # set the units_in - append a None value to the units_in tuple for the "units" of the gas argument if this has not already been done by the user
            units_in = self._check_units_list_against_sig(self._model_function_in, units_in)
            # if units are provided in the form of an array instead of a dict, make it a dict
            units_in = {k:u for k, u in zip(self.model_func_sig.parameters, units_in)}
        else:
            print('NOT DEFAULT + DICT')
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
        

        result = list(self.model_jacobian(*args_to_jac_func, **kwargs_to_jac_func)) # TODO have to wrap this in list(), I think due to pint wraps() handling arrays... could this lead to performance slowdown via redundant casting?
        if units_out != 'default':
            result = _sto(result, units_out, strict=False, possit=(0, 1))   #possit keyword makes _sto iterate over result and units_out simultaneously, see core.py > _possibly_iterable
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
        # TODO DOCSTRING
        # input to objective function: all parameters (fitted and set), tracers to calculate, observed data and their errors, parameter and tracer units
        def objfunc(parameters, tracers, observed_data, observed_errors, tracer_units):
            # separation of parameter names and values
            parameter_names = list(parameters.valuesdict().keys())
            parameter_values = list(parameters.valuesdict().values())
            paramsdict = {parameter_names[i]:parameter_values[i] for i in range(len(parameter_names))}
            
            modelled_data = self.run(tracers, **paramsdict)

            # perform conversion of units of result if necessary
            if hasattr(modelled_data, 'units'):
                modelled_data = _convertandgetmag(modelled_data, tracer_units)
            
            # if there is an error associated with every observation, weight by the errors
            if all(e is not None for e in observed_errors): #OLD CODE, if a problem arises here, check if reverting back to this fixes it: if observed_errors is not None:
                return (modelled_data - observed_data) / observed_errors
            else:
                return modelled_data - observed_data
        

        def jacfunc(parameters, tracers, observed_data, observed_errors, tracer_units):
            # separation of parameter names and values
            parameter_names = list(parameters.valuesdict().keys())
            parameter_values = list(parameters.valuesdict().values())
            paramsdict = {parameter_names[i]:parameter_values[i] for i in range(len(parameter_names))}

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
                        raise ValueError('There is an element (index %s) of the jacobian with length %s. It must have length %s' % (i, len(Ji), ntracers))
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
            jac_cut_to_fit = np.array(jac_cut_to_fit)
            jac_cut_to_fit = jac_cut_to_fit / observed_errors
            return np.array(jac_cut_to_fit).transpose()
    
        model_arg_names = self.model_arguments
        data_headers = data.columns.values.tolist()
        output_list = []
        fitted_only_out = False
        nrows = range(len(data))

        # convert tracers_used to list
        if type(tracers_used) == np.ndarray:
            tracers_used = tracers_used.tolist()

        dont_fit_these_args = [a for a in model_arg_names if a not in to_fit]
        if custom_labels is None:
            arg_tracer_labels = {x:x for x in tracers_used + dont_fit_these_args}
        else:
            arg_tracer_labels = {x:(custom_labels[x] if x in custom_labels else x) for x in tracers_used + dont_fit_these_args}

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

        # fit procedure for every row
        for r in nrows:
            # parameters to be fitted by lmfit initialised here.
            # lmfit's Parameter class cannot hold uncertainty/unit information that Pint Quantity objects can,
            # therefore we disassemble those objects into their magnitudes and units and then reassemble them
            # in the objective function (see also above).
            all_params = Parameters()
            model_sig_as_list = list(self.model_func_sig.parameters) # TODO DELETE ME
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
            
            # prepare the data for the minimisation process - astype + tolist functions turn non-numeric values into np.nan
            obs_tracerdata_in_row = np.array([data_obs[arg_tracer_labels[t]][r] for t in tracers_used]).astype(np.float64).tolist()  # TODO: more testing to see if these astype statements break anything
            obs_tracerdata_errs_in_row = np.array([data_errs[arg_tracer_labels[t]][r] for t in tracers_used]).astype(np.float64).tolist()
            obs_tracerdata_units_in_row = np.array([data_units[arg_tracer_labels[t]][r] for t in tracers_used])

            # set Jacobian to None if none was provided in the model
            if self.runjac is None:
                jacfunc = None
            
            # remove nan values in row for fitting TODO can probably be made more efficient
            # get the indices of nan-values in tracer data and their errors. If all the errors are
            # nan, we assume the user wants to proceed ignoring errors
            nan_indices_in_tracerdata = np.argwhere(np.isnan(obs_tracerdata_in_row)).flatten()
            _errordata_isnan = np.isnan(obs_tracerdata_errs_in_row)
            if all(b == True for b in _errordata_isnan) == True:
                nan_indices_in_data = nan_indices_in_tracerdata
                obs_tracerdata_errs_in_row = np.full(len(_errordata_isnan), None)
            else:
                nan_indices_in_errordata = np.argwhere(_errordata_isnan).flatten()
                nan_indices_in_data = np.union1d(nan_indices_in_tracerdata, nan_indices_in_errordata)
            # final mask removing nan-values from tracerdata values/errs/units arrays
            obs_tracerdata_in_row = [obs_tracerdata_in_row[i] for i in range(len(obs_tracerdata_in_row)) if i not in nan_indices_in_data]
            obs_tracerdata_errs_in_row = [obs_tracerdata_errs_in_row[i] for i in range(len(obs_tracerdata_errs_in_row)) if i not in nan_indices_in_data]
            obs_tracerdata_units_in_row = [obs_tracerdata_units_in_row[i] for i in range(len(obs_tracerdata_units_in_row)) if i not in nan_indices_in_data]
            valid_tracers_used = [tracers_used[i] for i in range(len(tracers_used)) if i not in nan_indices_in_data]
                
            #mzer = Minimizer(objfunc, all_params, fcn_args=(valid_tracers_used, obs_tracerdata_in_row, obs_tracerdata_errs_in_row, obs_tracerdata_units_in_row))
            #M = mzer.leastsq(Dfun=jacfunc, col_deriv=0, factor=0.001)
            #M = mzer.least_squares(jac=jacfunc) # APPEARS NOT TO WORK
            M = minimize(objfunc, all_params, args=(valid_tracers_used, obs_tracerdata_in_row, obs_tracerdata_errs_in_row, obs_tracerdata_units_in_row), method='leastsq', nan_policy='omit', Dfun=jacfunc)
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
        # match indices of output_dataframe to the input DataFrame
        output_dataframe.index = data.index
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
    data_indices = data.index.tolist()

    # parse observations
    # regex pattern for tracers in column headings
    pattern = r'(?:\b|_)(' + '|'.join(obs_labels) + r')(?=\b|_)'

    # filter columns that match the pattern, case insensitive
    selected_columns = [dh for dh in data_headers if re.search(pattern, dh, re.IGNORECASE)]
    selco_patterns = [re.search(pattern, dh, re.IGNORECASE)[0] for dh in data_headers if re.search(pattern, dh, re.IGNORECASE)]

    # parse errors and units
    # define the regex patterns for errors and units on observations
    error_pattern = r'(?:\b|_)(err|errs|error|errors|uncertainty|uncertainties|sigma|sigmas|err\.|err\.s)(?=\b|_)'
    unit_pattern = r'(?:\b|_)(unit|units|dim|dims|dimension|dimensions|dim\.|dim\.s)(?=\b|_)'

    obs_col_names = []
    err_col_names = []  
    unit_col_names = []
    base_tracer_names = []

    to_skip = []
    for i in range(len(selected_columns)):
        col = selected_columns[i]
        # if the column heading does not correspond to an error or unit error pattern, assume it is the concentration
        if not re.search(error_pattern, col, re.IGNORECASE) and not re.search(error_pattern, col, re.IGNORECASE) and i not in to_skip:
            base_tracer = selco_patterns[i]
            base_tracer_names.append(base_tracer)
            obs_col_names.append(col)
            # check for corresponding errors and units in the columns
            err_found, unit_found = False, False
            for _col in selected_columns:
                if base_tracer in _col and re.search(error_pattern, _col, re.IGNORECASE):
                    err_col_names.append(_col)
                    err_found = True
                    break
            for _col in selected_columns:
                if base_tracer in _col and re.search(unit_pattern, _col, re.IGNORECASE):
                    unit_col_names.append(_col)
                    unit_found = True
                    break
            # make sure we don't overcount occurences if the user put in two versions (e.g. He (cc/g) and He (mol/L))
            for j in range(len(selected_columns)):
                if base_tracer in selected_columns[j]:
                    to_skip.append(j)
        
            # TODO add None-append if an error or unit is not found
            if not err_found:
                err_col_names.append(None)
            if not unit_found:
                unit_col_names.append(None)

    obs_out = {}
    errs_out = {}
    units_out = {}
    # construct observations and errors DataFrames to output
    for ocn, ecn, ucn, btn in zip(obs_col_names, err_col_names, unit_col_names, base_tracer_names):
        # if the observations contain unit data, extract only the nominal values
        obs_out[btn] = np.array([_snv(data[ocn][r]) for r in data_indices])
        # if the errors were given in a separate column, just take these values
        if ecn is not None:
            errs_out[btn] = data[ecn]
        # if they weren't, try to extract them from the observations columns, and pad with None if necessary
        else:
            errs_out[btn] = np.array([_ssd(data[ocn][r]) for r in data_indices])
        # if the units were given in a separate column, just take these values
        if ucn is not None:
            units_out[btn] = data[ucn]
        # if they weren't, try to extract them from the observations columns, and pad with None if necessary
        else:
            units_out[btn] = np.array([_sgu(data[ocn][r]) for r in data_indices])
    obs_out = pd.DataFrame(obs_out)
    errs_out = pd.DataFrame(errs_out)
    units_out = pd.DataFrame(units_out)
    # make sure indices of obs/errs/units dataframes start at zero
    obs_out = obs_out.reset_index()
    errs_out = errs_out.reset_index()
    units_out = units_out.reset_index()
    # output the DataFrames
    return obs_out, errs_out, units_out