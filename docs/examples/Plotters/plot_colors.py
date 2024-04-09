"""
Colors
======

:class:`~marsilea.plotter.Colors` is a plotter that displays a categorical array.

"""

# %%

from marsilea.plotter import Colors

# %%
import numpy as np
import matplotlib.pyplot as plt

data = np.random.choice(["red", "green", "blue"], (10, 10))

_, ax = plt.subplots()
Colors(data).render(ax)
