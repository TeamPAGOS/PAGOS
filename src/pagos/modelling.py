from __future__ import annotations

import re
from collections.abc import Callable, Iterable
from copy import deepcopy
from functools import reduce
from inspect import getfullargspec, signature
from numbers import Number

import numpy as np
import pandas as pd
from lmfit import Parameters, fit_report, minimize
from matplotlib import pyplot as plt
from tqdm import tqdm

from pagos.core import (
    PAGOSQuantity,
    begin_new_mc_cycle,
    end_mc_cycle,
    end_of_first_mc_cycle_pass,
    is_first_mc_pass,
    is_mc_enabled,
    pQ,
    set_mc,
    unit_aware,
)

rng = np.random.default_rng()


class FitDataFrameResult:
    def __init__(
        self,
        index: pd.Index,
        regressors_to_fit: list | dict,
        n_mc_draws: int,
        logslist: list[dict] | None = None,
    ):
        """Holds results of TracerModel.fit_dataframe, when a Monte Carlo procedure has been performed.

        Args:
            index (Index): `Index` of each `DataFrame` corresponding to one MC draw
            regressors_to_fit (list | dict): Fit parameters
            n_mc_draws (int): Number of MC draws
            logslist: List of logs for the MC draws
        """
        self.regressors_to_fit = regressors_to_fit

        # create empty results frames
        if n_mc_draws:
            self.came_from_mc_procedure = True
            self.mc_frames: list[pd.DataFrame] = [
                pd.DataFrame(
                    index=index,
                    columns=(
                        regressors_to_fit
                        if isinstance(regressors_to_fit, list)
                        else regressors_to_fit.keys()
                    ),
                    dtype=np.float64,
                )
                for k in range(n_mc_draws)
            ]
        else:
            self.came_from_mc_procedure = False
            # create only one frame if MC procedure was not performed
            self.mc_frames: list[pd.DataFrame] = [
                pd.DataFrame(
                    index=index,
                    columns=(
                        [
                            name
                            for regressor in regressors_to_fit
                            for name in (regressor, f"{regressor} err")
                        ]
                    ),
                    dtype=np.float64,
                )
            ]

        self.logslist = logslist

    def set_results(self, result, j: int, k: int):
        self.mc_frames[k].iloc[j] = result

    def get_results(self, param: str | tuple[str] | None = None):
        """Get the results of a parameter or many parameters after an MC-fitting procedure.

        Args:
            param (str | tuple[str]): The parameter(s) to obtain.

        Returns:
            NDArray | dict[str, NDArray]: (`n` x `m`) array, where `n` is the number of samples that were fitted, and `m` the number of MC draws.
        """

        def _return(p):
            if len(self.mc_frames) == 1:
                return np.array([self.mc_frames[0][p].to_numpy()]).transpose().flatten()
            else:
                return np.array(
                    [mc_frame[p].to_numpy() for mc_frame in self.mc_frames]
                ).transpose()

        if param is None:
            # return all fitted parameters if param argument is not given
            return {p: _return(p) for p in self.regressors_to_fit}
        elif isinstance(param, str):
            return _return(param)
        else:
            return {p: _return(p) for p in param}

    def get_logs(self) -> list[dict] | None:
        if self.logslist:
            if len(self.logslist) == 1:
                return self.logslist[0]
            else:
                return self.logslist
        else:
            print("INFO: No logging was performed for this fit")
            return

    def plot_results(self):
        if self.came_from_mc_procedure:
            results = self.get_results()
            fig, ax = plt.subplots(
                n_samples := len(list(results.values())[0]),  # noqa: RUF015
                len(self.regressors_to_fit),
            )
            for i, p in enumerate(self.regressors_to_fit):
                for j in range(n_samples):
                    ax[j, i].hist(results[p][j])
                ax[0, i].set_title(p)
            fig.tight_layout()
            plt.show()
        else:
            raise NotImplementedError()


