import ast
import inspect
from collections.abc import Callable
from numbers import Number, Real
from textwrap import dedent

import pint
from pint.util import UnitsContainer
from visast import visualise

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


def unit_aware(default_units_in: dict | None, units_out: str | None):
    def _unit_aware(func: Callable):

        input_arguments_units = {
            k: None if u is None else ureg.parse_units_as_container(u)
            for k, u in default_units_in.items()
        }
        output_units = (
            None if units_out is None else ureg.parse_units_as_container(units_out)
        )

        # get AST of func (dedent used so that functions defined inside other
        # functions do not have invalid whitespace at the beginning)
        _ast = ast.parse(dedent(inspect.getsource(func)))
        visualise.graph(_ast)

        # Find the instances of when the function makes an assignment
        # from an external scope. These have to be artificially run
        # here so that the units associated with them can be recorded.
        _extern_assign_visitor = ExternalAssignmentVisitor(func)
        _ast = ast.fix_missing_locations(_extern_assign_visitor.visit(_ast))

        # Now these external assignments are unit-laden, we send a visitor
        # around the AST again, setting these units on any loading nodes
        # that access them.
        # Surgery is performed on nodes where unit conversions would occur.
        # Repeat until there are no more conversions.
        _unit_conv_transformer = UnitConversionTransformer(
            input_arguments_units, _extern_assign_visitor.ext_assigns, output_units
        )
        c = 0
        while True:
            # visualise.graph(_ast)
            print(c)
            _unit_conv_transformer.changelock = set()
            _unit_conv_transformer.did_anything_change = False
            _ast = ast.fix_missing_locations(_unit_conv_transformer.visit(_ast))
            if not _unit_conv_transformer.did_anything_change:
                break
            c += 1

        exec(ast.unparse(_ast), globals())
        __unit_aware_function.ast = _ast  # noqa: F821
        __unit_aware_function.__globals__.update(func.__globals__)  # noqa: F821

        return __unit_aware_function  # noqa: F821

    return _unit_aware


UNASSIGNED = object()


class ExternalAssignmentVisitor(ast.NodeTransformer):
    def __init__(self, func: Callable):
        self.func = func
        self.ext_assigns = {}
        super().__init__()

    # This initialises units on the nodes.
    # Literal nodes will be assigned "dimensionless", while other nodes
    # will be given a sentinel value.
    def generic_visit(self, node):
        if isinstance(node, ast.Constant):
            node.units = ureg.parse_units_as_container("dimensionless")
        # we might have applied units via visit_Assign. Otherwise, assign UNASSIGNED sentinel
        elif not hasattr(node, "units"):
            node.units = UNASSIGNED
        return super().generic_visit(node)

    def visit_Module(self, node: ast.Module):
        self._module = node
        return self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign):
        try:
            # We want to run the Assign statement, so that we can access what units are associated with the assignments
            body_with_only_assign_statement = [node]
            assign_tree = ast.Module(
                body_with_only_assign_statement, self._module.type_ignores
            )

            # execute the Assign statement. This allows us to find any constants
            _globals_from_func = self.func.__globals__
            _original_globals = set(_globals_from_func)
            # this executes the assign statement, and the assigned variables are placed in self._globals
            exec(ast.unparse(assign_tree), _globals_from_func)
            newly_assigned_globals_set = set(_globals_from_func) - _original_globals
            # these are the variables that are assigned from external scope
            assigned_quantities = {
                name: _globals_from_func[name] for name in newly_assigned_globals_set
            }

            # store unit information of local variables
            target0 = node.targets[0]
            RHS_units_list = []
            # deal with unpacked assignment
            if isinstance(target0, (ast.Tuple, ast.List)):
                # changes a, b, c = some_collection
                # to a, b, c = [_v.value if isinstance(_v, PAGOSQuantity) else _v for _v in some_collection]
                comprehension_tree = (
                    ast.parse(
                        "[_v.value if isinstance(_v, PAGOSQuantity) else _v for _v in "
                        + ast.unparse(node.value)
                        + "]",
                    )
                    .body[0]
                    .value
                )
                node.value = comprehension_tree

                # get units of externally assigned local variables
                for elt in target0.elts:
                    if elt.id in assigned_quantities:
                        elt.units = assigned_quantities[elt.id].units

                        self.ext_assigns[elt.id] = elt.units
                    RHS_units_list.append(elt.units)

            # otherwise just a single assignment
            else:
                # changes var = thing
                # to var = thing.value if isinstance(thing, PAGOSQuantity) else thing
                value_access_tree = (
                    ast.parse(
                        ast.unparse(node.value)
                        + ".value if isinstance("
                        + ast.unparse(node.value)
                        + ", PAGOSQuantity) else "
                        + ast.unparse(node.value)
                    )
                    .body[0]
                    .value
                )
                node.value = value_access_tree

                if not hasattr(assigned_quantities[target0.id], "units"):
                    # None is assigned to variables that do not have units.
                    # This is NOT the same as having 'dimensionless' as a unit.
                    target0.units = None
                else:
                    target0.units = assigned_quantities[target0.id].units
                self.ext_assigns[target0.id] = target0.units
                RHS_units_list.append(target0.units)

            node.value.units = RHS_units_list

            # deals with any simultaneous assignment (a = b = c etc.)
            for target in node.targets[1:]:
                if isinstance(target, (ast.Tuple, ast.List)):
                    for i in range(len(target.elts)):
                        target.elts[i] = target0.elts[i].units
                else:
                    target.units = target0.units

        except NameError:
            # NameError thrown when we are in an Assign statement involving function arguments rather than local variables
            # These are unimportant as their unit information is stored in the function decorator anyway
            pass

        return self.generic_visit(node)


