import ast

from visast import visualise

from pagos.core import REGISTERED_UNIT_AWARE_FUNCTIONS, PAGOSQuantity, ccreg

registered_ASTs = [
    REGISTERED_UNIT_AWARE_FUNCTIONS[key][3].body[0]
    for key in REGISTERED_UNIT_AWARE_FUNCTIONS
]


class LocalVariableVisitor(ast.NodeVisitor):
    def __init__(self):
        self.reg_func_name: str | None = None
        self._globals: dict = {}
        self.local_variables = {}
        self._seen = set()
        self._module = None

    def visit_FunctionDef(self, node: ast.FunctionDef):
        if node in registered_ASTs and not self.reg_func_name:
            self.reg_func_name = node.name
            self._func_arguments = REGISTERED_UNIT_AWARE_FUNCTIONS[self.reg_func_name][
                0
            ]
            self._globals = REGISTERED_UNIT_AWARE_FUNCTIONS[self.reg_func_name][4]

        self.generic_visit(node)

    def visit_Module(self, node):
        self._module = node
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign):
        # run only the Assign statement, so that we can access what units are associated with the assignments
        body_with_only_assign_statement = [node]
        assign_tree = ast.Module(
            body_with_only_assign_statement, self._module.type_ignores
        )
        # visualise.graph(assign_tree)
        try:
            original_globals_set = set(self._globals)
            # this executes the assign statement, and the assigned variables are placed in self._globals
            exec(ast.unparse(assign_tree), self._globals)
            newly_assigned_globals_set = set(self._globals) - original_globals_set
            added_globals = {
                name: self._globals[name] for name in newly_assigned_globals_set
            }
            # store unit information of local variables
            # NOTE: by passing the assign_tree into exec(), we added entries the GLOBAL variables,
            #       but these entries that were added ARE the LOCAL variables of the function.
            #       So that can get confusing!
            for name in added_globals:  # noqa: PLC0206
                if isinstance(added_globals[name], PAGOSQuantity):
                    self.local_variables[name] = added_globals[name].units
                else:
                    self.local_variables[name] = None

            # reset _globals to actual __globals__ of the function
            self._globals = {
                k: self._globals[k] for k in self._globals if k in original_globals_set
            }

        except NameError:
            for target in node.targets:
                if target.id in self._func_arguments:
                    pass
                else:
                    ...
            # NameError thrown when we are in an Assign statement involving function arguments rather than local variables
            # These are unimportant as their unit information is stored in the function decorator anyway
        self.generic_visit(node)


class NodeUnitAssigner(ast.NodeVisitor):
    def __init__(self, local_variables={}):
        self.reg_func_name: str | None = None
        self.unitsdict: dict = {}
        self.local_variables = local_variables

    def visit_FunctionDef(self, node: ast.FunctionDef):
        if node in registered_ASTs and not self.reg_func_name:
            self.reg_func_name = node.name
            self.unitsdict = REGISTERED_UNIT_AWARE_FUNCTIONS[self.reg_func_name][0]

        return self.generic_visit(node)

    def visit_Name(self, node: ast.Name):
        if isinstance(node.ctx, ast.Load):
            if node.id in self.local_variables:
                node.units = self.local_variables[node.id]
                print("FOUND UNITS FOR", node.id, "--", node.units)
            elif node.id in self.unitsdict:
                node.units = self.unitsdict[node.id]
                print("FOUND UNITS FOR", node.id, "--", node.units)


def generate_conv_node(node_in: ast.AST, op: ast.AST, factor: ast.Constant):
    conversion_node = ast.BinOp(left=node_in, op=op, right=ast.Constant(factor))
    conversion_node.units = node_in.left.units
    return conversion_node


class UnitConversionTransformer(ast.NodeTransformer):
    def __init__(self, local_variables={}):
        self.reg_func_name: str | None = None
        self.unitsdict: dict = {}
        self.local_variables = local_variables
        self.did_anything_change = False

    def visit_FunctionDef(self, node: ast.FunctionDef):
        if node in registered_ASTs and not self.reg_func_name:
            self.reg_func_name = node.name
            self.unitsdict = REGISTERED_UNIT_AWARE_FUNCTIONS[self.reg_func_name][0]

        return self.generic_visit(node)

    def visit_Name(self, node: ast.Name):
        if node.id in self.local_variables:
            if not hasattr(node, "units"):
                node.units = self.local_variables[node.id]
                self.did_anything_change = True
            else:
                old_units = node.units
                node.units = self.local_variables[node.id]
                if node.units != old_units:
                    self.did_anything_change = True
        return self.generic_visit(node)

    def visit_BinOp(self, node: ast.BinOp):

        ret_node = node

        if isinstance(node.op, ast.Add):
            print(node.left, "+", node.right)
            if not hasattr(node, "units"):
                # a + b:    b to [a] -> [a]
                try:
                    ua = node.left.units
                    ub = node.right.units
                    cfactor = ccreg._get_conversion_factor(ub, ua)

                    transplanted_node = generate_conv_node(
                        node.right, ast.Mult(), ast._ConstantValue(cfactor)
                    )
                    print(f"TRANSPLANTED {ua} + {ub} WITH {ua} + {ub} * {cfactor}")

                    ret_node = ast.BinOp(node.left, node.op, transplanted_node)
                    ret_node.units = ua
                    self.did_anything_change = True
                except AttributeError:
                    pass

        if isinstance(node.op, ast.Mult):
            print(node.left, "*", node.right)
            if not hasattr(node, "units"):
                # a * b:    -> [a] * [b]
                try:
                    ua = node.left.units
                    ub = node.right.units

                    ret_node.units = ua * ub
                    print(f"MULTIPLIED {ua} * {ub} TO {ua * ub}")
                    self.did_anything_change = True

                except AttributeError:
                    pass

        if isinstance(node.op, ast.Pow):
            print(node.left, "^", node.right)
            if not hasattr(node, "units"):
                # a ^ b:    -> [a] ^ b
                try:
                    ua = node.left.units
                    b = node.right.value

                    node.units = ua**b
                    print(f"POWERED {ua} & {b} TO {ua**b}")
                    self.did_anything_change = True

                except AttributeError:
                    pass

        return self.generic_visit(ret_node)

    def visit_Assign(self, node: ast.Assign):
        if hasattr(node.value, "units"):
            for t in node.targets:
                if not hasattr(t, "units"):
                    t.units = node.value.units
                    self.local_variables[t.id] = t.units
                    self.did_anything_change = True
        return self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id == "unit_aware":
            return
        return self.generic_visit(node)

    """def visit_Return(self, node: ast.Return):
        pass"""


_ast = REGISTERED_UNIT_AWARE_FUNCTIONS["calc_dens"][3]
visualise.graph(_ast)


local_variable_visitor = LocalVariableVisitor()
local_variable_visitor.visit(_ast)

node_unit_assigner = NodeUnitAssigner(local_variable_visitor.local_variables)
node_unit_assigner.visit(_ast)

unit_conversion_transformer = UnitConversionTransformer(
    local_variable_visitor.local_variables
)

i = 0
while True:
    i += 1
    print("PASS", i)
    unit_conversion_transformer.did_anything_change = False
    _ast = ast.fix_missing_locations(unit_conversion_transformer.visit(_ast))
    if not unit_conversion_transformer.did_anything_change:
        break
    # visualise.graph(_ast)

print(unit_conversion_transformer.local_variables)

visualise.graph(_ast)

print(ast.unparse(_ast))
exec(ast.unparse(_ast), globals())
