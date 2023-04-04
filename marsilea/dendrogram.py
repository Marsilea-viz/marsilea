from itertools import cycle
from typing import List, Sequence

import numpy as np
from matplotlib.collections import LineCollection
from matplotlib.colors import is_color_like
from matplotlib.lines import Line2D
from scipy.cluster.hierarchy import linkage, dendrogram


class _DendrogramBase:

    is_singleton = False

    def __init__(self,
                 data,
                 method=None,
                 metric=None,
                 ):
        if method is None:
            method = "single"
        if metric is None:
            metric = "euclidean"
        # edge case: data is 1d, may happen when user split the data
        if len(data) == 1:
            # TODO: the y coords are heuristic value,
            #       need a better way to handle
            self.x_coords = np.array([[1., 1., 1., 1.]])
            self.y_coords = np.array([[0., .75, .75, 0.]])
            self._reorder_index = np.array([0])
            self.is_singleton = True
        else:
            self.Z = linkage(data, method=method, metric=metric)
            self._plot_data = dendrogram(self.Z, no_plot=True)

            self.x_coords = np.asarray(self._plot_data['icoord']) / 5
            self.y_coords = np.asarray(self._plot_data['dcoord'])
            self._reorder_index = self._plot_data['leaves']
            ycoords = np.unique(self.y_coords)
            ycoords = ycoords[np.nonzero(ycoords)]
            y_min, y_max = np.min(ycoords), np.max(ycoords)
            interval = y_max - y_min
            for i, j in zip(*np.nonzero(self.y_coords)):
                if self.y_coords[i, j] != 0.:
                    v = self.y_coords[i, j]
                    self.y_coords[i, j] = (v - y_min) / interval + .2
                    # self.y_coords[i, j] -= offset
            # self.y_coords[np.nonzero(self.y_coords)] - offset

        self._render_x_coords = self.x_coords
        self._render_y_coords = self.y_coords
        self.n_leaves = len(self.reorder_index)
        self.max_dependent_coord = np.max(self.y_coords)

        self.xlim = np.array([0, self.n_leaves * 2])
        self.ylim = np.array([0, self.max_dependent_coord * 1.05])
        self._render_xlim = self.xlim
        self._render_ylim = self.ylim
        # Should be lazy eval
        self._center = np.mean(data, axis=0)

    @property
    def xrange(self):
        return self.xlim[1] - self.xlim[0]

    @property
    def yrange(self):
        return self.ylim[1] - self.ylim[0]

    @property
    def render_xrange(self):
        return self._render_xlim[1] - self._render_xlim[0]

    @property
    def render_yrange(self):
        return self._render_ylim[1] - self._render_ylim[0]

    def set_lim(self, x_start=None, y_end=None):
        if x_start is not None:
            self._render_xlim = self.xlim + x_start
            self._render_x_coords = self.x_coords + x_start

        if y_end is not None:
            if y_end < self.ylim[1]:
                raise ValueError(f"{y_end} is lower than "
                                 f"current ylim at {self.ylim[1]}")
            self._render_ylim = (0, y_end)

    @property
    def reorder_index(self):
        return self._reorder_index

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

    @property
    def render_root(self):
        xc = self._render_x_coords[-1]
        yc = self._render_y_coords[-1]
        x1 = (xc[2] - xc[1]) / 2. + xc[1]
        y1 = yc[1]
        return x1, y1

    def _draw_dendrogram(self, ax, orient="top", color=".1", linewidth=.7):
        x_coords = self._render_x_coords
        y_coords = self._render_y_coords
        if orient in ["right", "left"]:
            x_coords, y_coords = y_coords, x_coords

        lines = LineCollection(
            [list(zip(x, y)) for x, y in zip(x_coords, y_coords)],
            color=color, linewidth=linewidth
        )
        ax.add_collection(lines)


class Dendrogram(_DendrogramBase):
    """A dendrogram class
    
    Parameters
    ----------

    data : np.ndarray
    method : str
        Refer to :func:`scipy.cluster.hierarchy.linkage`
    metric : str
        Refer to :func:`scipy.cluster.hierarchy.linkage`
    
    """

    def __init__(self,
                 data: np.ndarray,
                 method=None,
                 metric=None
                 ):
        super().__init__(data, method=method, metric=metric)

    # here we left an empty **kwargs to align api with GroupDendrogram
    def draw(self, ax, orient="top",
             color=None, linewidth=None,
             add_root=False, root_color=None,
             control_ax=True,
             **kwargs):
        """

        Parameters
        ----------
        ax
        orient
        color : color
            The line color of the dendrogram
        linewidth : float
        add_root : bool
            Add a line to represent the root of dendrogram
        root_color : color
            The color of the root line
        control_ax : bool
            Adjust the axes to ensure the dendrogram will display correctly

        Returns
        -------

        """
        color = ".1" if color is None else color
        root_color = color if root_color is None else root_color
        linewidth = .7 if linewidth is None else linewidth

        self._draw_dendrogram(ax, orient=orient, color=color,
                              linewidth=linewidth)

        xlim = self._render_xlim
        ylim = self._render_ylim
        if orient in ["right", "left"]:
            xlim, ylim = ylim, xlim

        if control_ax:
            ax.set_xlim(*xlim)
            ax.set_ylim(*ylim)
            if orient == "left":
                ax.invert_xaxis()
            if orient == "bottom":
                ax.invert_yaxis()

        if add_root:
            x1, y1 = self.render_root
            if orient in ["right", "left"]:
                x1, y1 = y1, x1
                x2 = xlim[1]
                y2 = y1
            else:
                x2 = x1
                y2 = ylim[1]
            root_line = Line2D([x1, x2], [y1, y2],
                               color=root_color, linewidth=linewidth)
            ax.add_artist(root_line)


