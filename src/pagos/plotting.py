"""
Plotting functionality in PAGOS.
"""

from pagos import u
from uncertainties.core import Variable, AffineScalarFunc
from collections.abc import Iterable
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def make_plots(main_data:pd.DataFrame, to_plot:list|pd.DataFrame, y_data_label:str='Depth', custom_colors:list=None, **kwargs):
    """Make Matplotlib plots showing comprehensive gas exchange data.

    :param main_data: Pandas DataFrame with all necessary data.
    :type main_data: DataFrame
    :param to_plot: List of column headings in `main_data` whose entries should be plotted, or separate DataFrame containing these columns.
    :type to_plot: list | DataFrame
    :param y_data_label: y-axis against which to plot all data, defaults to 'Depth'
    :type y_data_label: str, optional
    :param custom_colors: array of colours corresponding to each point, defaults to None
    :type custom_colors: list, optional
    """    
    # handling to_plot argument being either a DataFrame or column headings of the main_data DataFrame
    if type(to_plot) != pd.DataFrame:
        if isinstance(to_plot, Iterable):
            to_plot = main_data[to_plot]
        else:
            raise ValueError('to_plot argument must either be a separate DataFrame to main_data, or a list of column headings in main_data.')
    
    paramnames = to_plot.columns.values
    nsubplots = len(to_plot.columns.values)
    fig, axs = plt.subplots(1, nsubplots, sharey=True)

    # whole-plot keyword argument handling
    if kwargs is not None:
        for k in kwargs.keys():
            if k == 'title':
                fig.suptitle(kwargs[k])

    # per-axis keyword argument handling
    # TODO there has got to be a more efficient way of writing this!
    for k in kwargs.keys():
        for i, n in enumerate(paramnames):
            if type(kwargs[k]) == dict:
                if n in kwargs[k].keys():
                    if k == 'xlim':
                        axs[i].set_xlim(kwargs[k][n])
                    if k == 'grid':
                        if kwargs[k][n] == True:
                            axs[i].grid()
            else:
                if k == 'xlim':
                    axs[i].set_xlim(kwargs[k])
                if k == 'grid':
                    if kwargs[k] == True:
                        axs[i].grid()
            

    for i, v in enumerate(paramnames):  # for each column/parameter
        for j, q in enumerate(to_plot[v]):  # for each entry
            if q is None or q is np.nan:
                pass
            # parse and plot data
            else:
                if (isinstance(q, u.Quantity) and isinstance(q.magnitude, (Variable, AffineScalarFunc))) or isinstance(q, (Variable, AffineScalarFunc)):
                    x = q.nominal_value
                    xerr = q.std_dev
                elif isinstance(q, u.Quantity):
                    x = q.magnitude
                    xerr = 0
                else:
                    x = q
                    xerr = 0
                y = main_data[y_data_label][j]

                if custom_colors is not None:
                    c = custom_colors[j]
                else:
                    c = 'blue'

                axs[i].errorbar(x, y, xerr=xerr, fmt='.', capsize=2, color=c) 
        # format(..., '~') here changes the display of units from 'gram / cubic_centimeter' to 'g / cc'  
        display_unit = str(format(to_plot[v][0].units, '~')) # TODO this could be bad if somehow the array has different units for different entries. To look at later...
        # TODO the above currently takes the long form of the unit - can we shorten it?
        axs[i].set_xlabel(v + ' [' + display_unit + ']')

    plt.show()