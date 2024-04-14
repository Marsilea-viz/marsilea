"""
Area
====

:class:`~marsilea.plotter.Area` is a plotter for drawing area plot.

"""

# %%
from marsilea.plotter import Area

# %%
import numpy as np
import matplotlib.pyplot as plt

_, ax = plt.subplots()
data = np.random.randint(0, 10, 10) + 1
Area(data).render(ax)
