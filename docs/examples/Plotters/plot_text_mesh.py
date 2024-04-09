"""
TextMesh
========

:class:`TextMesh` is a class that allows you to layout text in a mesh style.

"""

# %%
from marsilea.plotter import TextMesh

# %%
import numpy as np
import matplotlib.pyplot as plt

data = np.random.randint(0, 10, (10, 10))

_, ax = plt.subplots()
TextMesh(data).render(ax)
