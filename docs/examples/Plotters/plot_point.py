"""
Point
=====

:class:`~marsilea.plotter.Point` is a wrapper for seaborn's pointplot.

"""

# %%
from marsilea.plotter import Point

# %%
import numpy as np
import matplotlib.pyplot as plt

_, ax = plt.subplots()
data = np.random.randint(0, 10, (10, 10))
Point(data).render(ax)
