from numbers import Number

from pagos.newcore import PAGOSQuantity, pQ, pCalc
import numpy as np
import pandas as pd
from lmfit import fit_report, minimize, Parameters
from tqdm import tqdm
from collections.abc import Callable, Iterable
from inspect import getfullargspec, signature


class TracerModel:
    """
    Object that holds a function representing a tracer model and its methods,
    including fitting to data and forward modelling given an input.
    """

    def __init__(
        self,
        model_function: Callable,
        default_units_in: Iterable[str],
        default_units_out: str,
        # jacobian: Callable = None,        TODO later?
        # jacobian_units: list[str] = None  TODO later?
    ):
        """
        :param model_function: function representing the model
        :type model_function: Callable
        :param default_units_in: units of the input arguments to `model_function` to be **assumed** if none are explicitly given.
        Must be in the same order as the arguments to `model_function`.

        :type default_units_in: Iterable[str]
        :param default_units_out: the units which the output of `model_function` should be **converted to**
        :type default_units_out: str
        """

        # check type of default_units_in
        if not isinstance(default_units_in, dict):
            raise TypeError("default_units_in must be a dictionary")

        # set instance variables

        # list of parameters in the model function's signature
        self.modelfunc_params = list(signature(model_function).parameters)

        # if default_units_in argument did not include None
        # at the start for the tracer parameter, add this in here

        if len(default_units_in) == len(self.modelfunc_params) - 1:
            self.default_units_in = {self.modelfunc_params[0]: None} | default_units_in
        elif len(default_units_in) == len(self.modelfunc_params):
            self.default_units_in = default_units_in
        else:
            raise ValueError(
                "default_units_in should have one entry for every argument to model_function (except the tracer)."
            )

        self.default_units_out = default_units_out

        self.model_function = pCalc.unit_aware(
            self.default_units_in, self.default_units_out
        )(model_function)

        self.model_arguments = getfullargspec(self.model_function).args

        # initialisation of objective function which will be used for fitting
        def objfunc(
            regressors: Parameters,
            tracers: list,
            obs_tr: np.ndarray,
            obs_tr_errs: np.ndarray,
        ):
            """This is the objective function that will be minimised by
            lmfit.minimize. It is the residual of observed and modelled data.

            Args:
                regressors (Parameters): `Parameters` object holding all fixed and variable regressors to be passed to `minimize` (all non-tracer variables of the model)
                tracers (list): the tracers that will be used (e.g. `['He', 'Ne', 'Ar']`)
                obs_tr (np.ndarray): observed tracer values, in the order of the `tracers` list, stripped of units
                obs_tr_errs (np.ndarray): observed tracer errors, in the order of the `tracers` list, stripped of units
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
                kwargs_to_model_func[k] = pQ(k, units_in[k])

        result = self.model_function(*args_to_model_func, **kwargs_to_model_func)

        if units_out != "default":
            return result.to(units_out)
        else:
            return result

    def fit(
        self,
        fixed_regressors: dict,
        regressors_to_fit: dict,
        tracers: list,
        obs_tr: np.ndarray,
        obs_tr_errs: np.ndarray,
        regr_to_fit_bounds: dict | None = None,
    ):

        # turn regressors dictionary into Parameters object (passed into minimize())
        regr_params_object = Parameters()
        for k in fixed_regressors:  # noqa: PLC0206
            # add fixed regressor to Parameters object
            regr_params_object.add(k, fixed_regressors[k], vary=False)
        for k in regressors_to_fit:  # noqa: PLC0206
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

        # fit objective function to provided data
        fit_result = minimize(
            self.objfunc, regr_params_object, args=(tracers, obs_tr, obs_tr_errs)
        )
        return fit_result


# ++++++ TESTING ++++++++

if __name__ == "__main__":
    from pagos.gasobject import calc_Ceq, abn
    from pagos.newcore import set_warn_nonmult

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

    print(fit_report(fit_ua))

    # THIS WORKS! Note that fit(...) at the moment is does not perform any of the pre-preparation required
    # for the observations (needs to take in quantities with no units, will not perform any MC stuff,
    # appropriate conversions need to have been done beforehand). This intentional and should happen
    # before fit(...) is called!
