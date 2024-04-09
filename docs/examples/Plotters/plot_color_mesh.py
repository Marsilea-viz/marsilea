"""
ColorMesh
=========

:class:`~marsilea.plotter.ColorMesh` is a plotter that displays a 2D array as a
colored mesh.

"""

# %%
from marsilea.plotter import ColorMesh

# %%
import numpy as np
import matplotlib.pyplot as plt

data = np.random.randint(0, 10, (10, 10))

_, ax = plt.subplots()
ColorMesh(data, annot=True).render(ax)
