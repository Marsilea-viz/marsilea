"""
Boxen
=====

:class:`~marsilea.plotter.Boxen` is a wrapper for seaborn's boxenplot.

"""

# %%
from marsilea.plotter import Boxen

# %%
import numpy as np
import matplotlib.pyplot as plt

_, ax = plt.subplots()
data = np.random.randint(0, 10, (10, 10))
Boxen(data).render(ax)
