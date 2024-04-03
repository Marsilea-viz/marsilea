"""
Numbers
=======

:class:`~marsilea.plotter.Numbers` is to display numbers in a bar plot.
"""

# %%
from marsilea.plotter import Numbers

# %%
import numpy as np
import matplotlib.pyplot as plt

_, ax = plt.subplots()
data = np.random.randint(0, 10, 10)
Numbers(data).render(ax)
