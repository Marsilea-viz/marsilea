"""
Save to file
============

This example shows how to save a plot to a file.

"""

# %%
import numpy as np
import marsilea as ma

data = np.random.randint(0, 10, (10, 10))

# %%
# To save a plot to a file, use the :code:`save` method.

h = ma.Heatmap(data, width=3, height=3)
h.save("plot.png")

# %%
# You can also save the plot use the :func:`matplotlib.pyplot.savefig`.

import matplotlib.pyplot as plt

h = ma.Heatmap(data, width=3, height=3)
h.render()

plt.savefig("plot.pdf", bbox_inches="tight")
