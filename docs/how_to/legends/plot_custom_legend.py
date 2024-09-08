"""
Ordering Legends
================

To add custom legend to the plot, first define
a function that returns the legend object. Then
pass it to the :code:`custom_legend` method.

"""

# %%
import numpy as np

import marsilea as ma

data = np.random.randint(0, 10, (10, 10))


# %%
from legendkit import cat_legend


def my_legend():
    return cat_legend(
        labels=["my super legend"], colors=["lightblue"], title="My Legend"
    )


h = ma.Heatmap(data, width=3, height=3)
h.custom_legend(my_legend)
h.add_legends()
h.render()