class TracerModel:
    def __init__(
        self,
        model_function: Callable,
        default_units_in: dict | None = None,
        default_units_out: str | None = None,
        # jacobian: Callable = None,        TODO later?
        # jacobian_units: list[str] = None  TODO later?
    ):
        """Object that holds a function representing a tracer model and its methods,
        including fitting to data and forward modelling given an input.

        Args:
            model_function (Callable): function representing the model
            default_units_in (dict | None): units of the input arguments to `model_function` to be **assumed** if none are explicitly given.
                Must be in the same order as the arguments to `model_function`.
                If `None`, then tries to proceed assuming that `model_function` is already wrapped with `unit_aware`.
            default_units_out (str): the units which the output of `model_function` should be **converted to**

        Raises:
            TypeError: if default_units_in is not a dictionary or None
            ValueError: if default_units_in does not have one entry for every argument to model_function (except the tracer)
        """

        # check type of default_units_in
        if not isinstance(default_units_in, (dict)) and default_units_in is not None:
            raise TypeError("default_units_in must be a dictionary or None")

        # set instance variables

        # list of parameters in the model function's signature
        self.modelfunc_params = list(signature(model_function).parameters)

        if default_units_in is not None:
            # if default_units_in argument did not include None
            # at the start for the tracer parameter, add this in here
            if len(default_units_in) == len(self.modelfunc_params) - 1:
                self.default_units_in = {
                    self.modelfunc_params[0]: None
                } | default_units_in
            elif len(default_units_in) == len(self.modelfunc_params):
                self.default_units_in = default_units_in
            else:
                raise ValueError(
                    "default_units_in should have one entry for every argument to model_function (except the tracer)."
                )
        else:
            try:
                self.default_units_in = model_function.default_units_in
            except AttributeError:
                self.default_units_in = None

        if default_units_out is None:
            try:
                self.default_units_out = model_function.units_out
            except AttributeError:
                self.default_units_out = None
        else:
            self.default_units_out = default_units_out

        self.model_function = unit_aware(self.default_units_in, self.default_units_out)(
            model_function
        )

        # initialisation of objective function which will be used for fitting
        def objfunc(
            regressors: Parameters,
            tracers: list,
            obs_tr: np.ndarray,
            obs_tr_errs: np.ndarray,
            logs: dict | None = None,
        ):
            """This is the objective function that will be minimised by
            lmfit.minimize. It is the residual of observed and modelled data.

            Args:
                regressors (Parameters): `Parameters` object holding all fixed and variable regressors to be passed to `minimize` (all non-tracer variables of the model)
                tracers (list): the tracers that will be used (e.g. `['He', 'Ne', 'Ar']`)
                obs_tr (np.ndarray): observed tracer values, in the order of the `tracers` list, stripped of units
                obs_tr_errs (np.ndarray): observed tracer errors, in the order of the `tracers` list, stripped of units
                logging (bool): whether or not to log results of the calculation
            """

            # unpack parameters
            regr_dict = regressors.valuesdict()

            mod_tr = np.array(
                [self.model_function(tr, **regr_dict).value for tr in tracers]
            )
            if obs_tr_errs is not None:
                norm_resid = (mod_tr - obs_tr) / obs_tr_errs
            else:
                norm_resid = mod_tr - obs_tr

            if is_first_mc_pass():
                # at the end of the first call of the objective function,
                # we convert the stored list of MC factors into a cycle
                # and activate fast calculations
                end_of_first_mc_cycle_pass()

            if logs:
                for i, t in enumerate(tracers):
                    logs[t].append(obs_tr[i])
                for r in regr_dict:
                    logs[r].append(regr_dict[r])
                logs["chi2"].append(np.sum(norm_resid**2))

            # returns an array of residuals. minimize() will automatically square and sum the elements of the array for the LM algorithm
            return norm_resid

        self.objfunc = objfunc

    def run(
        self,
        *args_to_model_func: Iterable,
        units_in: Iterable[str] = "default",
        units_out: str = "default",
        **kwargs_to_model_func: dict,
    ) -> PAGOSQuantity:
        """Run the model function.

        :param *args_to_model_func: Arguments to be passed into the model function
        :type *args_to_model_func: Iterable
        :param units_in: Units of the parameters going into the model, defaults to 'default'
        :type units_in: Iterable[str], optional
        :param units_out: Units returned by the model, defaults to 'default'
        :type units_out: str, optional
        :param **kwargs_to_model_func: Keyword arguments to be passed into the model function
        :type **kwargs_to_model_func: dict
        :return: Result of model function run with the given parameters
        :rtype: PAGOSQuantity
        """

        # prescribe units if units_out or units_in differ from defaults
        # if units_in argument did not include None
        # at the start for the tracer parameter, add this in here
        if units_in == "default":
            units_in = self.default_units_in
        elif len(units_in) == len(self.modelfunc_params) - 1:
            units_in = {self.modelfunc_params[0]: None} | units_in
        elif len(units_in) == len(self.modelfunc_params):
            pass
        else:
            raise ValueError(
                'units_in should either be "default" or an array with one entry per argument to the model function (except the tracer).'
            )

        # force to list
        args_to_model_func = list(args_to_model_func)

        if units_in is not None:
            # convert all arguments passed in to PAGOSQuantity objects
            for i, (argname, val) in enumerate(
                zip(self.modelfunc_params[1:], args_to_model_func[1:]), start=1
            ):
                # we skip the first element of args_to_model_func, as this must be the tracer,
                # which has no units
                if isinstance(val, Number):
                    args_to_model_func[i] = pQ(val, units_in[argname])
            # the keyword arguments, if they have units, will take units
            for k in kwargs_to_model_func:  # noqa: PLC0206
                if isinstance(kwargs_to_model_func[k], Number):
                    kwargs_to_model_func[k] = pQ(kwargs_to_model_func[k], units_in[k])

        result = self.model_function(*args_to_model_func, **kwargs_to_model_func)

        if units_out != "default":
            return result.to(units_out)
        else:
            return result

    def _fit(
        self,
        regr_params_object: Parameters,
        tracers: list,
        obs_tr: np.ndarray,
        obs_tr_errs: np.ndarray | None,
        logs: dict | None = None,
    ):
        # fit objective function to provided data
        fit_result = minimize(
            self.objfunc,
            regr_params_object,
            args=(tracers, obs_tr, obs_tr_errs, logs),
        )
        return fit_result

    def fit(
        self,
        fixed_regressors: dict,
        regressors_to_fit: dict,
        tracers: list,
        obs_tr: np.ndarray,
        obs_tr_errs: np.ndarray | None,
        regr_to_fit_bounds: dict | None = None,
        logs: dict | None = None,
        comes_from_fit_df: bool = False,
    ):
        if not comes_from_fit_df:
            # Perform pre-conversion of inputs' units to self.default_units_in and always
            # take the value. This is because self.objfunc will expect non-unit-laden inputs
            # that are nevertheless valued as if with units of self.default_units_in.
            # This is unnecessary if the data came from the method fit_dataframe, hence the
            # if statement
            fixed_regressors = {
                k: pQ(fixed_regressors[k], self.default_units_in[k]).value
                if isinstance(fixed_regressors[k], (PAGOSQuantity, Number))
                else fixed_regressors[k]
                for k in fixed_regressors
            }
            regressors_to_fit = {
                k: pQ(regressors_to_fit[k], self.default_units_in[k]).value
                for k in regressors_to_fit
            }

        # turn regressors dictionary into Parameters object (passed into minimize())
        regr_params_object = Parameters()
        for k in fixed_regressors:
            # add fixed regressor to Parameters object
            regr_params_object.add(k, fixed_regressors[k], vary=False)
        for k in regressors_to_fit:
            # apply bounds to fitted parameters if they are present
            if regr_to_fit_bounds:
                try:
                    _min, _max = regr_to_fit_bounds[k]
                except KeyError:
                    _min, _max = (-np.inf, np.inf)
            else:
                _min, _max = (-np.inf, np.inf)
            # add variable regressor to Parameters object
            regr_params_object.add(
                k, regressors_to_fit[k], vary=True, min=_min, max=_max
            )

        # begin a new Monte Carlo cycle - all calls to the objective function should repeat the same MC variations
        # otherwise the objective function can never be minimised!
        begin_new_mc_cycle()

        fitted = self._fit(
            regr_params_object,
            tracers,
            obs_tr,
            obs_tr_errs,
            logs,
        )

        end_mc_cycle()

        return fitted

    def fit_dataframe(
        self,
        data: pd.DataFrame,
        tracers: list,
        regressors_to_fit: dict | list,
        regr_to_fit_bounds: dict | None = None,
        do_warnings: bool = True,
        tqdm_bar: bool = True,
        logging: bool = False,
        nmc: int = 0,
    ) -> FitDataFrameResult:

        n_samples = data.shape[0]

        # The observations for each fixed regressor as a dictionary of parameter names and an array of values
        # The tracer observations as a matrix [n_tracers] x [n_samples]
        # The tracer observation errors as a matrix [n_tracers] x [n_samples]
        (
            obs_foreach_fixed_regressor,
            errs_foreach_fixed_regressor,
            tracer_obs_matrix,
            tracer_errs_matrix,
        ) = self.prepare_dataframe_for_fitting(
            data, tracers, regressors_to_fit, do_warnings, bool(nmc)
        )

        # the fixed regressors are the parameters which are not fitted, and are also not the tracer parameter (hence [1:])
        fixed_regressors = [
            p for p in self.modelfunc_params[1:] if p not in regressors_to_fit
        ]

        # convert initial guesses for regressors to fit to default_units_in
        regressors_to_fit = {
            k: pQ(regressors_to_fit[k], self.default_units_in[k]).value
            for k in regressors_to_fit
        }

        # set up logging object if desired
        if logging:
            log_template_for_one_sample = (
                {t: [] for t in tracers}
                | {fr: [] for fr in fixed_regressors}
                | {rtf: [] for rtf in regressors_to_fit}
                | {"chi2": []}
            )

            log_template_for_one_mc_frame = [
                deepcopy(log_template_for_one_sample) for _ in range(n_samples)
            ]

            if nmc:
                logslist = [deepcopy(log_template_for_one_mc_frame) for _ in range(nmc)]
            else:
                logslist = [deepcopy(log_template_for_one_mc_frame)]
        else:
            logslist = None

        # prepare mc variations around the values for the tracers and fixed regressors, if Monte Carlo should be performed
        if nmc:
            set_mc(True)
            # varying each (t x s) tracer-sample pairs, nmc times, to get a cube with (t x s x nmc) entries
            if tracer_errs_matrix is not None:
                tracer_obs_cubematrix = np.tile(
                    tracer_obs_matrix, (nmc, 1, 1)
                ) + rng.normal(
                    loc=np.zeros(tracer_obs_matrix.shape),
                    scale=tracer_errs_matrix,
                    size=(nmc, *tracer_obs_matrix.shape),
                )
            else:
                tracer_obs_cubematrix = np.tile(tracer_obs_matrix, (nmc, 1, 1))
            # doing the same with the fixed regressors (but adhering to dictionary structure)
            fixed_regressor_cubedict = {
                r: obs_foreach_fixed_regressor[r]
                + rng.normal(
                    loc=np.zeros(n_samples),
                    scale=errs_foreach_fixed_regressor[r],
                    size=(nmc, n_samples),
                )
                for r in fixed_regressors
            }

            out_dfs = FitDataFrameResult(
                data.index, regressors_to_fit, nmc, logslist=logslist
            )

            # loading bar, increments on every mc variation of the input parameters
            if tqdm_bar:
                _range_nmc = tqdm(range(nmc))
            else:
                _range_nmc = range(nmc)

            # exception counters
            value_error_exceptions: int = 0
            overflow_error_exceptions: int = 0

            # perform fits for every row in every "slice" of the data cubes
            for k in _range_nmc:
                for j in tqdm(range(n_samples), leave=False):
                    if logging:
                        logs_kj = logslist[k][j]
                    else:
                        logs_kj = None

                    try:
                        fitresult_jk = self.fit(
                            fixed_regressors={
                                r: fixed_regressor_cubedict[r][k, j]
                                for r in fixed_regressors
                            },
                            regressors_to_fit=regressors_to_fit,
                            tracers=tracers,
                            obs_tr=tracer_obs_cubematrix[k, :, j],
                            # normalise by the average of the tracer distributions
                            obs_tr_errs=tracer_obs_matrix[:, j],
                            regr_to_fit_bounds=regr_to_fit_bounds,
                            logs=logs_kj,
                            comes_from_fit_df=True,
                        )
                        params_out_jk = np.array(
                            [fitresult_jk.params[r].value for r in regressors_to_fit]
                        )

                        out_dfs.set_results(params_out_jk, j, k)
                    except ValueError:
                        out_dfs.set_results(
                            np.full(len(regressors_to_fit), np.nan), j, k
                        )
                        value_error_exceptions += 1
                    except OverflowError:
                        out_dfs.set_results(
                            np.full(len(regressors_to_fit), np.nan), j, k
                        )
                        overflow_error_exceptions += 1

            set_mc(False)
            success_rate = (
                100
                - (value_error_exceptions + overflow_error_exceptions)
                / (n_samples * nmc)
                * 100
            )
            print(
                f"Completed fitting DataFrame with {value_error_exceptions} ValueErrors and {overflow_error_exceptions} OverflowErrors ({success_rate:.1f}% success rate)"
            )
            return out_dfs

        # otherwise just fit the data once, if no MC procedure is requested
        else:
            out_df = FitDataFrameResult(
                index=data.index,
                regressors_to_fit=regressors_to_fit,
                n_mc_draws=0,
                logslist=logslist,
            )

            # loading bar, increments on each sample
            if tqdm_bar:
                _range_nsamples = tqdm(range(n_samples))
            else:
                _range_nsamples = range(n_samples)

            # perform fit for every row in the dataframe
            for j in _range_nsamples:
                if logging:
                    logs_j = logslist[0][j]
                else:
                    logs_j = None

                if tracer_errs_matrix is None:
                    _obs_tr_errs = None
                else:
                    _obs_tr_errs = tracer_errs_matrix[:, j]
                fitresult_j = self.fit(
                    fixed_regressors={
                        r: obs_foreach_fixed_regressor[r][j] for r in fixed_regressors
                    },
                    regressors_to_fit=regressors_to_fit,
                    tracers=tracers,
                    obs_tr=tracer_obs_matrix[:, j],
                    obs_tr_errs=_obs_tr_errs,
                    regr_to_fit_bounds=regr_to_fit_bounds,
                    logs=logs_j,
                    comes_from_fit_df=True,
                )
                params_out_j = np.array(
                    [
                        [fitresult_j.params[r].value, fitresult_j.params[r].stderr]
                        for r in regressors_to_fit
                    ]
                ).flatten()

                out_df.set_results(params_out_j, j, 0)

            return out_df

    def prepare_dataframe_for_fitting(
        self,
        data: pd.DataFrame,
        tracers: list,
        regressors_to_fit: dict | list,
        do_warnings: bool = True,
        mc_active: bool = False,
    ):
        """Mostly just parsing the dataframe's columns, kept separate from fit_dataframe for readability"""

        n_samples = data.shape[0]
        n_tracers = len(tracers)

        tracer_obs_matrix = np.empty((n_tracers, n_samples), dtype=np.float64)
        tracer_errs_matrix = np.empty((n_tracers, n_samples), dtype=np.float64)
        tracer_units_matrix = np.empty((n_tracers, n_samples), dtype=object)

        # the fixed regressors are the parameters which are not fitted, and are also not the tracer parameter (hence [1:])
        fixed_regressors = [
            p for p in self.modelfunc_params[1:] if p not in regressors_to_fit
        ]
        obs_foreach_fixed_regressor: dict[str, np.typing.NDArray[np.float64]] = {}
        errs_foreach_fixed_regressor: dict[str, np.typing.NDArray[np.float64]] = {}
        units_foreach_fixed_regressor: dict[str, np.typing.NDArray[np.str_]] = {}
        headers = data.columns.to_list()

        (
            warn_no_tr_errs,
            warn_many_tr_errs,
            warn_no_tr_units,
            warn_many_tr_units,
            warn_no_fr,
            warn_many_fr,
            warn_no_fr_errs,
            warn_many_fr_errs,
            warn_no_fr_units,
            warn_many_fr_units,
        ) = [], [], [], [], [], [], [], [], [], []

        # this loop is in TRACER ORDER, which the tracer observation matrices must also obey!
        for i, tracername in enumerate(tracers):
            # find the occurrences of the tracer name
            tracerpattern = rf"(\s|^)({re.escape(tracername)})(\s|$)"
            where_tracername = [
                index
                for index, item in enumerate(headers)
                if re.search(tracerpattern, item)
            ]

            # find the occurrences of an error indicator
            errorpattern = r"(\s|^)(err|errs|error|errors|uncertainty|uncertainties|sigma|sigmas|err\.|err\.s|Err|Errs|Error|Errors|Uncertainty|Uncertainties|Sigma|Sigmas|Err\.|Err\.s)(\s|$)"
            where_error = [
                index
                for index, item in enumerate(headers)
                if re.search(tracerpattern, item) and re.search(errorpattern, item)
            ]

            if len(where_error) == 0:
                tracer_err_index = None
                if do_warnings:
                    warn_no_tr_errs.append(tracername)
            else:
                tracer_err_index = where_error[0]
                if len(where_error) > 1 and do_warnings:
                    warn_many_tr_errs.append((tracername, headers[tracer_err_index]))

            # find the occurrences of a unit indicator
            unitpattern = r"(?:\b|_)(unit|units|dim|dims|dimension|dimensions|dim\.|dim\.s|Unit|Units|Dim|Dims|Dimension|Dimensions|Dim\.|Dim\.s)(?=\b|_)"
            where_unit = [
                index
                for index, item in enumerate(headers)
                if re.search(tracerpattern, item) and re.search(unitpattern, item)
            ]
            if len(where_unit) == 0:
                tracer_unit_index = None
                if do_warnings:
                    warn_no_tr_units.append(tracername)
            else:
                tracer_unit_index = where_unit[0]
                if len(where_unit) > 1 and do_warnings:
                    warn_many_tr_units.append((tracername, headers[tracer_unit_index]))

            # remove the error and unit indices from the tracer indices so we are (hopefully) left with only the index of the tracer amount
            where_tracername = np.setdiff1d(
                np.setdiff1d(where_tracername, where_error), where_unit
            )
            if len(where_tracername) == 0:
                raise KeyError(f"No column was found for the tracer {tracername}.")
            else:
                tracername_index = where_tracername[0]
                if len(where_tracername) > 1 and do_warnings:
                    warn_many_tr_errs.append((tracername, headers[tracername_index]))

            # fill out tracer observation matrices with observations, errors and units
            tracer_obs_matrix[i] = data[headers[tracername_index]].to_numpy()
            if tracer_err_index is not None:
                tracer_errs_matrix[i] = data[headers[tracer_err_index]].to_numpy()
            else:
                # -1 will be interpreted later as "set to None"
                tracer_errs_matrix[i] = np.full(len(data), -1, dtype="float64")
            if tracer_unit_index is not None:
                tracer_units_matrix[i] = data[headers[tracer_unit_index]].to_numpy()
            else:
                tracer_units_matrix[i] = np.full(
                    len(data), self.default_units_out, dtype=object
                )
        if np.any(tracer_errs_matrix < 0):
            tracer_errs_matrix = None

        for parname in fixed_regressors:
            # find the occurrences of the parameter name
            parpattern = rf"(\s|^)({re.escape(parname)})(\s|$)"
            where_parname = [
                index
                for index, item in enumerate(headers)
                if re.search(parpattern, item)
            ]

            if len(where_parname) == 0:
                warn_no_fr.append(parname)

            # find the occurrences of an error indicator
            errorpattern = r"(\s|^)(err|errs|error|errors|uncertainty|uncertainties|sigma|sigmas|err\.|err\.s|Err|Errs|Error|Errors|Uncertainty|Uncertainties|Sigma|Sigmas|Err\.|Err\.s)(\s|$)"
            where_error = [
                index
                for index, item in enumerate(headers)
                if re.search(parpattern, item) and re.search(errorpattern, item)
            ]
            if len(where_error) == 0:
                par_err_index = None
                if do_warnings:
                    warn_no_fr_errs.append(parname)
            else:
                par_err_index = where_error[0]
                if len(where_error) > 1 and do_warnings:
                    warn_many_fr_errs.append((parname, headers[par_err_index]))

            # find the occurrences of a unit indicator
            unitpattern = r"(?:\b|_)(unit|units|dim|dims|dimension|dimensions|dim\.|dim\.s|Unit|Units|Dim|Dims|Dimension|Dimensions|Dim\.|Dim\.s)(?=\b|_)"
            where_unit = [
                index
                for index, item in enumerate(headers)
                if re.search(parpattern, item) and re.search(unitpattern, item)
            ]
            if len(where_unit) == 0:
                par_unit_index = None
                if do_warnings:
                    warn_no_fr_units.append((parname, self.default_units_in[parname]))
            else:
                par_unit_index = where_unit[0]
                if len(where_unit) > 1 and do_warnings:
                    warn_many_fr_units.append((parname, headers[par_unit_index]))

            # remove the error and unit indices from the parameter name indices so we are (hopefully) left with only the index of the parameter name
            where_parname = np.setdiff1d(
                np.setdiff1d(where_parname, where_error), where_unit
            )
            if len(where_parname) == 0:
                raise KeyError(
                    f"No column was found for the observed parameter {parname}."
                )
            else:
                parname_index = where_parname[0]
                if len(where_parname) > 1 and do_warnings:
                    warn_many_fr.append((parname, headers[parname_index]))

            # append the fixed regressor data, errors and units to the external dictionaries
            obs_foreach_fixed_regressor[parname] = data[
                headers[parname_index]
            ].to_numpy()
            if par_err_index is not None:
                errs_foreach_fixed_regressor[parname] = data[
                    headers[par_err_index]
                ].to_numpy()
            else:
                errs_foreach_fixed_regressor[parname] = np.full(
                    len(data), 0, dtype="float64"
                )
            if par_unit_index is not None:
                units_foreach_fixed_regressor[parname] = data[
                    headers[par_unit_index]
                ].to_numpy()
            else:
                units_foreach_fixed_regressor[parname] = np.full(
                    len(data), self.default_units_in[parname], dtype=object
                )

        # print warnings
        # fmt: off
        def _gen_warnclause(x):
            # only used for generating warning messages
            # returns a string that looks like "a, b, c and d" for x = ['a', 'b', 'c', 'd']
            if len(x) == 1:
                return x[0]
            else:
                return (reduce(lambda result, current: result + ", " + current, x[:-1]) + " and " + x[-1])

        if warn_no_tr_errs: print(f"FIT WARNING: No columns found for the error on {_gen_warnclause(warn_no_tr_errs)}, setting all such errors to zero.")
        if warn_many_tr_errs: print(f"FIT WARNING: Multiple columns found for the error on {_gen_warnclause([w[0] for w in warn_many_tr_errs])}, taking {_gen_warnclause([w[1] for w in warn_many_tr_errs])}.")
        if warn_no_tr_units: print(f"FIT WARNING: No columns found for the unit on {_gen_warnclause(warn_no_tr_units)}, assuming the default units of the function return ({self.default_units_out}).")
        if warn_many_tr_units: print(f"FIT WARNING: Multiple columns found for the unit of {_gen_warnclause([w[0] for w in warn_many_tr_units])}, taking {_gen_warnclause([w[1] for w in warn_many_tr_units])}.")
        if warn_no_fr: print(f"FIT WARNING: No column was found for the parameter {_gen_warnclause(warn_no_fr)}, which should be set by observation.")
        if warn_many_fr: print(f"FIT WARNING: Multiple columns found for the parameter {_gen_warnclause([w[0] for w in warn_many_fr])}, taking {_gen_warnclause([w[1] for w in warn_many_fr])}.")
        if warn_no_fr_units: print(f"FIT WARNING: No columns found for the unit of {_gen_warnclause([w[0] for w in warn_no_fr_units])}, assuming the default units in for the function ({_gen_warnclause([w[1] for w in warn_no_fr_units])}).")
        if warn_many_fr_units: print(f"FIT WARNING: Multiple columns found for the unit of {_gen_warnclause([w[0] for w in warn_many_fr_units])}, taking {_gen_warnclause([w[1] for w in warn_many_fr_units])}.")
        if mc_active:
            if warn_no_fr_errs: print(f"MC WARNING: No columns found for the error on {_gen_warnclause(warn_no_fr_errs)}, setting all such errors to zero.")
            if warn_many_fr_errs: print(f"MC WARNING: Multiple columns found for the error on {_gen_warnclause([w[0] for w in warn_many_fr_errs])}, taking {_gen_warnclause([w[1] for w in warn_many_fr_errs])}.")
        # fmt: on

        # convert all tracer inputs to default_units_out (loop in TRACER ORDER)
        for i in range(n_tracers):
            if not np.all((ut := tracer_units_matrix[i]) == self.default_units_out):
                if np.all(ut == ut[0]):
                    tracer_obs_matrix[i] = (
                        pQ(tracer_obs_matrix[i], ut[0]).to(self.default_units_out).value
                    )
                    tracer_err_index[i] = (
                        pQ(tracer_err_index[i], ut[0]).to(self.default_units_out).value
                    )
                else:
                    for j in range(n_samples):
                        tracer_obs_matrix[i][j] = (
                            pQ(tracer_obs_matrix[i][j], ut[j])
                            .to(self.default_units_out)
                            .value
                        )
                        tracer_err_index[i][j] = (
                            pQ(tracer_err_index[i][j], ut[j])
                            .to(self.default_units_out)
                            .value
                        )

        # convert all fixed regressor inputs to default_units_in
        for r in fixed_regressors:
            if not np.all(
                (ur := units_foreach_fixed_regressor[r]) == self.default_units_in[r]
            ):
                if np.all(ur == ur[0]):
                    obs_foreach_fixed_regressor[r] = (
                        pQ(obs_foreach_fixed_regressor[r], ur[0])
                        .to(self.default_units_in[r])
                        .value
                    )
                    errs_foreach_fixed_regressor[r] = (
                        pQ(errs_foreach_fixed_regressor[r], ur[0])
                        .to(self.default_units_in[r])
                        .value
                    )
                else:
                    for i in range(len(obs_foreach_fixed_regressor[r])):
                        obs_foreach_fixed_regressor[r][i] = (
                            pQ(obs_foreach_fixed_regressor[r][i], ur[i])
                            .to(self.default_units_in[r])
                            .value
                        )
                    for i in range(len(errs_foreach_fixed_regressor[r])):
                        errs_foreach_fixed_regressor[r][i] = (
                            pQ(errs_foreach_fixed_regressor[r][i], ur[i])
                            .to(self.default_units_in[r])
                            .value
                        )

        return (
            obs_foreach_fixed_regressor,
            errs_foreach_fixed_regressor,
            tracer_obs_matrix,
            tracer_errs_matrix,
        )


