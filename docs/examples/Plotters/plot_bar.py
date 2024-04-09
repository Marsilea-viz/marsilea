"""
Bar
===

:class:`~marsilea.plotter.Bar` is a wrapper for seaborn's barplot.

"""

# %%
from marsilea.plotter import Bar

# %%
import numpy as np
import matplotlib.pyplot as plt

_, ax = plt.subplots()
data = np.random.randint(0, 10, (10, 10))
Bar(data).render(ax)
