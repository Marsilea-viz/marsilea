"""
Arc
===

:class:`~marsilea.plotter.Arc` is for drawing connection between data.

"""


# %%
from marsilea.plotter import Arc

# %%
import numpy as np
import matplotlib.pyplot as plt

_, ax = plt.subplots(figsize=(6, 3))
anchors = np.arange(10)
Arc(anchors, links=[(0, 5), (2, 9), (1, 9)]).render(ax)
