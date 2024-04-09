"""
Swarm
=====

:class:`~marsilea.plotter.Swarm` is a wrapper for seaborn's swarmplot.

"""

# %%
from marsilea.plotter import Swarm

# %%
import numpy as np
import matplotlib.pyplot as plt

_, ax = plt.subplots()
data = np.random.rand(50, 10)
Swarm(data).render(ax)
