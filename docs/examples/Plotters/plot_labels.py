"""
Labels
======

:class:`~marsilea.plotter.Labels` is to draw text labels on the plot.

"""

# %%
from marsilea.plotter import Labels

# %%
import numpy as np
import matplotlib.pyplot as plt

_, ax = plt.subplots(figsize=(.5, 6))
data = np.random.randint(0, 10, 30)
l = Labels(data)
l.set_side('right')
l.render(ax)
