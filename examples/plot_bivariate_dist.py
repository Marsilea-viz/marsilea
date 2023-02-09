"""
Bivariate Distribution
=======================

"""

import numpy as np
import seaborn as sns
from matplotlib import pyplot as plt
from scipy.stats import gaussian_kde

import heatgraphy as hg


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

wb = hg.WhiteBoard(name="main", width=3, height=3)
wb.add_canvas("top", size=.4, pad=.1, name="x1")
wb.add_canvas("bottom", size=.4, pad=.1, name="x2")

wb.add_canvas("left", size=.4, pad=.1, name="y1")
wb.add_canvas("right", size=.4, pad=.1, name="y2")
wb.add_title(left="Y-axis distribution", top="X-axis distribution")
wb.add_pad("left", size=.3)
wb.add_pad("right", size=.3)
wb.render()

main_ax = wb.get_ax("main")
main_ax.set_axis_off()
main_ax.pcolormesh(Z, cmap="Greens")

x_ax = wb.get_ax("x2")
x_ax.set_axis_off()
x_ax.pcolormesh(zy.reshape(1, -1), cmap="Blues")

x2_ax = wb.get_ax("x1")
sns.lineplot(x=np.arange(len(zy)), y=zy,
             ax=x2_ax, color="b", alpha=.7)
x2_ax.set_xlim(0, len(zy))
x2_ax.tick_params(bottom=False, labelbottom=False)
sns.despine(ax=x2_ax)

y_ax = wb.get_ax("y2")
y_ax.set_axis_off()
y_ax.pcolormesh(zy.reshape(-1, 1), cmap="Reds")
y_ax.invert_yaxis()

y2_ax = wb.get_ax("y1")
sns.lineplot(y=np.arange(len(zx)), x=zx, ax=y2_ax,
             orient="y", color="r", alpha=.7)
y2_ax.set_ylim(0, len(zx))
sns.despine(ax=y2_ax, left=True, right=False)
y2_ax.tick_params(right=False, labelright=False)
for tick in y2_ax.get_xticklabels():
    tick.set_rotation(90)
y2_ax.invert_xaxis()
plt.show()