class GroupDendrogram(_DendrogramBase):
    """Meta dendrogram

    Parameters
    ----------

    dens : array of :class:`Dendrogram`
        A list of :class:`Dendrogram`
    method : str
    metric : str
    
    """

    def __init__(self,
                 dens: List[Dendrogram],
                 method=None,
                 metric=None
                 ):
        data = np.vstack([d.center for d in dens])
        super().__init__(data, method=method, metric=metric)
        self.orig_dens = np.asarray(dens)
        self.dens = np.asarray(dens)[self.reorder_index]
        self.n = len(self.dens)

        den_xlim = 0
        ylim = 0
        x_coords = []
        for den in self.dens:
            den_xlim += den.xrange
            dylim = den.yrange
            if dylim > ylim:
                ylim = dylim
            x_coords.append(den.root[0])
        self.den_xlim = den_xlim
        self.den_ylim = ylim
        self.divider = ylim * 1.05

    def draw(self,
             ax,
             orient="top",
             spacing=None,
             add_meta=True,
             add_base=True,
             base_colors=None,
             meta_color=None,
             linewidth=None,
             divide=True,
             divide_style="--",
             meta_ratio=.2,
             ):
        """

        Parameters
        ----------
        ax
        orient
        spacing : float, array of float
            The space between dendrograms
        add_meta : bool
            Draw the meta dendrogram
        add_base : bool
            Draw the base dendrograms
        base_colors : color, array of colors
            The color of base dendrograms, if array is passed,
            will be applied by group order.
        meta_color : color
            The color of meta dendrogram
        linewidth
        divide : bool
            Draw a divide line the divides the meta and base dendrograms
        divide_style :
            The linestyle of the divide line
        meta_ratio : float
            The size of meta dendrogram relative to the base dendrogram

        """

        meta_color = ".1" if meta_color is None else meta_color
        linewidth = .7 if linewidth is None else linewidth
        if base_colors is None:
            base_colors = cycle([None])
        elif is_color_like(base_colors):
            base_colors = cycle([base_colors])
        else:
            base_colors = np.asarray(base_colors)
            if add_meta:
                base_colors = base_colors[self.reorder_index]

        if spacing is None:
            spacing = [0 for _ in range(self.n - 1)]
        elif not isinstance(spacing, Sequence):
            spacing = [spacing for _ in range(self.n - 1)]

        render_xlim = self.den_xlim / (1 - np.sum(spacing))
        skeleton = np.sort(np.unique(self.x_coords[self.y_coords == 0]))
        ranger = [(skeleton[i], skeleton[i + 1]) \
                  for i in range(len(skeleton) - 1)]

        draw_dens = self.dens if add_meta else self.orig_dens

        if add_base:
            x_start = 0
            for i, den in enumerate(draw_dens):
                if x_start != 0:
                    den.set_lim(x_start=x_start, y_end=self.divider)
                else:
                    den.set_lim(y_end=self.divider)
                if i != self.n - 1:
                    x_start = x_start + den.xrange + spacing[i] * render_xlim
            # get render x
            # orient ?
            skeleton_x = [den.render_root[0] for den in draw_dens]

        else:
            xstart = 0
            skeleton_x = []
            for i, den in enumerate(draw_dens):
                if i == 0:
                    xstart += den.xrange / 2
                else:
                    xstart += den.xrange / 2 + spacing[i - 1] * render_xlim
                skeleton_x.append(xstart)
                xstart += den.xrange / 2

        mapper = dict(zip(skeleton, skeleton_x))
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

        self._render_x_coords = np.asarray(
            [real_x[i] for i in self.x_coords.flatten()]
        ).reshape(self.x_coords.shape)
        if add_base:
            if add_meta:
                norm_y_coords = self.y_coords  # / np.max(self.y_coords)
                amplify = self.den_ylim * meta_ratio
                self._render_y_coords = norm_y_coords * amplify + self.divider
            else:
                self._render_y_coords = self.den_ylim
        else:
            self._render_y_coords = self.y_coords / 5

        if add_meta:
            # Add meta dendrogram
            self._draw_dendrogram(ax, orient=orient,
                                  color=meta_color, linewidth=linewidth)

        if divide & add_base & add_meta:
            xmin = np.min(draw_dens[0].x_coords)
            xmax = np.max(draw_dens[-1]._render_x_coords)
            if orient in ["top", "bottom"]:
                ax.hlines(self.divider, xmin, xmax,  # 0, xlim,
                          linestyles=divide_style, color=meta_color,
                          linewidth=linewidth)
            else:
                ax.vlines(self.divider, xmin, xmax,  # 0, ylim,
                          linestyles=divide_style, color=meta_color,
                          linewidth=linewidth)

        if add_base:
            for den, color in zip(draw_dens, base_colors):
                # The singleton dendrogram will only be drawn if meta is drawn
                if not den.is_singleton or add_meta:
                    den.draw(ax, orient=orient, add_root=add_meta, color=color,
                             linewidth=linewidth,
                             root_color=meta_color, control_ax=False)

        xlim = render_xlim
        # reserve room to avoid clipping of the top
        ylim = np.max(self._render_y_coords) * 1.05
        if orient in ["right", "left"]:
            xlim, ylim = ylim, xlim

        ax.set_xlim(0, xlim)
        ax.set_ylim(0, ylim)
        if orient == "left":
            ax.invert_xaxis()
        if orient != "top":
            ax.invert_yaxis()
