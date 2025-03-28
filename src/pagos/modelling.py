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
import warnings

from pagos.core import u as _u, Q as _Q, snv as _snv, sto as _sto
from pagos.core import _possibly_iterable, _set_possit, _set_wp


class GasExchangeModel:
    """
    Object that holds a function representing a gas exchange model and its methods, including
    fitting to data and forward-modelling given an input.
    """
    def __init__(self, model_function:Callable, default_units_in:list[str], default_units_out:str, jacobian:Callable=None, jacobian_units:list[str]=None):
        """
        :param model_function: function represented in the GasExchangeModel object.
        :type model_function: Callable
        :param default_units_in: strings specifying the units of the input arguments to `model_function` that will be **assumed** if none are given.
        Must be in the same order as the arguments to `model_function`.
        :type default_units_in: list[str]
        :param default_units_out: single string specifying which units to **convert** the output of `model_function` to.
        Note that conversion happens **after** calculation.
        :type default_units_out: str
        :param jacobian: function returning a numpy array of derivatives of `model_function` with respect to its parameters, i.e. a jacobian matrix.
        Defaults to None.
        :type jacobian: Callable, optional
        :param jacobian_units: strings specifying which units to **convert** the output of the `jacobian` to.
        Note that this has **no effect** on the `fit` method.
        Defaults to None
        :type jacobian_units: list[str], optional
        """
        # force default units into list:
        if default_units_in == None or type(default_units_in) == str:
            default_units_in = [default_units_in]
        else:
            default_units_in = list(default_units_in)
        # set instance variables
        # if default_units_in argument did not include None at the start for the gas parameter, add this in here
        self._model_function_in = model_function
        self.default_units_in = self._check_units_list_against_sig(model_function, default_units_in)
        self.default_units_out = default_units_out
        self.model_arguments = inspect.getfullargspec(self._model_function_in).args
        self.default_units_in_dict = {key:val for key, val in zip(self.model_arguments, self.default_units_in)}

        self._jacobian_in = jacobian
        self.jacobian_units = jacobian_units

        # the function and jacobian that will run if the user does not specify units_in or units_out when calling run() and runjac()
        self.model_function = _possibly_iterable(_u.wraps(self.default_units_out, self.default_units_in, strict=False)(self._model_function_in))
        self.model_func_sig = signature(self.model_function)
        # fast versions that are called in fit()
        self.model_function_fast = _possibly_iterable(self._model_function_in)
        self.model_func_fast_sig = signature(self.model_function_fast)

        if self._jacobian_in is None:
            self.runjac = None
        else:
            # case: no output units are provided for the Jacobian - defaults to model function units divided by parameter units
            if self.jacobian_units is None:
                                                                                                 # Jacobian units set according to:
                self.jacobian_units = [default_units_out if dui in ('', 'dimensionless', None)   # Uᴶᵢ = Uᴼᵁᵀ                if Uᴵᴺ do not have dimensions
                                       else default_units_out + '/(' + dui + ')'                 # Uᴶᵢ = Uᴼᵁᵀ / Uᴵᴺᵢ         if Uᴵᴺ have dimensions
                                       for dui in default_units_in]                              #     where Uᴶᵢ = units of Jacobian row i, Uᴼᵁᵀ = default units out, Uᴵᴺᵢ = iᵗʰ default unit in 
                                        #NOTE this^ used to be tuple() but this screwed up possibly_iterable... should the units all have to be lists?                  
                self.model_jacobian = _possibly_iterable(_u.wraps(self.jacobian_units, self.default_units_in, strict=False)(self._jacobian_in))
                self.model_jac_sig = signature(self.model_jacobian)
            # case: user-defined Jacobian output units are given
            elif all(ju is None or (_u.Unit(dui) * _u.Unit(ju)).is_compatible_with(_u.Unit(default_units_out))
                     for dui, ju in zip(default_units_in, jacobian_units)):
                self.model_jacobian = _possibly_iterable(_u.wraps(self.jacobian_units, self.default_units_in, strict=False)(self._jacobian_in))
                self.model_jac_sig = signature(self.model_jacobian)
            else:
                raise ValueError('Jacobian output units are incommensurable with the model function input and output units.\nShould follow dim[jacobian_i] = dim[output] / dim[input_i].')
            self.model_jacobian_fast = _possibly_iterable(self._jacobian_in)
            self.model_jac_fast_sig = signature(self.model_jacobian_fast)


    def run(self, *args_to_model_func, units_in='default', units_out='default', **kwargs_to_model_func):
        """Run the model function.

        :param units_in: Units of the parameters going into the model, defaults to 'default'
        :type units_in: str, optional
        :param units_out: Units returned by the model, defaults to 'default'
        :type units_out: str, optional
        :return: Result of model function run with the given parameters
        """
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

        # TODO is wraps functionality lost here by passing in quantities?       
        result = self.model_function(*args_to_model_func, disablenext=True, **kwargs_to_model_func)
        _set_possit(True)
        if units_out != 'default':
            result = _sto(result, units_out, strict=False)
        return result
    

    def runjac(self, *args_to_jac_func, units_in='default', units_out='default', **kwargs_to_jac_func):
        """Run the model Jacobian.

        :param units_in: Units of the parameters going into the Jacobian, defaults to 'default'
        :type units_in: str, optional
        :param units_out: Units returned by the Jacobian, defaults to 'default'
        :type units_out: str, optional
        :return: Result of model Jacobian run with the given parameters
        """
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
        

        result = self.model_jacobian(*args_to_jac_func, disablenext=True, **kwargs_to_jac_func)#list(self.model_jacobian(*args_to_jac_func, **kwargs_to_jac_func)) # TODO have to wrap this in list(), I think due to pint wraps() handling arrays... could this lead to performance slowdown via redundant casting?
        _set_possit(True)
        if units_out != 'default':
            result = _sto(result, units_out, strict=False, possit=(0, 1))   #possit keyword makes _sto iterate over result and units_out simultaneously, see core.py > _possibly_iterable
        return result
    
        
    def run_fast(self, *args_to_model_func, **kwargs_to_model_func):
        _set_wp(False)  # TODO should this be outside the run function and instead in an enclosing fit scope?
        result = self.model_function_fast(*args_to_model_func, disablenext=True, **kwargs_to_model_func)    # TODO should this be the unwrapped version without possibly_iterable?
        _set_possit(True)
        _set_wp(True)
        return result
    
    
    def runjac_fast(self, *args_to_jac_func, **kwargs_to_jac_func):
        _set_wp(False) # TODO should this be outside the run function and instead in an enclosing fit scope?
        result = self.model_jacobian_fast(*args_to_jac_func, disablenext=True, **kwargs_to_jac_func)
        _set_possit(True)
        _set_wp(True)
        return result
    

    @staticmethod
    def _check_units_list_against_sig(func, units):
        if len(units) == len(signature(func).parameters) - 1:
            return [None] + units
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
        
    
    def fit(self, data:pd.DataFrame, to_fit:Iterable[str], init_guess:Iterable[float]|Iterable[str]|Iterable[Iterable[float]], tracers_used:Iterable[str], constraints:dict=None, tqdm_bar:bool=False) -> pd.DataFrame:
        """Fit the parameters of a `GasExchangeModel` using a `DataFrame` of hydrological observations.

        :param data: Hydrological data.
        :type data: pd.DataFrame
        :param to_fit: List of parameters to be fitted, corresponding to arguments of the function of the `model_function`/`run`.
        :type to_fit: Iterable[str]
        :param init_guess: List of initial guesses for the fitted parameters in `to_fit`. Can be 2D (n_initguesses x n_data), specifying a set of IGs for each sample in `data`, or a list of strings corresponding to columns in `data` to use as sets of IGs.
        :type init_guess: Iterable[float] | Iterable[str] | Iterable[Iterable[float]]
        :param tracers_used: List of tracers used to fit each set of parameters.
        :type tracers_used: Iterable[str]
        :param custom_labels: Dictionary describing the correspondences of the column headings of `data` to the tracer strings in `tracers_used`, in format `{heading1:tracer1, heading2:tracer2, ...}`, defaults to None.
        :type custom_labels: dict, optional
        :param constraints: Dictionary of bounds on the fitted parameters, in format `{param1:(min1, max1), param2:(min2, max2), ...}`, defaults to None.
        :type constraints: dict, optional
        :return: `DataFrame` of the hydrological data and the corresponding fitted parameters.
        :rtype: pd.DataFrame
        """
        # input to objective function: all parameters (fitted and set), tracers to calculate, observed data and their errors, parameter and tracer units
        def objfunc(parameters, tracers, observed_data, observed_errors):
            # separation of parameter names and values
            parameter_names = list(parameters.valuesdict().keys())
            parameter_values = list(parameters.valuesdict().values())
            paramsdict = {parameter_names[i]:parameter_values[i] for i in range(len(parameter_names))}
            
            modelled_data = self.run_fast(tracers, **paramsdict)

            # if there is an error associated with every observation, weight by the errors
            if all(e is not None for e in observed_errors):
                return (modelled_data - observed_data) / observed_errors
            else:
                return modelled_data - observed_data
        

        def jacfunc(parameters, tracers, observed_data, observed_errors):
            # separation of parameter names and values
            parameter_names = list(parameters.valuesdict().keys())
            parameter_values = list(parameters.valuesdict().values())
            paramsdict = {parameter_names[i]:parameter_values[i] for i in range(len(parameter_names))}

            modelled_jac = self.runjac_fast(tracers, **paramsdict)

            # Jacobian term selection (different Jacobian depending on which parameters are to be fitted)
            # e.g. if only parameters T, S of a model C(T, S, p, A) are to be fitted, Jacobian should be [dC/dT, dC/dS] without p and A derivatives
            jindx = [i for i, p in enumerate(list(self.model_jac_sig.parameters)[1:]) if p in to_fit] # TODO can this be moved outside of jacfunc?

            ntracers = len(tracers)
            if modelled_jac.shape[1] != ntracers:   #TODO: verify that either that modelled_jac will ALWAYS be np.ndarray or change to accommodate other iterables
                raise ValueError('The columns of the jacobian have length %s. All columns must have length %s' % (modelled_jac.shape[1], ntracers))
            jac_cut_to_fit = modelled_jac[:, jindx]

            for i in range(len(jindx)):
                jac_cut_to_fit[:, i] = jac_cut_to_fit[:, i] / observed_errors
            
            return jac_cut_to_fit
    
        data_is_df = isinstance(data, pd.DataFrame)
        model_arg_names = self.model_arguments

        # convert tracers_used to list
        if type(tracers_used) == np.ndarray:
            tracers_used = tracers_used.tolist()

        # get list of model parameters set by observation
        dont_fit_these_args = [a for a in model_arg_names if a not in to_fit and a != 'gas']    # TODO is != 'gas' the most robust way?
        
        # get list of fitted parameter units
        def_fit_param_units = [self.default_units_in_dict[p] for p in to_fit]   # ordered in the same way as to_fit
        
        # prevent jacobian from entering minimize() function if none was provided
        if self.runjac is None:
            jacfunc = None

        # convert input to numpy arrays
        tracers_used, dont_fit_these_args, to_fit = np.array(tracers_used), np.array(dont_fit_these_args), np.array(to_fit)

        if data_is_df:
            # fit procedure if the data is a DataFrame
            obs_tracers, obs_tr_errs, obs_tr_units, obs_params = _prepare_data(data, tracers_used, dont_fit_these_args, self.default_units_out)

            # perform fit for each row
            ret = pd.DataFrame(columns=to_fit, index=np.arange(len(obs_tracers)))
            # show loading bar if desired
            if tqdm_bar:
                ran = tqdm(range(len(obs_tracers)))
            else:
                ran = range(len(obs_tracers))
            for i in ran:
                vi, ei, ui, opi = obs_tracers[i], obs_tr_errs[i], obs_tr_units[i], obs_params[i]

                fitted_params = _perform_single_fit(objfunc, vi, ei, ui, opi, tracers_used, dont_fit_these_args, to_fit, init_guess, constraints, def_fit_param_units, self.default_units_out, jacfunc)
                for j, tf in enumerate(to_fit):
                    ret.loc[i][tf] = _Q(fitted_params[tf].value, def_fit_param_units[j], fitted_params[tf].stderr)        
        else:
            # fit procedure if the data is a single tuple
            obs_tracers, obs_tr_errs, obs_tr_units, obs_params = data

            # allow for just single values to have been input for errors and units
            if not hasattr(obs_tr_errs, '__len__'): # <- checks if a single value was given for the error
                obs_tr_errs = np.full(len(obs_tracers), obs_tr_errs)
            if isinstance(obs_tr_units, str):       # <- checks if a single string was given for the unit
                obs_tr_units = np.full(len(obs_tracers), obs_tr_units)

            # force input into numpy arrays
            obs_tracers, obs_tr_errs, obs_tr_units, obs_params = np.array(obs_tracers), np.array(obs_tr_errs), np.array(obs_tr_units), np.array(obs_params)

            fitted_params = _perform_single_fit(objfunc, obs_tracers, obs_tr_errs, obs_tr_units, obs_params, tracers_used, dont_fit_these_args, to_fit, init_guess, constraints, def_fit_param_units, self.default_units_out, jacfunc)
            ret = []
            for j, tf in enumerate(to_fit):
                ret.append(_Q(fitted_params[tf].value, def_fit_param_units[j], fitted_params[tf].stderr))
        
        return ret


