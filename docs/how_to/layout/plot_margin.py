"""
Add canvas margin
=================

Margin allows you to add white space around the whole plot.
This is helpful when you plot get clipped during saving.

"""

# %%
import numpy as np
import marsilea as ma

from matplotlib.patches import Rectangle

data = np.random.randint(0, 10, (10, 10))

h = ma.Heatmap(data, width=1, height=1)
h.set_margin(0.1)
h.render()
_ = h.figure.add_artist(Rectangle((0, 0), 1, 1, ec="g", fc="none", lw=1))

# %%
# You can control the margin using the `margin` parameter.
h = ma.Heatmap(data, width=1, height=1)
h.set_margin(1)
h.render()
_ = h.figure.add_artist(Rectangle((0, 0), 1, 1, ec="g", fc="none", lw=1))