def generate_conv_node(
    node_in: ast.AST,
    factor: Number,
    original_to: UnitsContainer,
    original_from: UnitsContainer,
):
    if factor == 1:
        return node_in
    factor_node = ast.Constant(factor)
    factor_node.units = original_to / original_from

    conversion_node = ast.BinOp(left=node_in, op=ast.Mult(), right=factor_node)
    conversion_node.units = original_to

    return conversion_node


def raise_error_if_invalid(obj):
    if isinstance(obj, pint.DimensionalityError):
        raise obj


class UnitConversionTransformer(ast.NodeTransformer):
    def __init__(
        self,
        input_argument_units: dict[str, UnitsContainer],
        external_assigns: dict[str, UnitsContainer],
        output_units: UnitsContainer,
    ):
        # If this is True, at least one more pass of visit() will be performed on the whole tree.
        self.did_anything_change = False

        # If variables are re-assigned, they are put here. This ensures unit transformations are
        # not prematurely performed BEFORE re-assignment.
        self.changelock = set()

        # When we visit an Assign node in the tree, the relevant variables are placed here. This
        # prevents unit transformations INSIDE re-assignment statements - they should only happen
        # after the re-assignment has been performed.
        self.assigning = []

        # Dictionary of local variables to the function and their units.
        self.local_variables = input_argument_units | external_assigns

        # Output units of the function.
        self.output_units = output_units
        super().__init__()

    def something_changed(self):
        self.did_anything_change = True

    def visit_FunctionDef(self, node: ast.FunctionDef):
        # Changes name of function to that which we will access later
        node.name = "__unit_aware_function"
        return self.generic_visit(node)

    def visit_Name(self, node: ast.Name):
        if node.id in self.local_variables:
            # This finds Load nodes corresponding to previous Store nodes which
            # stored unit information
            if node.units is UNASSIGNED:
                try:
                    node.units = self.local_variables[node.id]
                    self.something_changed()
                except KeyError:
                    try:
                        node.units = self.in_arg_units[node.id]
                        self.something_changed()
                    except KeyError:
                        pass
            # This overwrites nodes that already have units but are assigned a
            # new value with Load.
            else:
                # Will not work inside a re-assignment statement (e.g. x = x.to('kg')),
                # because only from outside this statement should the new units be applied.
                if node.id not in self.assigning:
                    old_units = node.units
                    node.units = self.local_variables[node.id]
                    if node.units != old_units:
                        self.something_changed()

        return self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign):
        # This is for internal variable assignment, where the variable is
        # entirely confined to local scope

        # We keep track of whether or not we are down-tree of an Assigment node.
        # This is so that any reassignments (e.g. x = x.to('kg')) do not propagate
        # unit changes inside the reassignment itself
        _targets = []
        for t in node.targets:
            if isinstance(t, (ast.List, ast.Tuple)):
                for elt in t.elts:
                    _targets.append(elt)
                    self.assigning.append(elt.id)
            else:
                _targets.append(t)
                self.assigning.append(t.id)

        for i in range(len(_targets)):
            t = _targets[i]
            if isinstance(node.value.units, list):
                u = node.value.units[i]
            else:
                u = node.value.units
            if t.units != u:
                _targets[i].units = u
                self.local_variables[t.id] = t.units
                self.something_changed()
                self.changelock.add(t.id)
            elif u is UNASSIGNED:
                self.something_changed()
                self.changelock.add(t.id)

        to_return = self.generic_visit(node)
        for i in range(len(_targets)):
            self.assigning.pop()
        return to_return

    def visit_BinOp(self, node: ast.BinOp):
        # This will perform all necessary conversions at any binary operation nodes.
        # How to read comments:
        #   a, b      : operands
        #   [...]     : units of ...
        #   -> [...]  : return in units of ...

        ret_node = node

        original_units = node.units

        # operation conversions that require a and b to have units:
        ua: UnitsContainer = node.left.units
        ub: UnitsContainer = node.right.units
        if ua is not UNASSIGNED and ub is not UNASSIGNED:
            if isinstance(node.op, (ast.Add, ast.Sub)):
                # a +- b:    b to [a] -> [a]
                cfactor = ureg._get_conversion_factor(ub, ua)
                raise_error_if_invalid(cfactor)

                transplanted_node = generate_conv_node(node.right, cfactor, ua, ub)

                ret_node = ast.BinOp(node.left, node.op, transplanted_node)
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
                        cfactor = ureg._get_conversion_factor(ua, UnitsContainer({}))
                        raise_error_if_invalid(cfactor)
                        transplanted_node = generate_conv_node(
                            node.left, cfactor, UnitsContainer({}), ua
                        )
                        ret_node.left = transplanted_node
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

        # if a change occurs, we want the traversal loop to happen at least once more
        if original_units != ret_node.units:
            self.something_changed()

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
            ):
                # a $ b:    b to [a] -> [a]
                # where $ ∈ {==, !=, <, <=, >, >=}
                cfactor = ureg._get_conversion_factor(ub, ua)
                raise_error_if_invalid(cfactor)

                transplanted_node = generate_conv_node(com, cfactor, ua, ub)
                ret_node.comparators[i] = transplanted_node
                self.something_changed()

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
        uo = self.output_units
        if ur != uo and ur is not UNASSIGNED:
            cfactor = ureg._get_conversion_factor(ur, uo)
            raise_error_if_invalid(cfactor)

            transplanted_node = generate_conv_node(node.value, cfactor, uo, ur)

            ret_node = ast.Return(transplanted_node)
            self.something_changed()

        # This blocks conversion if variable has been re-assigned on this pass,
        # giving the variables one more cycle to be updated before conversion
        if isinstance(node.value, ast.Name) and node.value.id in self.changelock:
            return self.generic_visit(node)

        return self.generic_visit(ret_node)

    def visit_Call(self, node: ast.Call):
        # this removes the decorator
        ret_node = node
        if isinstance(node.func, ast.Name) and node.func.id == "unit_aware":
            return
        # this finds instances of to()
        elif isinstance(node.func, ast.Attribute) and node.func.attr == "to":
            ui = node.func.value.units
            uo = ureg.parse_units_as_container(node.args[0].value)
            if node.units is UNASSIGNED and ui is not UNASSIGNED:
                # i.to(o):     i to [o] -> [o]
                cfactor = ureg._get_conversion_factor(ui, uo)
                raise_error_if_invalid(cfactor)

                transplanted_node = generate_conv_node(node.func.value, cfactor, uo, ui)
                ret_node = transplanted_node
                ret_node.units = uo
                self.something_changed()
        return self.generic_visit(ret_node)


if __name__ == "__main__":

    @unit_aware({"a": "kg", "b": "g"}, "kg")
    def myfunc(a, b):
        b = b.to("kg")
        a = a.to("g")
        c = 2 * a - b
        return a + b + c

    @unit_aware({"a": "m", "b": "s^-1"}, "km/hr")
    def myfunc2(a, b):
        return a * b

    @unit_aware({"a": "m", "b": "mm", "c": "cm"}, None)
    def myfunc3(a, b, c):
        return a <= b < c

    @unit_aware({"a": "N", "b": "g*cm", "c": "hr^2"}, "kN^2")
    def myfunc4(a, b, c):
        d = a - b / c
        e = d**2
        if a < d:
            return e
        else:
            return a**2

    print(myfunc)
    visualise.graph(myfunc.ast)
    print(myfunc(1, 2))

    print(myfunc2)
    visualise.graph(myfunc2.ast)
    print(myfunc2(1, 2))

    print(myfunc3)
    visualise.graph(myfunc3.ast)
    print(myfunc3(1, 2, 3))

    print(myfunc4)
    visualise.graph(myfunc4.ast)
    print(myfunc4(1, 2, 3))


a, b, c = d = (1, 2, 3)
