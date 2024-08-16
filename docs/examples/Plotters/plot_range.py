"""
Range
=====

:class:`~marsilea.plotter.Range` is a plotter that displays range between two values.

"""

# %%
from marsilea.plotter import Range

# %%
import numpy as np
import matplotlib.pyplot as plt

_, ax = plt.subplots()
data = np.random.randint(1, 100, (10, 2))
Range(data).render(ax)
