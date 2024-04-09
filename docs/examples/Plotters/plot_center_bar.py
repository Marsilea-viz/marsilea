"""
CenterBar
=========

:class:`~marsilea.plotter.CenterBar` is for comparing two groups of 1d data.

"""

# %%
from marsilea.plotter import CenterBar

# %%
import numpy as np
import matplotlib.pyplot as plt

_, ax = plt.subplots()
data = np.random.randint(0, 10, (10, 2))

CenterBar(data, ["D1", "D2"]).render(ax)