def _prepare_data(data:pd.DataFrame, tracers, obs_params, default_units_out):
    headers = data.columns.to_list()

    # finding the instances of the tracer names in headers
    
    obs_foreach_tracer = []
    errs_foreach_tracer = []
    units_foreach_tracer = []
    obs_foreach_parameter = []
    for tracername in tracers:
        # find the occurrences of the tracer name
        tracerpattern = rf'(\s|^)({re.escape(tracername)})(\s|$)'
        where_tracername = [index for index, item in enumerate(headers) if re.search(tracerpattern, item)]

        # find the occurrences of an error indicator
        errorpattern = r'(\s|^)(err|errs|error|errors|uncertainty|uncertainties|sigma|sigmas|err\.|err\.s|Err|Errs|Error|Errors|Uncertainty|Uncertainties|Sigma|Sigmas|Err\.|Err\.s)(\s|$)'
        where_error = [index for index, item in enumerate(headers) if re.search(tracerpattern, item) and re.search(errorpattern, item)]
        if len(where_error) == 0:
            tracer_err_index = None
            warnings.warn('No columns found for the error on %s, setting all such errors to nan.' % (tracername), stacklevel=4)
        else:
            tracer_err_index = where_error[0]
            if len(where_error) > 1:
                warnings.warn('Multiple columns found for the error on %s, taking \'%s\'.' % (tracername, headers[tracer_err_index]), stacklevel=4)
        
        # find the occurrences of a unit indicator
        unitpattern = r'(?:\b|_)(unit|units|dim|dims|dimension|dimensions|dim\.|dim\.s|Unit|Units|Dim|Dims|Dimension|Dimensions|Dim\.|Dim\.s)(?=\b|_)'
        where_unit = [index for index, item in enumerate(headers) if re.search(tracerpattern, item) and re.search(unitpattern, item)]
        if len(where_unit) == 0:
            tracer_unit_index = None
            warnings.warn('No columns found for the unit of %s, assuming the default units of the function return (%s).' % (tracername, default_units_out), stacklevel=4)
        else:
            tracer_unit_index = where_unit[0]
            if len(where_unit) > 1:
                warnings.warn('Multiple columns found for the unit of %s, taking \'%s\'.' % (tracername, headers[tracer_unit_index]), stacklevel=4)

        # remove the error and unit indices from the tracer indices so we are (hopefully) left with only the index of the tracer amount
        where_tracername = np.setdiff1d(np.setdiff1d(where_tracername, where_error), where_unit)
        if len(where_tracername) == 0:
            raise KeyError('No column was found for the tracer %s.' % (tracername))
        else:
            tracername_index = where_tracername[0]
            if len(where_tracername) > 1:
                warnings.warn('Multiple columns found for the tracer %s, taking \'%s\'.' % (tracername, headers[tracername_index]), stacklevel=4)
        
        # append the tracer data, errors and units to the external arrays
        obs_foreach_tracer.append(data[headers[tracername_index]].to_numpy())
        if tracer_err_index is not None:
            errs_foreach_tracer.append(data[headers[tracer_err_index]].to_numpy())
        else:
            errs_foreach_tracer.append(np.full(len(data), np.nan, dtype='float64'))
        if tracer_unit_index is not None:
            units_foreach_tracer.append(data[headers[tracer_unit_index]].to_numpy())
        else:
            units_foreach_tracer.append(np.full(len(data), default_units_out, dtype=object))
    
    for opname in obs_params:
        # find the occurrences of the parameter name
        oppattern = rf'(\s|^)({re.escape(opname)})(\s|$)'
        where_opname = [index for index, item in enumerate(headers) if re.search(oppattern, item)]
        if len(where_opname) == 0:
            raise KeyError('No column was found for the parameter %s, which should be set by observation.' % (opname))
        else:
            opname_index = where_opname[0]
            if len(where_opname) > 1:
                warnings.warn('Multiple columns found for the parameter %s, taking \'%s\'.' % (opname, headers[opname_index]), stacklevel=4)
        obs_foreach_parameter.append(data[headers[opname_index]].to_numpy())

    return np.vstack(obs_foreach_tracer).transpose(),\
           np.vstack(errs_foreach_tracer).transpose(),\
           np.vstack(units_foreach_tracer).transpose(),\
           np.vstack(obs_foreach_parameter).transpose()


