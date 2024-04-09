"""
AnnoLabels
==========

:class:`~marsilea.plotter.AnnoLabels` is to annotate some specific records in the data.

"""

# %%
from marsilea.plotter import AnnoLabels

# %%
import numpy as np
import matplotlib.pyplot as plt

_, ax = plt.subplots()
data = np.arange(100)

anno = AnnoLabels(data, [1, 2, 3, 98, 99])
anno.set_side("right")
anno.render(ax)
