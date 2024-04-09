"""
Retrieve axes
=============

This example shows how to access the axes object in Marsilea.

"""


# %%
import numpy as np
import marsilea as ma

data = np.random.randint(0, 10, (10, 10))

#%%
# To get the main axes object, use the :meth:`~marsilea.base.WhiteBoard.get_main_axes` method.
# The axes will only exist after you render the plot.
h = ma.Heatmap(data, width=3, height=3)
h.render()
main_ax = h.get_main_ax()
main_ax.text(0.5, 0.5, "Main Axes", ha="center", va="center", bbox=dict(facecolor="white"),
             fontsize=20, color="red", transform=main_ax.transAxes)


# %%
# If you cut the canvas, you will get multiple axes objects.

h = ma.Heatmap(data, width=3, height=3)
h.cut_rows([2])
h.render()
main_ax = h.get_main_ax()
print(f"{len(main_ax)} axes objects")
