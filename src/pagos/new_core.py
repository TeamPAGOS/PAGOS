import ast
import inspect
from collections.abc import Callable
from numbers import Number, Real
from textwrap import dedent

import pint
from pint.util import UnitsContainer
from visast import visualise
from pagos import visast_util

visualise.graph = visast_util.graph

ureg = pint.UnitRegistry()


class PAGOSQuantity:
    def __init__(self, value, units):
        self.value = value
        if isinstance(units, str):
            self.units = ureg._parse_units_as_container(units)
        elif isinstance(units, pint.util.UnitsContainer):
            self.units = units
        else:
            raise NotImplementedError("Type of units passed in is not implemented")


def pQ(value, units):
    return PAGOSQuantity(value, units)


# Register of unit aware functions
REGISTERED_UNIT_AWARE_FUNCTIONS: dict[str, tuple[dict | None, str | None]] = {}


def register_unit_aware_function(
    func_name: str, in_args_units: dict | None, out_units: str | None
) -> None:
    REGISTERED_UNIT_AWARE_FUNCTIONS[func_name] = (in_args_units, out_units)


def is_function_unit_aware(func_name: str) -> bool:
    return func_name in REGISTERED_UNIT_AWARE_FUNCTIONS


def get_unit_aware_function_info(func_name: str) -> tuple[dict | None, str | None]:
    return REGISTERED_UNIT_AWARE_FUNCTIONS[func_name]


def unit_aware(default_units_in: dict | None, units_out: str | None, debug=False):
    def _unit_aware(func: Callable):

        if default_units_in is None:
            input_arguments_units = None
        else:
            input_arguments_units = {
                k: None if u is None else ureg.parse_units_as_container(u)
                for k, u in default_units_in.items()
            }
        output_units = (
            None if units_out is None else ureg.parse_units_as_container(units_out)
        )

        # add function's details to register of unit aware functions
        register_unit_aware_function(func.__name__, input_arguments_units, output_units)

        # get AST of func (dedent used so that functions defined inside other
        # functions do not have invalid whitespace at the beginning)
        _ast = ast.parse(dedent(inspect.getsource(func)))

        # Find the instances of when the function makes an assignment
        # from an external scope. These have to be artificially run
        # here so that the units associated with them can be recorded.
        # Also assigns units to function argument-related nodes.
        _init_load_visitor = InitialLoadVisitor()
        _ast = ast.fix_missing_locations(_init_load_visitor.visit(_ast))

        # Now that the function arguments and external assignments are unit-laden,
        # we send a NodeTransformer around the AST again. Surgery is performed on
        # nodes where unit conversions would occur. Repeat until there are no more
        # conversions.

        # Now these external assignments are unit-laden, we send a visitor
        # around the AST again, setting these units on any loading nodes
        # that access them.
        # Surgery is performed on nodes where unit conversions would occur.
        # Repeat until there are no more conversions.
        _unit_assignment_visitor = UnitAssignmentVisitor(func, debug=debug)
        c = 0
        while True:
            # visualise.graph(_ast)
            _unit_assignment_visitor.changelock = set()
            _unit_assignment_visitor.did_anything_change = False
            _ast = ast.fix_missing_locations(_unit_assignment_visitor.visit(_ast))
            if not _unit_assignment_visitor.did_anything_change:
                break
            c += 1
            # visualise.graph(_ast)

        exec(ast.unparse(_ast), globals())
        exec(f"{func.__name__}.ast = _ast", globals(), locals())
        exec(
            f"{func.__name__}.__globals__.update(func.__globals__)", globals(), locals()
        )

        return eval(func.__name__, globals(), locals())

    return _unit_aware


# sentinel object for unassigned units on nodes
UNASSIGNED = object()


def execute_partial_tree(node: ast.AST, in_module: ast.AST, globs):
    load_statement_tree = ast.Module([node], in_module.type_ignores)
    # Execute the load statement
    _temp_globals = globs
    exec(ast.unparse(load_statement_tree), _temp_globals)
    return globs


def raise_error_if_invalid(obj):
    if isinstance(obj, pint.DimensionalityError):
        raise obj


