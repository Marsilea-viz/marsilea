"""
Strip
=====

:class:`~marsilea.plotter.Strip` is a wrapper for seaborn's stripplot.

"""

# %%
from marsilea.plotter import Strip

# %%
import numpy as np
import matplotlib.pyplot as plt

_, ax = plt.subplots()
data = np.random.rand(50, 10)
Strip(data).render(ax)