def _perform_single_fit(objfunc, obs, errs, units, obs_params_values, tracers, obs_params, fit_params, init_guess, bounds, default_fitparam_units, default_units_out, jacfunc):
    # setup tracer data
    # remove nan-values and discard corresponding tracers
    wherevalidobs = np.nonzero(~np.isnan(obs))[0]   # gets the indices of where obs are not nan
    tracers_tomin = tracers[wherevalidobs]          # removes tracers where obs are nan
    obs_tomin = obs[wherevalidobs]                  # "       obs     "     "   "   "
    errs_tomin = errs[wherevalidobs]                # "       errs    "     "   "   "
    units_used = units[wherevalidobs]

    # make units the same as the default units out
    for i in range(len(tracers_tomin)):
        obs_tomin[i] = _sto(_Q(obs_tomin[i], units_used[i]), default_units_out).magnitude
        errs_tomin[i] = _sto(_Q(errs_tomin[i], units_used[i]), default_units_out).magnitude
    
    # setup parameters set by observation
    all_params = Parameters()
    # add_many tuple order: (NAME VALUE VARY MIN  MAX  EXPR  BRUTE_STEP)
    all_params.add_many(*[(obs_params[i], obs_params_values[i], False) for i in range(len(obs_params))])

    # setup parameters to be fitted
    # set bounds to infinite none are given
    if bounds is None:
        bounds = [(-np.inf, np.inf) for i in range(len(fit_params))]
    # make units of the initial guess and bounds the same as the default units in
    for i in range(len(fit_params)):
        # convert bounds to list so that items may be assigned
        bounds[i] = list(bounds[i])
        init_guess[i] = _snv(_sto(init_guess[i], default_fitparam_units[i], strict=False))
        bounds[i][0] = _snv(_sto(bounds[i][0], default_fitparam_units[i], strict=False))
        bounds[i][1] = _snv(_sto(bounds[i][1], default_fitparam_units[i], strict=False))
        all_params.add(fit_params[i], init_guess[i], True, bounds[i][0], bounds[i][1])
    
    # perform minimisation and return
    M = minimize(objfunc, all_params, args=(tracers_tomin, obs_tomin, errs_tomin), method='leastsq', nan_policy='omit', Dfun=jacfunc)
    return M.params

