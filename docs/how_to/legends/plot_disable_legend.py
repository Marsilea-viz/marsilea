"""
Disabling the legend of a plot
==============================

This example demonstrates how to disable the legend of a plot.

"""

# %%
import numpy as np
import marsilea as ma

data = np.random.randint(0, 10, (10, 10))

# %%
# By default, the legend is enabled.

h = ma.Heatmap(data, width=3, height=3, label="Main canvas")
h.add_left(ma.plotter.ColorMesh(data[0], cmap="Greens", label="Close Legend"))
h.add_legends()
h.render()

# %%
# To disable the legend, set the :code:`legend` parameter to `False`.

h = ma.Heatmap(data, width=3, height=3, label="Main canvas")
h.add_left(ma.plotter.ColorMesh(data[0], cmap="Greens"), legend=False)
h.add_legends()
h.render()
