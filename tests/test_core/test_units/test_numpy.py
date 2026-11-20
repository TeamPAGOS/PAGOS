from pagos.new_core import unit_aware
from pagos.new_units import pQ
import numpy as np
from pagos.visast_util import visualise


@unit_aware({"x": "dimensionless", "y": "cm"}, units_out="dimensionless")
def my_numpy_function(x, y):
    z = np.log(x)
    return z


visualise.graph(my_numpy_function.ast)
