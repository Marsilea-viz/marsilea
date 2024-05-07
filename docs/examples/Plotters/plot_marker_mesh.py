"""
MarkerMesh
==========

:class:`~marsilea.plotter.MarkerMesh` is a plotter that displays a 2D array as a mesh with markers.

"""

# %%
from marsilea.plotter import MarkerMesh

# %%
import numpy as np
import matplotlib.pyplot as plt

data = np.random.randint(0, 10, (10, 10))

_, ax = plt.subplots()
MarkerMesh(data, color="#F05454").render(ax)
