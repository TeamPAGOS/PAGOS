from magicgui import magic_factory
from magicgui.widgets import (
    MainWindow,
    Dialog,
    Label,
)
from magicgui.application import use_app
from qtpy.QtWidgets import (
    QAbstractItemView,
    QPushButton,
)
from inspect import isfunction, getmodule, getsource
import pandas as pd
import numpy as np
import re
from inspect import signature

# pagos imports
import pagos.builtin_models as pagos_bms
from pagos.gui.gui_util import remove_docstrings_and_type_hints, ordc
from pagos import GasExchangeModel

# globals
list_of_builtin_models = [
    func.__name__
    for func in pagos_bms.__dict__.values()
    if isfunction(func) and getmodule(func) == pagos_bms
]
custom_model_name_placeholder = "Custom..."
custom_model_code_placeholder = "def custommodel(gas, ...):"
default_setup_field_code = "from pagos.gas import abn, ice, calc_Ceq, calc_dCeq_dT, calc_Sc, mv\nfrom pagos.water import calc_kinvisc"


# TODO: allow file importing for the models! (drag and drop also?)
class Main:
    def __init__(self):
        # some variables that will be used later
        self.current_selected_model = custom_model_name_placeholder
        self.saved_custom_model_code = custom_model_code_placeholder
        self.current_model_code = ""
        self.current_setup_code = default_setup_field_code
        self.suppress_codefield_change = False
        self.suppress_selected_model_change = False
        self.used_tracers = {}
        self.used_other_params = {}
        self.manual_errs = {}
        self.manual_units = {}
        self.selected_to_fit = []
        self.fit_param_units = {}
        self.comp_mod = None
        self.all_model_args_except_gas = []

        # set up the left and right hand side of the main window
        self.left = self.left_fac()
        self.right = self.right_fac()
        self.left.self.bind(self)
        self.right.self.bind(self)

        self.maincontainer = MainWindow(
            widgets=[self.left, self.right],
            layout="horizontal",
            labels=False,
            name="PAGOS",
        )

        # some individual settings that couldn't be done inside magicgui
        try:
            self.left.modelfield.native.setFontFamily("mono")
            self.left.modelfield.value = (
                self.left.modelfield.value
            )  # <- refresh so that the mono font is applied
        except:  # noqa: E722
            print("WARNING: Could not set font of model field, keeping default.")
        self.left.modelfield.native.setTabStopDistance(35.0)
        self.right.datatable.native.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        for ch in self.right.manual_errs.native.findChildren(QPushButton):
            ch.setVisible(False)
        for ch in self.right.manual_units.native.findChildren(QPushButton):
            ch.setVisible(False)
        for ch in self.left.fitparam_unit_input.native.findChildren(QPushButton):
            ch.setVisible(False)

        # setup callbacks left
        self.left.modelselect.changed.connect(self.model_selected)
        self.left.setupfield.native.textChanged.connect(self.setup_changed)
        # self.left.modelfield.changed.connect(self.code_changed) # TODO: why does this not work? Current solution: use native, see below
        self.left.modelfield.native.textChanged.connect(self.code_changed)
        self.left.select_to_fit_button.clicked.connect(
            self.select_to_fit_button_clicked
        )
        self.left.fit_button.clicked.connect(self.perform_fit)
        # setup callbacks right
        self.right.select_tracers.clicked.connect(lambda: self.select_tr_or_op(mode=1))
        self.right.select_other_params.clicked.connect(
            lambda: self.select_tr_or_op(mode=2)
        )

        # menu
        self.maincontainer.create_menu_item(
            "File", "Import data", callback=self.openfile, shortcut="ctrl+o"
        )

        self.maincontainer.show(run=True)

    ### callbacks for the MENU BAR ###

    # file opening callback
    def openfile(self):
        # loading tip
        self.left.filename.value = "loading data..."

        # open the file dialog object which is part of the MainWindow (TODO: I think???)
        imported_data_path: str = use_app().get_obj("show_file_dialog")(
            mode="r", caption="Import data"
        )
        raw_dataframe = pd.read_csv(imported_data_path)

        # get some information about the file
        self.filename = imported_data_path.split(sep="/")[-1]
        self.imported_params = raw_dataframe.columns

        # convert raw_dataframe to dict of pandas Series (magicgui cannot handle entire DataFrame):
        data_as_dict = raw_dataframe.to_dict(orient="series")

        # add data to the view table
        self.right.datatable.value = data_as_dict

        # alter the view of the left hand side
        self.left.filename.value = self.filename
        self.left.modelselect.visible = True
        self.left.setupfield.visible = True
        self.left.modelfield.visible = True
        self.left.select_to_fit.visible = True
        self.left.select_to_fit_button.visible = True

    ### callbacks for LEFT hand side ###

    # model selection callback
    def model_selected(self, modelname):
        # change the internal current_selected_model (unless suppressed)
        if not self.suppress_selected_model_change:
            self.current_selected_model = modelname
            self.suppress_selected_model_change = True
        # if suppressed, toggle back to non-suppressed
        else:
            self.suppress_selected_model_change = False

        # print model code to the modelfield (unless suppressed)
        if not self.suppress_codefield_change:
            if modelname == custom_model_name_placeholder:
                self.left.modelfield.value = self.saved_custom_model_code
            else:
                modelfunc = getattr(pagos_bms, modelname)
                sourcecode = remove_docstrings_and_type_hints(getsource(modelfunc))
                self.left.modelfield.value = sourcecode
        # non-suppress the change current_selected_model
        self.suppress_selected_model_change = False

    def setup_changed(self):
        self.current_setup_code = self.left.setupfield.value

    # code changed callback
    def code_changed(self):
        if (
            self.current_selected_model != custom_model_name_placeholder
            and not self.suppress_selected_model_change
        ):
            self.suppress_codefield_change = True
            self.left.modelselect.value = custom_model_name_placeholder
            self.suppress_codefield_change = False

        self.current_model_code = self.left.modelfield.value

        # save the current code inside the modelfield if the model selected is custom, so that the user can return to it later
        if self.current_selected_model == custom_model_name_placeholder:
            self.saved_custom_model_code = self.current_model_code

        # get name of function using regex
        funccode_regex = r"(def \b\w+\b\((.+|())\)(:| :)((\n\s.+)+|.+))"  # matches the whole function definition and body "def <funcname>(...): ..."
        funcname_regex = (
            r"(?<=def\s)\w+(?=\()"  # matches only the function name "<funcname>"
        )

        # tries to compile the current code inside the modelfield into something runnable
        try:
            funccode = re.findall(funccode_regex, self.current_model_code)[-1][
                0
            ]  # finds the LAST def statement
            self.funcname = re.findall(funcname_regex, funccode)[
                0
            ]  # finds the corresponding function name

            # translate typed code into code object
            try:
                self.comp_mod = compile(self.current_model_code, "<string>", "exec")
                self.left.errmsgs.visible = False
                print("Model code changed. Successful compilation!")
            except (SyntaxError, ModuleNotFoundError) as je:
                self.left.errmsgs.value = (
                    "WARNING: Current input contains a %s." % je.__name__
                )
                self.left.errmsgs.visible = True
                print(
                    "Model code changed. [!] UNSUCCESSFUL compilation. Error message below."
                )
                print(je)
                # clear fit-parameter selection list
                self.left.select_to_fit.choices = []

            self.update_fit_param_selection_list()
        except IndexError as ie:
            self.left.errmsgs.value = "Current input could not compile."
            self.left.errmsgs.visible = True
            print(
                "Model code changed. [!] UNSUCCESSFUL compilation. Likely due to the code being incomplete. Error message below."
            )
            print(ie)
            # clear fit-parameter selection list
            self.left.select_to_fit.choices = []

        # FIXME: typing certain things into the modelfield or deleting all the text will break the monospace font and return to default - why does this happen?!

    def update_fit_param_selection_list(self):
        self.left.fitparam_unit_input.visible = False
        self.left.select_to_fit.value = []
        # update fit-parameter selection list
        if self.comp_mod:  # checks if any valid compiled model code exists
            # extract argument names of the compiled function
            _locals, _globals = {}, {}
            exec(self.comp_mod, _globals, _locals)
            all_arguments_in_model = list(
                signature(_locals[self.funcname]).parameters.keys()
            )

            # array that needs to be accessed later in perform_fit()
            self.all_model_args_except_gas = ordc(all_arguments_in_model, ["gas"])

            # filter out the arguments which the user has selected to read in from data (the so-called "other params")
            args_without_non_fitted_params = ordc(
                self.all_model_args_except_gas, list(self.used_other_params.keys())
            )
            self.left.select_to_fit.choices = args_without_non_fitted_params
        else:
            self.left.select_to_fit.choices = []

    # select parameters for fitting button callback
    def select_to_fit_button_clicked(self):
        self.selected_to_fit = self.left.select_to_fit.value
        if self.selected_to_fit:
            self.left.fit_button.visible = True
            self.left.fit_button.text = "Perform fit on " + re.sub(
                r"[^\w\,\s]", "", str(self.selected_to_fit)
            )

            # show fit parameter unit input widget
            self.left.fitparam_unit_input.visible = True
            self.left.fitparam_unit_input.value = ["" for entry in self.selected_to_fit]
            # hide editing buttons - user should not add or remove anything via this mechanism
            for ch in self.left.fitparam_unit_input.native.findChildren(QPushButton):
                ch.setVisible(False)
            # add labels (not possible in magicgui ListEdit constructor)
            for entry, val in zip(
                self.left.fitparam_unit_input[:-1], self.selected_to_fit
            ):
                entry.label = val

        # hide widgets if nothing is selected
        else:
            self.left.fit_button.visible = False
            self.left.fitparam_unit_input.visible = False

    # perform fit button callback
    def perform_fit(self):
        ## parsing of manually input units/errors
        # extract values from manual errors widget and place them in the self.manual_errs dictionary at the corresponding place
        for entry in self.right.manual_errs._list[:-1]:
            label = entry.label
            self.manual_errs[label.split(" ", 1)[1]] = entry.value
            # split to remove 'err' from string
        for entry in self.right.manual_units._list[:-1]:
            label = entry.label
            self.manual_units[label.split(" ", 1)[1]] = entry.value
            # split to remove 'unit' from string

        # extract values from units on the fit parameters (necessarily user-defined)
        for entry in self.left.fitparam_unit_input._list[:-1]:
            label = entry.label
            self.fit_param_units[label] = entry.value

        ## creation of final objects passed to the fit
        # DataFrames of the tracer/other parameter data values/errors/units
        _temp_union = self.used_tracers | self.used_other_params
        _temp_tracer_data_values = {
            x: self.used_tracers[x]["data"] for x in self.used_tracers
        }
        _temp_tracer_data_units = {
            "units " + x: 0 for x in self.used_tracers
        }  # <- 0 placeholder for empty
        _temp_tracer_data_errors = {
            "errs " + x: 0 for x in self.used_tracers
        }  # <- 0 placeholder for empty
        _temp_op_data_values = {
            x: self.used_other_params[x]["data"] for x in self.used_other_params
        }
        _temp_op_data_errors = {
            "units " + x: 0 for x in self.used_other_params
        }  # <- 0 placeholder for empty
        _temp_op_data_units = {
            "errs " + x: 0 for x in self.used_other_params
        }  # <- 0 placeholder for empty

        # "Assign B-Values of A or use C If Manual"
        # This function is only used here, within perform_fit()
        def abvacim(A, B, C, add_prefix=True):
            _r = {}
            if add_prefix:
                pref = B + " "
            else:
                pref = ""
            for x in A:
                _entry = A[x]
                if isinstance(e := _entry[B], pd.Series):
                    _r[pref + x] = e[0]
                elif e == "man":
                    _r[pref + x] = C[x]
                else:
                    raise NotImplementedError(
                        "the required object is neither the string 'man' nor a Pandas Series. This should not have happened, report back to maintainer!"
                    )
            return _r

        _temp_tracer_data_errors = abvacim(self.used_tracers, "errs", self.manual_errs)
        _temp_tracer_data_units = abvacim(self.used_tracers, "units", self.manual_units)
        _temp_op_data_errors = abvacim(self.used_other_params, "errs", self.manual_errs)
        _temp_op_data_units = abvacim(
            self.used_other_params, "units", self.manual_units
        )

        _temp_default_param_units = [
            (
                abvacim(self.used_other_params, "units", self.manual_units, False)
                | self.fit_param_units
            )[x]
            for x in self.all_model_args_except_gas
        ]

        df_to_pass_in = pd.DataFrame(
            _temp_tracer_data_values | _temp_tracer_data_errors | _temp_op_data_values
        )

        ## passing the collected arguments into PAGOS
        # TODO: add a way for the user to input in initial guesses
        create_model_string = (
            "\ngem = GasExchangeModel(%s, _temp_default_param_units, _temp_tracer_data_units['units ' + list(self.used_tracers.keys())[0]])"
            % self.funcname
        )
        fit_model_string = "\nfitresults = gem.fit(data=df_to_pass_in, to_fit=self.selected_to_fit, init_guess=np.zeros(len(self.selected_to_fit)), tracers_used=list(self.used_tracers.keys()))"
        # deal with the setup code
        setup_namespace = {}
        try:
            exec(self.current_setup_code, globals(), setup_namespace)
        except Exception as e:
            print(f"Failed to execute setup code: {e}")
            return
        # combine function definition, GasExchangeModel object creation and fitting procedure all into one executable code object,
        # taking into account the relevant locals and globals
        exec_globals = setup_namespace.copy()
        exec_locals = {
            "df_to_pass_in": df_to_pass_in,
            "self": self,
            "np": np,
            "pd": pd,
            "_temp_default_param_units": _temp_default_param_units,
            "_temp_tracer_data_units": _temp_tracer_data_units,
            "GasExchangeModel": GasExchangeModel,
        }
        code_to_execute = (
            self.current_model_code + create_model_string + fit_model_string
        )
        # execute!
        exec(code_to_execute, exec_globals, exec_locals)
        print(exec_locals["fitresults"])

    ### callbacks for RIGHT hand side ###

    # select tracers or other parameters button callback
    def select_tr_or_op(self, mode):
        # get user-selected ranges from the table
        selected_ranges = self.right.datatable.native.selectedRanges()

        # get column headings from ranges
        headings = []
        for r in selected_ranges:
            startindex = r.leftColumn()
            columncount = r.columnCount()
            for i in range(columncount):
                headings.append(self.right.datatable.column_headers[startindex + i])
        selected_tracers = set(headings)

        # parse error/unit columns from selection
        # search for columns containing words like "error", "err", "uncertainties" etc, and the same for units
        errorpattern = r"(\s|^)(err|errs|error|errors|uncertainty|uncertainties|sigma|sigmas|err\.|err\.s|Err|Errs|Error|Errors|Uncertainty|Uncertainties|Sigma|Sigmas|Err\.|Err\.s)(\s|$)"
        unitpattern = r"(\s|^)(unit|units|dim|dims|dimension|dimensions|dim\.|dim\.s|Unit|Units|Dim|Dims|Dimension|Dimensions|Dim\.|Dim\.s)(\s|$)"

        which_errors = set(
            tracer for tracer in selected_tracers if re.search(errorpattern, tracer)
        )
        which_units = set(
            tracer for tracer in selected_tracers if re.search(unitpattern, tracer)
        )
        if which_errors.intersection(which_units):
            # TODO: proper code to handle this should go here, with warning box rather than CLI output
            print(
                "CONFLICT: PAGOS could not parse which columns contain error data and which contain unit data!"
            )
        else:
            tr_or_op_dict = {
                k: {"err": [], "unit": []}
                for k in selected_tracers.difference(which_errors, which_units)
            }

            for elt_i in tr_or_op_dict:
                for er_j in which_errors:
                    if re.search(rf"\b{re.escape(elt_i)}\b", er_j):
                        tr_or_op_dict[elt_i]["err"].append(er_j)
                for un_j in which_units:
                    if re.search(rf"\b{re.escape(elt_i)}\b", un_j):
                        tr_or_op_dict[elt_i]["unit"].append(un_j)
            # after this step, we have a dict_i-dict_j-list_k structure,  {tracer_i: {'err':[errs_k], 'unit':[units_k]}}
            # we now ask the user to resolve any conflicts, e.g. if two sets of errors were found for one tracer (i.e. we want [errs_k] and [units_k] to have only one element each).
            # alternatively, the user just does this manually if self.right.man_eu is True

            eu_dialog_widgets = []
            n_err_widgs, n_unit_widgs = 0, 0
            manselect = self.right.man_eu.value
            for elt_i in tr_or_op_dict:
                err, unit = tr_or_op_dict[elt_i]["err"], tr_or_op_dict[elt_i]["unit"]
                # if manual error selection is necessary
                if len(err) > 0 and manselect or len(err) > 1:

                    @magic_factory(
                        auto_call=True,
                        rbs={
                            "widget_type": "RadioButtons",
                            "choices": err + ["none of the above"],
                        },
                        labels=False,
                        tracername={"visible": False},
                    )
                    def err_radio(rbs=err[0], tracername=elt_i):
                        return ("err", tracername)

                    eu_dialog_widgets.append(
                        Label(value="Which of these is an error on %s?" % elt_i)
                    )
                    eu_dialog_widgets.append(err_radio())
                    n_err_widgs += 1
                # if manual unit selection is necessary
                if len(unit) > 0 and manselect or len(unit) > 1:

                    @magic_factory(
                        auto_call=True,
                        rbs={
                            "widget_type": "RadioButtons",
                            "choices": unit + ["none of the above"],
                        },
                        labels=False,
                        tracername={"visible": False},
                    )
                    def unit_radio(rbs=unit[0], tracername=elt_i):
                        return ("unit", tracername)

                    eu_dialog_widgets.append(
                        Label(value="Which of these is a unit on %s?" % elt_i)
                    )
                    eu_dialog_widgets.append(unit_radio())
                    n_unit_widgs += 1

            # final step - defined here so that it can be accessed either immediately or after the conflict resolution dialog has completed successfully
            def finished_select_tracers():
                # clear current used_tracers or used_other_params matrix and replace with the selected column data
                def raise_mode_error():
                    raise ValueError(
                        "Something has gone terribly wrong - mode argument to select_tr_or_op should only be 1 or 2, not %i"
                        % mode
                    )

                # NOTE: welcome to if-statement hell...
                if mode == 1:
                    self.used_tracers = {}
                elif mode == 2:
                    self.used_other_params = {}
                else:
                    raise_mode_error()
                for q in tr_or_op_dict:
                    data = self.right.datatable.to_dict("series")[q]
                    if len(err_entry := tr_or_op_dict[q]["err"]) == 0:
                        errs = "man"
                    else:
                        if err_entry[0] == "none of the above":
                            errs = "man"
                        else:
                            errs = self.right.datatable.to_dict("series")[err_entry[0]]
                    if len(unit_entry := tr_or_op_dict[q]["unit"]) == 0:
                        units = "man"
                    else:
                        if unit_entry[0] == "none of the above":
                            units = "man"
                        else:
                            units = self.right.datatable.to_dict("series")[
                                unit_entry[0]
                            ]

                    if mode == 1:
                        self.used_tracers[q] = {
                            "data": data,
                            "errs": errs,
                            "units": units,
                        }
                    elif mode == 2:
                        self.used_other_params[q] = {
                            "data": data,
                            "errs": errs,
                            "units": units,
                        }
                    else:
                        raise_mode_error()

                # setting widgets
                def isman(x):
                    return (
                        isinstance(x, str) and x == "man"
                    )  # this construction avoids "ValueError: The truth value of a Series is ambiguous" from Pandas.

                manual_errs = [
                    q for q in self.used_tracers if isman(self.used_tracers[q]["errs"])
                ] + [
                    q
                    for q in self.used_other_params
                    if isman(self.used_other_params[q]["errs"])
                ]
                manual_units = [
                    q for q in self.used_tracers if isman(self.used_tracers[q]["units"])
                ] + [
                    q
                    for q in self.used_other_params
                    if isman(self.used_other_params[q]["units"])
                ]
                self.manual_errs = {k: "" for k in manual_errs}
                self.manual_units = {k: "" for k in manual_units}

                self.right.manual_errs.value = ["" for entry in manual_errs]
                self.right.manual_units.value = ["" for entry in manual_units]
                # hide editing buttons - user should not add or remove anything via this mechanism
                for ch in self.right.manual_errs.native.findChildren(QPushButton):
                    ch.setVisible(False)
                for ch in self.right.manual_units.native.findChildren(QPushButton):
                    ch.setVisible(False)
                # add labels (not possible in magicgui ListEdit constructor)
                for entry, val in zip(self.right.manual_errs._list[:-1], manual_errs):
                    entry.label = "err " + val
                for entry, val in zip(self.right.manual_units._list[:-1], manual_units):
                    entry.label = "unit " + val
                # set text widget
                self.right.text_over_tracers1.value = (
                    "Quantities taking errors from data table: "
                    + ", ".join(
                        [
                            elt
                            for elt in self.used_tracers
                            if not isman(self.used_tracers[elt]["errs"])
                        ]
                        + [
                            elt
                            for elt in self.used_other_params
                            if not isman(self.used_other_params[elt]["errs"])
                        ]
                    )
                )
                self.right.text_over_tracers2.value = (
                    "Quantities taking units from data table: "
                    + ", ".join(
                        [
                            elt
                            for elt in self.used_tracers
                            if not isman(self.used_tracers[elt]["units"])
                        ]
                        + [
                            elt
                            for elt in self.used_other_params
                            if not isman(self.used_other_params[elt]["units"])
                        ]
                    )
                )

                # set fit parameter selection widget
                self.update_fit_param_selection_list()

            if n_err_widgs == 0 and n_unit_widgs == 0:
                finished_select_tracers()
            else:
                if n_unit_widgs > 0 and n_err_widgs > 0:
                    textappend1 = "ERRORS/UNITS"
                elif n_err_widgs > 0:
                    textappend1 = "ERRORS"
                elif n_unit_widgs > 0:
                    textappend1 = "UNITS"
                if manselect:
                    textappend2 = ""
                else:
                    textappend2 = " and PAGOS could not automatically parse them"
                eu_msg = Label(
                    value=f"Some columns you selected seem like they might be {textappend1} on tracer measurements{textappend2}. Please select those which are:"
                )
                eu_dialog_widgets.insert(0, eu_msg)
                eu_dialog = Dialog(
                    widgets=eu_dialog_widgets, labels=False, scrollable=True
                )
                eu_dialog.native.setModal(True)
                # FIXME: CANNOT GET RESIZING TO WORK!!
                if eu_dialog.height > 600:
                    eu_dialog.native.resize(eu_dialog.width, 600)
                eu_dialog.show()

                # setting action on accepted close
                def change_used_tracers():
                    for wdg in eu_dialog_widgets[2::2]:
                        unitorerr, tracername = wdg.__call__()
                        colname = wdg.rbs.value
                        tr_or_op_dict[tracername][unitorerr] = [colname]
                    finished_select_tracers()

                eu_dialog.native.accepted.connect(change_used_tracers)

    # left hand side of Window
    @magic_factory(
        layout="vertical",
        auto_call=True,
        labels=True,
        filename={
            "widget_type": "Label",
            "value": "Add some data to get started",
            "label": "Sample name",
        },
        modelselect={
            "widget_type": "ComboBox",
            "choices": ["Custom..."] + list_of_builtin_models,
            "value": custom_model_name_placeholder,
            "visible": False,
        },
        select_to_fit={"widget_type": "Select", "visible": False},
        select_to_fit_button={
            "widget_type": "PushButton",
            "value": False,
            "text": "Mark selected parameters for fitting",
            "visible": False,
        },
        fitparam_unit_input={
            "widget_type": "ListEdit",
            "value": [],
            "labels": True,
            "visible": False,
            "label": "Input units on fit parameters:",
        },
        errmsgs={"widget_type": "Label", "value": "ERROR", "visible": False},
        setupfield={
            "widget_type": "TextEdit",
            "visible": False,
            "value": default_setup_field_code,
        },
        modelfield={
            "widget_type": "TextEdit",
            "visible": False,
            "value": custom_model_code_placeholder,
        },
        fit_button={
            "widget_type": "PushButton",
            "value": False,
            "text": "Perform fit",
            "visible": False,
        },
    )
    def left_fac(
        self,
        filename: str,
        modelselect: list,
        select_to_fit,
        select_to_fit_button: bool,
        fitparam_unit_input: list[str],
        errmsgs: str,
        setupfield: str,
        modelfield: str,
        fit_button: bool,
    ):
        pass

    # right hand side of window
    @magic_factory(
        layout="vertical",
        auto_call=True,
        labels=False,
        man_eu={
            "widget_type": "CheckBox",
            "text": "Manually select all units/errors",
            "value": False,
        },
        select_tracers={
            "widget_type": "PushButton",
            "text": "Select tracers",
            "tooltip": "Select columns in the data table below and then click here to set tracers you'll use in the model.",
        },
        select_other_params={
            "widget_type": "PushButton",
            "text": "Select other parameters",
            "tooltip": "Select columns in the data table below and then click here to set non-tracer parameters you'll use in the model.",
        },
        text_over_tracers1={
            "widget_type": "Label",
            "value": "Quantities taking errors from data table:",
        },
        text_over_tracers2={
            "widget_type": "Label",
            "value": "Quantities taking units from data table:",
        },
        manual_errs={"widget_type": "ListEdit", "value": [], "labels": True},
        manual_units={"widget_type": "ListEdit", "value": [], "labels": True},
        text_over_dt={"widget_type": "Label", "value": "Data"},
        datatable={"widget_type": "Table", "value": None},
    )
    def right_fac(
        self,
        man_eu: bool,
        select_tracers: bool,
        select_other_params: bool,
        text_over_tracers1: str,
        text_over_tracers2: str,
        manual_errs: list[str],
        manual_units: list[str],
        text_over_dt: str,
        datatable: float,
    ):
        pass


# TODO: a lot of stuff in this is hidden until the user inputs correct data or presses a button etc. Is it possible instead to have things simply "greyed out"? # SUGGESTION ("enabled" parameter)


Main()
