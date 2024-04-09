"""
SizedMesh
=========

:class:`~marsilea.plotter.SizedMesh` is a plotter that create a mesh plot with different sizes of markers.

"""

# %%
from marsilea.plotter import SizedMesh

# %%
import numpy as np
import matplotlib.pyplot as plt

_, ax = plt.subplots()
data = np.random.randint(0, 10, (10, 10))
SizedMesh(data).render(ax)
