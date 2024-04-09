"""
Box
===

:class:`~marsilea.plotter.Box` is a wrapper for seaborn's boxplot.

"""

# %%
from marsilea.plotter import Box

# %%
import numpy as np
import matplotlib.pyplot as plt

_, ax = plt.subplots()
data = np.random.randint(0, 10, (10, 10))
Box(data).render(ax)
