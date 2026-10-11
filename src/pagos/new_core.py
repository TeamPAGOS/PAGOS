import ast
import inspect
from collections.abc import Callable
from numbers import Number
from textwrap import dedent

import pint
from pint.util import UnitsContainer
from visast import visualise

ureg = pint.UnitRegistry()


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

        # Find the instances of when the function makes an assignment
        # from an external scope. These have to be artificially run
        # here so that the units associated with them can be recorded.
        _extern_assign_visitor = ExternalAssignmentVisitor()
        _extern_assign_visitor.visit(_ast)

        # Now these external assignments are unit-laden, we send a visitor
        # around the AST again, setting these units on any loading nodes
        # that access them.
        # Surgery is performed on nodes where unit conversions would occur.
        # Repeat until there are no more conversions.
        _unit_conv_transformer = UnitConversionTransformer(
            input_arguments_units, _extern_assign_visitor.ext_assigns, output_units
        )
        while True:
            # visualise.graph(_ast)
            _unit_conv_transformer.changelock = set()
            _unit_conv_transformer.did_anything_change = False
            _ast = ast.fix_missing_locations(_unit_conv_transformer.visit(_ast))
            if not _unit_conv_transformer.did_anything_change:
                break

        exec(ast.unparse(_ast), globals())

        # the above exec statement defines a function __unit_aware_function
        # this is what will actually be returned
        __unit_aware_function.default_units_in = default_units_in  # noqa: F821
        __unit_aware_function.units_out = units_out  # noqa: F821
        __unit_aware_function.ast = _ast  # noqa: F821
        return __unit_aware_function  # noqa: F821

    return _unit_aware


