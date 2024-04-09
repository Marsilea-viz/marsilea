"""
Ordering Legends
================

This example demonstrates how to order legends in a plot.

"""

# %%
import numpy as np
import marsilea as ma
from marsilea.plotter import ColorMesh, Colors

data = np.random.randint(0, 10, (10, 10))


# %%

h = ma.Heatmap(data, width=3, height=3)
h.add_left(ColorMesh(data[0]), name="Plot 1")
h.add_left(Colors(np.random.choice(["red", "blue", "green"], 10)), name="Plot 2")
h.add_legends(order=["Plot 2", "Plot 1"])
h.render()

