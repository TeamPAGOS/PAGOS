import inspect

from visast import visualise
import ast
from pagos import visast_util
from pagos.new_core import unit_aware

visualise.graph = visast_util.graph

external_var = 1
external_list = [1, 2]
external_dict = {"a": 1, "b": 2, "c": 3}
external_nested = [[1, 2], [3, 4]]


def ext_func(arg):
    return arg + external_var


class ExtClass:
    def __init__(self):
        self.property = 4

    def return_property(self):
        return self.property


external_obj = ExtClass()


@unit_aware({"arg1": "mm", "arg2": "m"}, "m")
def my_function(arg1, arg2):
    local_var1 = external_var
    local_var2 = external_list[1]
    local_var3 = external_dict["c"]
    local_var4 = external_obj.property

    # non-assignment statement inside assignment
    # important to look at internal non-assignment statement
    local_var5 = external_var + external_obj.property
    local_var6 = external_obj.return_property()
    local_var7 = ext_func(arg1, arg2)

    local_var8, localvar9 = external_list

    local_var10 = external_nested[1]

    local_var11 = local_var10[0]

    for i in range(2):
        for j in range(2):
            local_var12 = external_nested[i][j]

    # non-assignment in control flow
    if external_var:
        local_var13 = external_var
    else:
        local_var13 = external_list[0]


_ast = ast.parse(inspect.getsource(my_function))
visualise.graph(_ast)