# +++++++ TESTING ++++++++

if __name__ == "__main__":
    from pagos.gas import calc_Ceq, abn
    from pagos.core import set_warn_nonmult

    set_warn_nonmult(False)

    def ua(gas, T, S, p, A):
        ceq = calc_Ceq(gas, T, S, p)
        excess_air = A * abn(gas)
        return ceq + excess_air

    print(ua("He", 15, 20, 0.97, pQ(2e-4, "mol/kg")))

    ua_model = TracerModel(
        model_function=ua,
        default_units_in={"T": "degC", "S": "permille", "p": "atm", "A": "mol/kg"},
        default_units_out="mol_g/kg",
    )

    X = ua_model.run("He", pQ(288.15, "K"), 20, 0.97, 2e-4)
    print(X)

    observations = np.array(
        [
            ua_model.run(g, 15, 20, 0.97, 2e-4).value * np.random.normal(1, 0.1)
            for g in ["He", "Ne", "Ar", "Kr", "Xe"]
        ]
    )
    errs = observations / 80

    fit_ua = ua_model.fit(
        fixed_regressors={"S": 20, "p": 0.97},
        regressors_to_fit={"T": 10, "A": 1e-5},
        tracers=["He", "Ne", "Ar", "Kr", "Xe"],
        obs_tr=observations,
        obs_tr_errs=errs,
    )

    print(fit_ua.params)

    # THIS WORKS! Note that fit(...) at the moment is does not perform any of the pre-preparation required
    # for the observations (needs to take in quantities with no units, will not perform any MC stuff,
    # appropriate conversions need to have been done beforehand). This is intentional and should happen
    # before fit(...) is called!

    fit_ua = ua_model.fit(
        fixed_regressors={"S": pQ(20, "g/kg"), "p": pQ(0.97 * 1013.25, "mbar")},
        regressors_to_fit={"T": pQ(283.15, "K"), "A": 1e-5},
        tracers=["He", "Ne", "Ar", "Kr", "Xe"],
        obs_tr=observations,
        obs_tr_errs=errs,
    )

    print(fit_ua.params)

    my_data = pd.read_csv("temp/tempdata.csv")

    fit_df_ua = ua_model.fit_dataframe(
        my_data,
        ["He", "Ne", "Ar", "Kr", "Xe"],
        {"T": pQ(283.15, "K"), "A": 1e-5},
    )

    print(pd.DataFrame(fit_df_ua.get_results(("T", "A"))).compare(my_data[["T", "A"]]))
