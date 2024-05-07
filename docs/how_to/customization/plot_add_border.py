"""
Add/Remove border
=================

"""

# %%
import numpy as np
import marsilea as ma

data = np.random.randint(0, 10, (10, 10))

# %%
# To add a border
from matplotlib.patches import Rectangle

h = ma.Heatmap(data, width=3, height=3)
h.render()
ax = h.get_main_ax()
rect = Rectangle((0, 0), 1, 1, ec="green", fc="none", transform=ax.transAxes)
ax.add_artist(rect)


# %%
# To remove the border

h = ma.SizedHeatmap(data, width=3, height=3)
h.render()
main_ax = h.get_main_ax()
for spine in main_ax.spines.values():
    spine.set_visible(False)
