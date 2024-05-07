"""
Title
=====

:class:`~marsilea.plotter.Title` is for adding a title to the plot.

"""

# %%
from marsilea.plotter import Title

# %%
import marsilea as ma
import numpy as np

data = np.random.randint(0, 10, (10, 2))

h = ma.Heatmap(data)
h.add_top(Title("Title"))
h.render()