class ExternalAssignmentVisitor(ast.NodeVisitor):
    def __init__(self):
        self.ext_assigns = {}
        super().__init__()

    def visit_Module(self, node: ast.Module):
        self._module = node
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign):
        try:
            # We want to run the Assign statement, so that we can access what units are associated with the assignments
            body_with_only_assign_statement = [node]
            assign_tree = ast.Module(
                body_with_only_assign_statement, self._module.type_ignores
            )

            # execute the Assign statement. This allows us to find any constants
            _original_globals = set(globals())
            _globals = globals().copy()
            # this executes the assign statement, and the assigned variables are placed in self._globals
            exec(ast.unparse(assign_tree), _globals)
            newly_assigned_globals_set = set(_globals) - _original_globals
            assigned_quantities = {
                name: _globals[name] for name in newly_assigned_globals_set
            }
            # store unit information of local variables
            for target in node.targets:
                if isinstance(target, (ast.Tuple, ast.List)):
                    for elt in target.elts:
                        if elt.id in assigned_quantities:
                            elt.units = assigned_quantities[elt.id].units
                            self.ext_assigns[elt.id] = elt.units
                elif isinstance(target, ast.Name) and target.id in assigned_quantities:
                    if not hasattr(assigned_quantities[target.id], "units"):
                        # None is assigned to variables that do not have units.
                        # This is NOT the same as having 'dimensionless' as a unit.
                        target.units = None
                    else:
                        target.units = assigned_quantities[target.id].units
                    self.ext_assigns[target.id] = target.units

        except NameError:
            # NameError thrown when we are in an Assign statement involving function arguments rather than local variables
            # These are unimportant as their unit information is stored in the function decorator anyway
            pass

        self.generic_visit(node)


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
        self.did_anything_change = False
        self.changelock = set()
        self.local_variables = input_argument_units | external_assigns
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
            if not hasattr(node, "units"):
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
            # new value with Load. I'm not even sure this will ever be possible,
            # but I will print a debug message if it does get entered.
            else:
                old_units = node.units
                node.units = self.local_variables[node.id]
                if node.units != old_units:
                    self.something_changed()

        return self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign):
        # This is for internal variable assignment, where the variable is
        # entirely confined to local scope
        if hasattr(node.value, "units"):
            for i in range(len(node.targets)):
                t = node.targets[i]
                if not hasattr(t, "units") or t.units != node.value.units:
                    node.targets[i].units = node.value.units
                    self.local_variables[t.id] = t.units
                    self.something_changed()
                    self.changelock.add(t.id)
        else:
            for t in node.targets:
                self.changelock.add(t.id)

        return self.generic_visit(node)

    def visit_BinOp(self, node: ast.BinOp):
        # This will perform all necessary conversions at any binary operation nodes.
        # How to read comments:
        #   a, b      : operands
        #   [...]     : units of ...
        #   -> [...]  : return in units of ...

        ret_node = node

        # operation conversions that require a and b to have units:
        try:
            ua = node.left.units
            ub = node.right.units
            if isinstance(node.op, (ast.Add, ast.Sub)) and not hasattr(node, "units"):
                # a +- b:    b to [a] -> [a]
                cfactor = ureg._get_conversion_factor(ub, ua)
                raise_error_if_invalid(cfactor)

                transplanted_node = generate_conv_node(node.right, cfactor, ua, ub)

                ret_node = ast.BinOp(node.left, node.op, transplanted_node)
                ret_node.units = ua
                self.something_changed()

            elif isinstance(node.op, ast.Mult) and not hasattr(node, "units"):
                # a * b:    -> [a] * [b]
                ret_node.units = ua * ub
                self.something_changed()

            elif isinstance(node.op, (ast.Div, ast.FloorDiv)) and not hasattr(
                node, "units"
            ):
                # a / b:    -> [a] / [b]
                ret_node.units = ua / ub
                self.something_changed()

        except AttributeError:
            # AttributeError if units are not found on both nodes
            pass

        # Pow does not need both inputs to have units, only the left-hand input
        if isinstance(node.op, ast.Pow) and not hasattr(node, "units"):
            # a ^ b:    -> [a] ^ b
            try:
                ua = node.left.units
                b = node.right.value

                ret_node.units = ua**b
                self.something_changed()

            except AttributeError:
                # AttributeError if units are not found on the left-hand side
                pass

        # This blocks conversion if variable has been re-assigned on this pass,
        # giving the variables one more cycle to be updated before conversion
        if isinstance(node.right, ast.Name) and node.right.id in self.changelock:
            return self.generic_visit(node)
        if isinstance(node.left, ast.Name) and node.left.id in self.changelock:
            return self.generic_visit(node)

        return self.generic_visit(ret_node)

    def visit_Compare(self, node: ast.Compare):

        ret_node = node

        try:
            ua = node.left.units

            for i in range(len(ret_node.ops)):
                op = ret_node.ops[i]
                com = ret_node.comparators[i]
                try:
                    ub = com.units
                    if (
                        isinstance(
                            op, (ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE)
                        )
                        and ub != ua
                    ):
                        # a $ b:    b to [a] -> [a]
                        # where $ ∈ {==, !=, <, <=, >, >=}
                        cfactor = ureg._get_conversion_factor(ub, ua)
                        raise_error_if_invalid(cfactor)

                        transplanted_node = generate_conv_node(com, cfactor, ua, ub)
                        ret_node.comparators[i] = transplanted_node
                        self.something_changed()

                except AttributeError:
                    # AttributeError if units are not found on the right-hand nodes
                    pass
        except AttributeError:
            # AttributeError if units are not found on the left-hand node
            pass

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

        if hasattr(node.value, "units"):
            ur = node.value.units
            uo = self.output_units
            if ur != uo:
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
            try:
                ui = node.func.value.units
                uo = ureg.parse_units_as_container(node.args[0].value)
                if not hasattr(node, "units"):
                    # i.to(o):     i to [o] -> [o]
                    cfactor = ureg._get_conversion_factor(ui, uo)
                    raise_error_if_invalid(cfactor)

                    transplanted_node = generate_conv_node(
                        node.func.value, cfactor, uo, ui
                    )
                    ret_node = transplanted_node
                    ret_node.units = uo
                    self.something_changed()
            except AttributeError:
                pass
        return self.generic_visit(ret_node)


if __name__ == "__main__":

    @unit_aware({"a": "kg", "b": "g"}, "kg")
    def myfunc(a, b):
        b = b.to("kg")
        return a + b

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
