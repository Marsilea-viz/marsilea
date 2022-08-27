from typing import List, Sequence

import numpy as np
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D
from scipy.cluster.hierarchy import linkage, dendrogram


class _DendrogramBase:

    def __init__(self,
                 data,
                 method='single',
                 metric='euclidean'
                 ):
        self.Z = linkage(data, method=method, metric=metric)
        self._plot_data = dendrogram(self.Z, no_plot=True)

        self.x_coords = np.asarray(self._plot_data['icoord']) / 5
        self.y_coords = np.asarray(self._plot_data['dcoord'])
        self.n_leaves = len(self.reorder_index)
        self.max_dependent_coord = np.max(self.y_coords)

        self.xlim = np.array([0, self.n_leaves * 2])
        self.ylim = np.array([0, self.max_dependent_coord * 1.05])

        # Should be lazy eval
        self._center = np.mean(data, axis=0)

    @property
    def xrange(self):
        return self.xlim[1] - self.xlim[0]

    @property
    def yrange(self):
        return self.ylim[1] - self.ylim[0]

    def reset_lim(self, x_start=None, y_end=None):
        if x_start is not None:
            self.xlim = self.xlim + x_start
            self.x_coords = self.x_coords + x_start

        if y_end is not None:
            if y_end < self.ylim[1]:
                raise ValueError(f"{y_end} is lower than "
                                 f"current ylim at {self.ylim[1]}")
            self.ylim = (0, y_end)

    @property
    def reorder_index(self):
        return self._plot_data['leaves']

    @property
    def center(self):
        return self._center

    @property
    def root(self):
        xc = self.x_coords[-1]
        yc = self.y_coords[-1]
        x1 = (xc[2] - xc[1]) / 2. + xc[1]
        y1 = yc[1]
        return x1, y1


class Dendrogram(_DendrogramBase):

    def __init__(self,
                 data: np.ndarray,
                 method='single',
                 metric='euclidean'
                 ):
        super().__init__(data, method=method, metric=metric)

    def draw(self, ax, orient="h", add_root=False, control_ax=True):
        x_coords = self.x_coords
        y_coords = self.y_coords
        if orient == "v":
            x_coords, y_coords = y_coords, x_coords

        lines = LineCollection(
            [list(zip(x, y)) for x, y in zip(x_coords, y_coords)]
        )
        ax.add_collection(lines)

        xlim = self.xlim
        ylim = self.ylim
        if orient == "v":
            xlim, ylim = ylim, xlim

        if control_ax:
            ax.set_xlim(*xlim)
            ax.set_ylim(*ylim)

        if add_root:
            x1, y1 = self.root
            x2 = x1
            y2 = ylim[1]
            root_line = Line2D([x1, x2], [y1, y2])
            ax.add_artist(root_line)


class GroupDendrogram(_DendrogramBase):
    def __init__(self,
                 dens: List[Dendrogram],
                 method='single',
                 metric='euclidean'
                 ):
        data = np.asarray([d.center for d in dens])
        super().__init__(data, method=method, metric=metric)
        self.dens = np.asarray(dens)[self.reorder_index]
        self.n = len(self.dens)

    def test_draw(self, axes):
        for ax, den in zip(axes, self.dens):
            den.draw(ax, add_root=True)

    def draw(self,
             ax,
             orient="h",
             spacing=None,
             sub_frac=0.7
             ):
        if spacing is None:
            spacing = [0 for _ in range(self.n - 1)]
        elif not isinstance(spacing, Sequence):
            spacing = [spacing for _ in range(self.n - 1)]

        xlim = 0
        ylim = 0
        x_coords = []
        for den in self.dens:
            xlim += den.xrange
            dylim = den.yrange
            if dylim > ylim:
                ylim = dylim
            x_coords.append(den.root[0])
        xlim /= (1 - np.sum(spacing))


        x_start = 0
        for i, den in enumerate(self.dens):
            if x_start != 0:
                den.reset_lim(x_start=x_start, y_end=ylim)
            else:
                den.reset_lim(y_end=ylim)
            if i != self.n - 1:
                x_start = x_start + den.xrange + spacing[i] * xlim
        ax.set_xlim(0, xlim)
        ax.set_ylim(0, ylim/sub_frac)

        skeleton = np.sort(np.unique(self.x_coords[self.y_coords == 0]))
        ranger = [(skeleton[i], skeleton[i + 1]) \
                  for i in range(len(skeleton) - 1)]
        # get render x
        # orient ?
        render_x = [den.root[0] for den in self.dens]
        mapper = {i: v for i, v in zip(skeleton, render_x)}
        x_coords = np.sort(np.unique(self.x_coords.flatten()))

        real_x = {}

        ranger_ix = 0
        for xc in x_coords:
            render_coord = mapper.get(xc, None)
            if render_coord is None:
                while True:
                    lower, upper = ranger[ranger_ix]
                    real_up, real_low = mapper[upper], mapper[lower]
                    if (xc > lower) & (xc < upper):
                        ratio = (xc - lower) / (upper - lower)
                        real_length = (real_up - real_low) * ratio
                        render_coord = real_low + real_length
                        real_x[xc] = render_coord
                        break
                    else:
                        ranger_ix += 1
            else:
                real_x[xc] = render_coord
        self.x_coords = np.asarray(
            [real_x[i] for i in self.x_coords.flatten()]
        ).reshape(self.x_coords.shape)
        self.y_coords += ylim
        ax.hlines(ylim, 0, xlim, linestyles="--")

        for den in self.dens:
            den.draw(ax, orient=orient, add_root=True, control_ax=False)

        # Add meta dendrogram
        x_coords = self.x_coords
        y_coords = self.y_coords
        if orient == "v":
            x_coords, y_coords = y_coords, x_coords

        lines = LineCollection(
            [list(zip(x, y)) for x, y in zip(x_coords, y_coords)]
        )
        ax.add_collection(lines)

