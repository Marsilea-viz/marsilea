"""
Bivariate Distribution
=======================

"""

import numpy as np
import seaborn as sns
from matplotlib import pyplot as plt
from scipy.stats import gaussian_kde

import marsilea as ma

# %%
# Create datasets

np.random.seed(0)
rs = np.random.RandomState(50)
x, y = rs.normal(size=(2, 50))
xmin, ymin, xmax, ymax = x.min(), y.min(), x.max(), y.max()

X, Y = np.mgrid[xmin:xmax:100j, ymin:ymax:100j]
positions = np.vstack([X.ravel(), Y.ravel()])
values = np.vstack([x, y])

main_kernel = gaussian_kde(values)

Z = np.reshape(main_kernel(positions), X.shape)

x_kernel = gaussian_kde(x)
zx = x_kernel(np.mgrid[xmin:xmax:100j])

y_kernel = gaussian_kde(x)
zy = y_kernel(np.mgrid[ymin:ymax:100j])

# %%
# Create skeletons and add contents

wb = ma.WhiteBoard(width=3, height=3)
# Reserve empty canvas for drawing latter
wb.add_canvas("top", size=.4, pad=.1, name="x1")
wb.add_canvas("bottom", size=.4, pad=.1, name="x2")
wb.add_canvas("left", size=.4, pad=.1, name="y1")
wb.add_canvas("right", size=.4, pad=.1, name="y2")
# Add title
wb.add_title(left="Y-axis distribution", top="X-axis distribution")
# Add padding
wb.add_pad("left", size=.3)
wb.add_pad("right", size=.3)
# Initiate the axes
wb.render()

main_ax = wb.get_main_ax()
main_ax.set_axis_off()
main_ax.pcolormesh(Z, cmap="Greens")

x1_ax = wb.get_ax("x1")
sns.lineplot(x=np.arange(len(zy)), y=zy,
             ax=x1_ax, color="b", alpha=.7)
x1_ax.set_xlim(0, len(zy))
x1_ax.tick_params(bottom=False, labelbottom=False)
sns.despine(ax=x1_ax)

x2_ax = wb.get_ax("x2")
x2_ax.set_axis_off()
x2_ax.pcolormesh(zy.reshape(1, -1), cmap="Blues")

y1_ax = wb.get_ax("y1")
sns.lineplot(y=np.arange(len(zx)), x=zx, ax=y1_ax,
             orient="y", color="r", alpha=.7)
y1_ax.set_ylim(0, len(zx))
sns.despine(ax=y1_ax, left=True, right=False)
y1_ax.tick_params(right=False, labelright=False)
for tick in y1_ax.get_xticklabels():
    tick.set_rotation(90)
y1_ax.invert_xaxis()

y2_ax = wb.get_ax("y2")
y2_ax.set_axis_off()
y2_ax.pcolormesh(zy.reshape(-1, 1), cmap="Reds")
y2_ax.invert_yaxis()

plt.show()