class InitialLoadVisitor(ast.NodeTransformer):
    """
    Visits the AST and finds nodes where the arguments to the function
    are loaded. Also finds nodes where variables which are nonlocal
    to the function are loaded. This can happen in four main ways:
    ```
    1) Name -> Load

    2) Subscript -> Name     -> Load
                 -> Constant
                 -> Load

    3) Attribute -> Name -> Load
                 -> Load

    4) Call -> Name       -> Load
            -> arg node 1
               ...
            -> arg node n
    ```
    """

    def __init__(self):
        super().__init__()

    def visit(self, node):
        # by default, all nodes begin with UNASSIGNED sentinel value for units
        node.units = UNASSIGNED
        return super().visit(node)


class UnitAssignmentVisitor(ast.NodeTransformer):
    def __init__(self, func: Callable, debug: bool):
        self.func = func

        # boolean which triggers a new visitation cycle if set to true
        self.did_anything_change = False

        # boolean which causes debug printing
        self.debug = debug

        # this is a set of variables which are not allowed to be changed in the AST. Variables
        # are added whenever an Assign statement would change the units of a node. This means
        # that we MIGHT be re-assigning a variable (e.g. `v = ...` inside a function, where v
        # was already an argument to the function), so we need to wait 1 more cycle before
        # prematurely converting units (other references to v will need the newly acquired units
        # from the internal assignment, not those from the function argument's units!).
        self.changelock = set()

        # When we visit an Assign node in the tree, the relevant variables are placed here. This
        # prevents unit transformations INSIDE re-assignment statements - they should only happen
        # after the re-assignment has been performed.
        self.assigning = []

        # A dictionary of purely local variables (those which only exist inside function scope)
        # and their units
        self.local_variables = {}

        super().__init__()

    def something_changed(self):
        self.did_anything_change = True

    def convert_node_units(self, node: ast.AST, to_units: UnitsContainer) -> ast.AST:
        # this takes in a node and returns a node that has been converted to the target units
        # the converted node will normally be a BinOp, multiplying or adding a conversion factor
        if node.units is UNASSIGNED or to_units is UNASSIGNED:
            return node

        cfactor = ureg._get_conversion_factor(node.units, to_units)

        if isinstance(cfactor, pint.DimensionalityError):
            raise cfactor

        if cfactor == 1:
            return node

        factor_node = ast.Constant(cfactor)
        factor_node.units = to_units / node.units

        operator_node = ast.Mult()
        operator_node.units = UNASSIGNED

        conversion_node = ast.BinOp(left=node, op=operator_node, right=factor_node)

        conversion_node.units = to_units

        return conversion_node

    def visit(self, node):
        # assign parents to each node
        for child in ast.iter_child_nodes(node):
            child.parent = node

        old_units = node.units
        to_return = super().visit(node)
        if (
            not hasattr(to_return, "units")
            or to_return.units != old_units
            or self.changelock
        ):
            self.something_changed()

        return to_return

    def visit_Module(self, node: ast.Module):
        # important because we will need to access the module later when running
        # load statements
        self._module = node
        return self.generic_visit(node)

    def visit_FunctionDef(self, node):
        if self.debug:
            stringappended = getattr(self, "_stringappended", False)
            if not stringappended:
                self._stringappended = True
                node.body.insert(
                    0,
                    ast.parse(f"print('INSIDE FUNCTION {self.func.__name__}')").body[0],
                )
                node.body[0] = ast.fix_missing_locations(
                    InitialLoadVisitor().visit(node.body[0])
                )
        return self.generic_visit(node)

    def visit_Name(self, node: ast.Name):
        if node.id not in self.changelock:
            if isinstance(node.ctx, ast.Load):
                # 1.a: nonlocal variables loaded to the function
                if node.id in self.func.__globals__:
                    # Restructure the tree to just be this load statement
                    # Module -> FunctionDef -> ... -> Name -> Load
                    # becomes
                    # Module -> Name -> Load
                    # and execute it, dumping the resultant globals dict into partialtree_globs
                    partialtree_globs = execute_partial_tree(
                        node, self._module, self.func.__globals__
                    )
                    loaded_var = partialtree_globs[node.id]

                    # Having now loaded the variable, we extract its units (if any) and
                    # apply them to the node (unchanged will leave UNASSIGNED there)
                    node.units = getattr(loaded_var, "units", node.units)

                # 1.b: arguments to the function
                elif (
                    is_function_unit_aware(self.func.__name__)
                    and node.id in get_unit_aware_function_info(self.func.__name__)[0]
                ):
                    node.units = get_unit_aware_function_info(self.func.__name__)[0][
                        node.id
                    ]

                # 1.c: a variable that only exists in local scope
                if node.id in self.local_variables:
                    # This finds Load nodes corresponding to previous Store nodes which
                    # stored unit information
                    if node.units is UNASSIGNED:
                        try:
                            node.units = self.local_variables[node.id]
                        except KeyError:
                            pass
                    # This overwrites nodes that already have units but are assigned a
                    # new value with Load.
                    else:
                        # Will not work inside a re-assignment statement (e.g. x = x.to('kg')),
                        # because only from outside this statement should the new units be applied.
                        if node.id not in self.assigning:
                            node.units = self.local_variables[node.id]

        return self.generic_visit(node)

    def visit_Subscript(self, node: ast.Subscript):

        # Handle case 2: Subscript -> Name     -> Load
        #                          -> Constant
        #                          -> Load

        # Some of this may have already been parsed by InitialLoadVisitor.visit_Name:
        # Subscript -> Name with <units> (if iterable is pQ(<iterable>, <units>))
        #           -> Constant
        #           -> Load
        if node.value.units is not UNASSIGNED:
            # in that case, just pass the units up the tree
            node.units = node.value.units
        # or
        # Subscript -> Name with UNASSIGNED (if iterable is anything else)
        #           -> Constant
        #           -> Load
        elif node.value.id in self.func.__globals__:
            # if this happens we have to keep going up the tree, compiling what's below it
            # and seeing if a valid unit assignment occurs. This is because the slice of a
            # subscript could be dynamically decided further upwards in the tree.

            _considered_node = node
            while not isinstance(_considered_node, ast.FunctionDef):
                try:
                    partialtree_globs = execute_partial_tree(
                        _considered_node, self._module, self.func.__globals__
                    )
                except:
                    _considered_node = _considered_node.parent
                else:
                    break
            else:
                raise RuntimeError(
                    f"No part of {self.func.__name__}'s AST could be parsed to get the units on {node.value}."
                )
            # While loop should be broken if a compatible execution was found.
            # If this is successful, we set the unit on the Name node representing the loaded variable
            loaded_var = partialtree_globs[node.value.id]
            node.units = getattr(loaded_var, "units", node.units)

        # The subscripted variable could also be an argument into the function, which would be given units
        elif node.value.id in get_unit_aware_function_info(self.func.__name__)[0]:
            ...
        # Otherwise the final option is that the variable is entirely local to the function.
        # In this case, it will have been assigned elsewhere.
        else:
            ...
        return self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute):
        # Handle case 3: Attribute -> Name -> Load
        #                          -> Load

        # The instance from which we are accessing an attribute may be dynamically
        # created elsewhere in the function. This means we need to do the same kind
        # of parsing as we did in visit_Subscript: keep parsing the function further
        # and further up the tree until a successful compilation occurs
        _considered_node = node
        while not isinstance(_considered_node, ast.FunctionDef):
            try:
                partialtree_globs = execute_partial_tree(
                    _considered_node, self._module, self.func.__globals__
                )
            except:
                _considered_node = _considered_node.parent
            else:
                break
        else:
            raise RuntimeError(
                f"No part of {self.func.__name__}'s AST could be parsed to get the units on {node.value}.{node.attr}."
            )
        # While loop should be broken if a compatible execution was found.
        # If this is successful, we set the unit on the Name node representing the loaded variable
        loaded_var = partialtree_globs[node.value.id]
        node.units = getattr(loaded_var, "units", node.units)

        return self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign):
        # We keep track of whether or not we are down-tree of an Assigment node.
        # This is so that any reassignments (e.g. x = x.to('kg')) do not propagate
        # unit changes inside the reassignment itself
        _targets = []
        # there can be multiple targets, e.g. with x = y = (1, 2)
        for t in node.targets:
            # within each target, we could have unpacking, e.g. with x, y = 1, 2
            if isinstance(t, (ast.List, ast.Tuple)):
                for elt in t.elts:
                    _targets.append(elt)
                    self.assigning.append(elt.id)
            # otherwise we deal with a single element assignment
            else:
                _targets.append(t)
                self.assigning.append(t.id)

        # This block gets the units on the right hand side of the assign statement
        # and then applies them to the left hand side
        for i in range(len(_targets)):
            t = _targets[i]
            if isinstance(node.value.units, list):
                u = node.value.units[i]
            else:
                # this should only happen if we get assignment to an iterable quantity, like a, b = pQ([5, 2], 'cm')
                u = node.value.units

            # here we set the target units to those retrieved by node.value
            if t.units != u:
                _targets[i].units = u
                self.local_variables[t.id] = t.units
                # lock changes for any NEW assignment, so that we have one more cycle for local variables to access
                # the newly changed units
                self.changelock.add(t.id)
            elif u is UNASSIGNED:
                pass

        """# applying these units is a little tricky due to possible mixtures of unpacked iterables and single variables
        # this applies them
        _target_counter = 0
        for i in range(len(node.targets)):
            if isinstance(t, (ast.List, ast.Tuple)):
                for j in range(len(node.targets[i].elts)):
                    node.targets[i].elts[j].units = _targets[_target_counter].units
                    _target_counter += 1
            # otherwise we deal with a single element assignment
            else:
                node.targets[i].units = _targets[_target_counter].units
                _target_counter += 1"""

        # Finally, we need to put the units on the Assign node
        node.units = node.value.units

        to_return = self.generic_visit(node)
        for i in range(len(_targets)):
            self.assigning.pop()
        return to_return

    def visit_Call(self, node: ast.Call):

        # This removes the @unit_aware decorator
        if isinstance(node.func, ast.Name) and node.func.id == "unit_aware":
            return

        # otherwise it's a function call
        else:
            # Handles case 4: 4) Call -> Name       -> Load
            #                         -> arg node 1
            #                         ...
            #                         -> arg node n

            # The function may be unit-aware itself: then we just take the output units
            if isinstance(node.func, ast.Name) and is_function_unit_aware(node.func.id):
                node.units = get_unit_aware_function_info(node.func.id)[1]

                # we also convert the input units to those accepted by the unit_aware_function
                units_to_func_as_list = list(
                    get_unit_aware_function_info(node.func.id)[0].values()
                )
                # TODO: check if this works with keyword arguments!!!
                for i, u in enumerate(units_to_func_as_list):
                    node.args[i] = self.convert_node_units(node.args[i], u)

            # otherwise it might be the to() function which also has assigned units
            elif isinstance(node.func, ast.Name) and node.func.id == "to":
                variable_to_convert_node = node.args[0]
                to_units = node.args[1].value
                if isinstance(to_units, str):
                    to_units = ureg.parse_units_as_container(to_units)
                new_node = self.convert_node_units(variable_to_convert_node, to_units)
                node = new_node

            # otherwise it may be something that returns units anyway, like a getter of unit-laden constants
            else:
                # NOTE: do we need to include the locals here?
                result_of_function = eval(
                    ast.unparse(node), self.func.__globals__, self.local_variables
                )
                # the result of the function might be unpackable, so we account for that case here
                try:
                    node.units = result_of_function.units
                except AttributeError:
                    node.units = [r.units for r in result_of_function]

        return self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant):
        # assign "dimensionless" to all constants
        if isinstance(node.value, Number):
            node.units = ureg.parse_units_as_container("dimensionless")
        return self.generic_visit(node)

    def visit_BinOp(self, node: ast.BinOp):
        # This will perform all necessary conversions at any binary operation nodes.
        # How to read comments:
        #   a, b      : operands
        #   [...]     : units of ...
        #   -> [...]  : return in units of ...

        ret_node = node

        # operation conversions that require a and b to have units:
        ua: UnitsContainer = node.left.units
        ub: UnitsContainer = node.right.units
        if ua is not UNASSIGNED and ub is not UNASSIGNED and node.units is UNASSIGNED:
            if isinstance(node.op, (ast.Add, ast.Sub)):
                # a +- b:    b to [a] -> [a]
                conv_right_node = self.convert_node_units(node.right, ua)
                ret_node = ast.BinOp(node.left, node.op, conv_right_node)
                ret_node.units = ua

            elif isinstance(node.op, ast.Mult):
                # a * b:    -> [a] * [b]
                ret_node.units = ua * ub

            elif isinstance(node.op, (ast.Div, ast.FloorDiv)):
                # a / b:    -> [a] / [b]
                ret_node.units = ua / ub

            # Pow does not need both inputs to have units, only the left-hand input
            elif isinstance(node.op, ast.Pow):
                # a ^ b:    -> [a] ^ b

                # b MUST be dimensionless
                if ureg.Unit(ub).dimensionless:
                    if ureg.Unit(ua).dimensionless:
                        # convert to true dimensionless (e.g. from % or permille)
                        new_left_node = self.convert_node_units(
                            node.left, UnitsContainer({})
                        )
                        ret_node.left = new_left_node
                        ret_node.units = UnitsContainer({})
                    else:
                        # If a is not dimensionless, b must be constant (otherwise the resultant unit could change depending on b)
                        # This means we should be able to evaluate the RHS as an expression involving only constants
                        try:
                            expfactor = eval(ast.unparse(node.right))
                            ret_node.units = ua**expfactor
                        except:
                            raise NameError(
                                "Non-constant exponent of non-dimensionless base detected in function"
                            )
                else:
                    raise NameError("Non-dimensionless exponent detected in function")

        # This blocks conversion if variable has been re-assigned on this pass,
        # giving the variables one more cycle to be updated before conversion
        if isinstance(node.right, ast.Name) and node.right.id in self.changelock:
            return self.generic_visit(node)
        if isinstance(node.left, ast.Name) and node.left.id in self.changelock:
            return self.generic_visit(node)

        return self.generic_visit(ret_node)

    def visit_Compare(self, node: ast.Compare):

        ret_node = node
        ua = node.left.units
        for i in range(len(ret_node.ops)):
            op = ret_node.ops[i]
            com = ret_node.comparators[i]
            ub = com.units
            if (
                isinstance(op, (ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE))
                and ua != ub
                and ua is not UNASSIGNED
                and ub is not UNASSIGNED
                and node.units is UNASSIGNED
            ):
                # a $ b:    b to [a] -> [a]
                # where $ ∈ {==, !=, <, <=, >, >=}
                new_comparator_node = self.convert_node_units(
                    ret_node.comparators[i], ua
                )
                ret_node.comparators[i] = new_comparator_node

        # This blocks conversion if variable has been re-assigned on this pass,
        # giving the variables one more cycle to be updated before conversion
        if isinstance(node.left, ast.Name) and node.left.id in self.changelock:
            return self.generic_visit(node)
        if any(
            isinstance(com, ast.Name) and com.id in self.changelock
            for com in node.comparators
        ):
            return self.generic_visit(node)

        return self.generic_visit(ret_node)

    def visit_Return(self, node: ast.Return):
        # this performs conversion according to units_out
        ret_node = node
        ur = node.value.units
        uo = get_unit_aware_function_info(self.func.__name__)[1]
        if ur != uo and ur is not UNASSIGNED:
            cfactor = ureg._get_conversion_factor(ur, uo)
            raise_error_if_invalid(cfactor)
            new_value_node = self.convert_node_units(node.value, uo)
            ret_node = ast.Return(new_value_node)
            ret_node.units = new_value_node.units

        # This blocks conversion if variable has been re-assigned on this pass,
        # giving the variables one more cycle to be updated before conversion
        if isinstance(node.value, ast.Name) and node.value.id in self.changelock:
            return self.generic_visit(node)

        return self.generic_visit(ret_node)
