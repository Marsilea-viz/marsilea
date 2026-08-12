import sys
import warnings
import numpy as np
from itertools import cycle
from matplotlib.collections import LineCollection
from matplotlib.colors import is_color_like
from matplotlib.lines import Line2D
from scipy.cluster.hierarchy import linkage as scipy_linkage, dendrogram
from typing import List

from .exceptions import PerformanceWarning

_FASTCLUSTER_THRESHOLD = 10_000  # total elements; matches seaborn


def _compute_linkage(data, method, metric):
    """Compute hierarchical clustering linkage.

    Uses fastcluster if installed (``pip install marsilea[fast]``), which is
    always faster than scipy. Falls back to scipy and emits a
    :class:`PerformanceWarning` when data exceeds *_FASTCLUSTER_THRESHOLD*
    total elements.
    """
    try:
        import fastcluster

        euclidean_methods = ("centroid", "median", "ward")
        use_vector = method == "single" or (
            metric == "euclidean" and method in euclidean_methods
        )
        if use_vector:
            return fastcluster.linkage_vector(data, method=method, metric=metric)
        return fastcluster.linkage(data, method=method, metric=metric)
    except ImportError:
        if np.prod(data.shape) >= _FASTCLUSTER_THRESHOLD:
            warnings.warn(
                f"Clustering large array ({np.prod(data.shape)} elements) with scipy. "
                "Install `fastcluster` for better performance: "
                "pip install marsilea[fast]",
                PerformanceWarning,
                stacklevel=4,
            )
        return scipy_linkage(data, method=method, metric=metric)


def _dendrogram_layout(Z):
    """Get the drawing coordinates for a linkage matrix.

    scipy walks the tree recursively, one frame per level, so a tall tree
    overruns the interpreter's recursion limit. Single linkage chains, which
    makes the depth grow with the leaf count: the default limit of 1000 is
    already exhausted around 2500 leaves. Measured depth is ~0.65 frames per
    leaf, so allow triple that and put the limit back afterwards.
    """
    # Raising the limit covers the tree sizes this library plots. If one ever
    # outgrows the stack, replace this with an iterative icoord/dcoord builder.
    needed = 2 * len(Z) + 1000
    limit = sys.getrecursionlimit()
    if needed <= limit:
        return dendrogram(Z, no_plot=True)
    sys.setrecursionlimit(needed)
    try:
        return dendrogram(Z, no_plot=True)
    finally:
        sys.setrecursionlimit(limit)


#: Default for :meth:`ClusterBoard.add_dendrogram`; kept at the legacy
#: behaviour so existing figures do not move. See the height scaling how-to.
DEFAULT_HEIGHT_SCALE = "minmax"

_HEIGHT_SCALES = ("minmax", "group", "shared")

_HEIGHT_TRANSFORMS = {
    "linear": lambda u: u,
    "sqrt": np.sqrt,
    "log": lambda u: np.log1p(9.0 * u) / np.log(10.0),
}


class _HeightScale:
    """Map raw merge heights onto ``[0, 1]``.

    *pool* is the set of heights the scale is calibrated against, and choosing
    it is the whole game: one dendrogram's own heights make each group fill the
    space it is given, every group's heights pooled together make the groups
    comparable by eye.

    *transform* bends the result without reordering it. Merge heights are often
    bunched at the bottom, badly so for ward linkage, which leaves the top of
    the plot empty; ``"sqrt"`` and ``"log"`` open the low end up and ``"rank"``
    spreads the merges evenly. All of them trade away readable distances.
    """

    def __init__(self, pool, transform=None):
        pool = np.asarray(pool, dtype=float).ravel()
        self.pool = np.unique(pool[pool > 0])
        self.transform = transform

    def _bend(self, u):
        if self.transform is None:
            return u
        if callable(self.transform):
            return np.asarray(self.transform(u), dtype=float)
        return _HEIGHT_TRANSFORMS[self.transform](u)

    def __call__(self, y_coords):
        scaled = np.zeros_like(y_coords, dtype=float)
        merges = y_coords > 0
        if len(self.pool) == 0 or not merges.any():
            # nothing ever merged, every leaf is drawn flat on the baseline
            return scaled
        if self.transform == "rank":
            scaled[merges] = (
                np.searchsorted(self.pool, y_coords[merges], side="right")
                / self.pool.size
            )
        else:
            scaled[merges] = self._bend(
                np.clip(y_coords[merges] / self.pool[-1], 0.0, 1.0)
            )
        return scaled


def _base_scales(dens, scale, transform):
    """One height scale per base dendrogram.

    A shared scale is calibrated on every group's heights at once, which is
    what lets two groups be compared by eye; a group scale calibrates each on
    its own, and the legacy min-max gives back None.
    """
    if scale is None:
        scale = DEFAULT_HEIGHT_SCALE
    if scale == "shared":
        pool = np.concatenate([den.y_coords.ravel() for den in dens])
        return [_resolve_height_scale(scale, pool, transform)] * len(dens)
    return [_resolve_height_scale(scale, den.y_coords, transform) for den in dens]


def _resolve_height_scale(scale, pool, transform):
    """None means the legacy per-group min-max, anything else is a scale."""
    if scale is None:
        scale = DEFAULT_HEIGHT_SCALE
    if scale not in _HEIGHT_SCALES:
        raise ValueError(
            f"Unknown height_scale {scale!r}, expected one of {_HEIGHT_SCALES}"
        )
    if not (transform is None or callable(transform)) and (
        transform not in _HEIGHT_TRANSFORMS and transform != "rank"
    ):
        expected = (*_HEIGHT_TRANSFORMS, "rank")
        raise ValueError(
            f"Unknown height_transform {transform!r}, expected one of {expected}, "
            f"a callable, or None"
        )
    if scale == "minmax":
        if transform is not None:
            raise ValueError(
                "height_transform needs height_scale='group' or 'shared'; the "
                "default 'minmax' scaling stretches every group to the same "
                "height, so there is nothing left for a transform to do"
            )
        return None
    return _HeightScale(pool, transform=transform)


class _DendrogramBase:
    is_singleton = False

    def __init__(
        self,
        data,
        method=None,
        metric=None,
        linkage=None,
        get_meta_center=None,
        key=None,
        **kwargs,
    ):
        self.key = key
        self.data = data
        if method is None:
            method = "single"
        if metric is None:
            metric = "euclidean"
        # edge case: data is 1d, may happen when user split the data
        if len(data) == 1:
            self.x_coords = np.array([[1.0, 1.0, 1.0, 1.0]])
            # a lone observation never merges, so every height is truly zero
            self.y_coords = np.zeros((1, 4))
            self._reorder_index = np.array([0])
            self.is_singleton = True
            # ... and for the same reason there is no linkage
            self.Z = None
        else:
            if linkage is not None:
                self.Z = linkage
            else:
                self.Z = _compute_linkage(data, method=method, metric=metric)
            self._plot_data = _dendrogram_layout(self.Z)

            self.x_coords = np.asarray(self._plot_data["icoord"]) / 5
            # kept as scipy reports them, in the metric's own units; how they
            # map onto the axis is decided later by set_height_scale
            self.y_coords = np.asarray(self._plot_data["dcoord"], dtype=float)
            self._reorder_index = self._plot_data["leaves"]

        self.max_height = float(np.max(self.y_coords))
        self._render_x_coords = self.x_coords
        self.n_leaves = len(self.reorder_index)

        self.xlim = np.array([0, self.n_leaves * 2])
        self._render_xlim = self.xlim
        # drawable on its own; a GroupDendrogram rescales its members itself
        self.set_height_scale(None)

        # Should be lazy eval
        # TODO: Allow center to be calculated differently
        if get_meta_center is None:
            self._center = np.mean(data, axis=0)
        elif callable(get_meta_center):
            # Ensure the centroid function returns a numpy array of correct shape
            centroid = get_meta_center(data)
            if isinstance(centroid, np.ndarray) and centroid.shape == data.shape[1:]:
                self._center = centroid
            else:
                raise ValueError(
                    "The get_meta_center must return a numpy array with shape "
                    "matching the number of features in the data."
                )
        else:
            raise TypeError("The get_meta_center must be a callable function or None.")

    def _minmax_heights(self):
        """Legacy scaling: stretch this tree's own range onto ``[0.2, 1.2]``.

        Every dendrogram then ends up exactly as tall as every other one,
        whatever its real spread, which is what ``height_scale="shared"``
        exists to undo.
        """
        merges = self.y_coords != 0
        if len(self.y_coords) == 1 or not merges.any():
            # one merge, or none at all, leaves nothing to stretch
            return np.array([[0.0, 0.75, 0.75, 0.0]])
        scaled = self.y_coords.copy()
        heights = self.y_coords[merges]
        y_min, y_max = heights.min(), heights.max()
        interval = y_max - y_min
        if interval == 0:
            # every merge happened at the same distance, so there is no
            # spread to normalize against
            scaled[merges] = 1.2
        else:
            scaled[merges] = (heights - y_min) / interval + 0.2
        return scaled

    def set_height_scale(self, scale, band=1.0, offset=0.0):
        """Place the merge heights on the drawn axis.

        *scale* maps raw heights onto ``[0, 1]``; the result is stretched to
        *band* and lifted by *offset*. Passing None keeps the legacy per-group
        min-max normalization.

        Only the render coordinates are derived, so this can be called again
        with a different scale without losing the original heights.
        """
        if scale is None:
            scaled = self._minmax_heights()
            headroom = 1.05
        else:
            scaled = band * scale(self.y_coords)
            headroom = 1.0
        self._render_y_coords = scaled + offset
        self.max_dependent_coord = float(np.max(scaled))
        self.ylim = np.array([0.0, self.max_dependent_coord * headroom])
        self._render_ylim = self.ylim

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
                raise ValueError(
                    f"{y_end} is lower than current ylim at {self.ylim[1]}"
                )
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
        x1 = (xc[2] - xc[1]) / 2.0 + xc[1]
        y1 = yc[1]
        return x1, y1

    @property
    def render_root(self):
        xc = self._render_x_coords[-1]
        yc = self._render_y_coords[-1]
        x1 = (xc[2] - xc[1]) / 2.0 + xc[1]
        y1 = yc[1]
        return x1, y1

    def _draw_dendrogram(
        self, ax, orient="top", color=".1", linewidth=0.7, rasterized=False
    ):
        x_coords = self._render_x_coords
        y_coords = self._render_y_coords
        if orient in ["right", "left"]:
            x_coords, y_coords = y_coords, x_coords

        lines = LineCollection(
            [list(zip(x, y)) for x, y in zip(x_coords, y_coords)],
            color=color,
            linewidth=linewidth,
            rasterized=rasterized,
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

    def __init__(
        self,
        data: np.ndarray,
        method=None,
        metric=None,
        linkage=None,
        get_meta_center=None,
        key=None,
        **kwargs,
    ):
        super().__init__(
            data,
            method=method,
            metric=metric,
            key=key,
            linkage=linkage,
            get_meta_center=get_meta_center,
            **kwargs,
        )

    # here we left an empty **kwargs to align api with GroupDendrogram
    def draw(
        self,
        ax,
        orient="top",
        color=None,
        linewidth=None,
        add_root=False,
        root_color=None,
        control_ax=True,
        rasterized=False,
        height_scale=None,
        height_transform=None,
        **kwargs,
    ):
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
        rasterized : bool
            Rasterize the dendrogram to speed up rendering

        Returns
        -------

        """
        color = ".1" if color is None else color
        root_color = color if root_color is None else root_color
        linewidth = 0.7 if linewidth is None else linewidth

        if height_scale is not None or height_transform is not None:
            self.set_height_scale(
                _resolve_height_scale(height_scale, self.y_coords, height_transform)
            )
        # asking for neither leaves the heights alone, which is what a
        # GroupDendrogram needs: it has already scaled this dendrogram against
        # its sibling groups before handing it the axes

        self._draw_dendrogram(
            ax, orient=orient, color=color, linewidth=linewidth, rasterized=rasterized
        )

        xlim = self._render_xlim
        ylim = self._render_ylim
        if orient in ["right", "left"]:
            xlim, ylim = ylim, xlim
        if control_ax:
            ax.set_xlim(*xlim)
            ax.set_ylim(*ylim)
            if orient == "left":
                ax.invert_xaxis()
            if orient != "top":
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
            root_line = Line2D(
                [x1, x2],
                [y1, y2],
                color=root_color,
                linewidth=linewidth,
                rasterized=rasterized,
            )
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

    def __init__(
        self,
        dens: List[Dendrogram],
        method=None,
        metric=None,
        linkage=None,
        get_meta_center=None,
        key=None,
        **kwargs,
    ):
        data = np.vstack([d.center for d in dens])
        super().__init__(
            data,
            method=method,
            metric=metric,
            linkage=linkage,
            get_meta_center=get_meta_center,
            key=key,
            **kwargs,
        )
        self.orig_dens = np.asarray(dens)
        self.dens = np.asarray(dens)[self.reorder_index]
        self.n = len(self.dens)

        self.den_xlim = sum(den.xrange for den in self.dens)
        # how tall the bases end up, and so where the divider sits, depends on
        # the height scale the caller asks for; draw() fills these in
        self.den_ylim = None
        self.divider = None

    def draw(
        self,
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
        meta_ratio=0.2,
        rasterized=False,
        height_scale=None,
        height_transform=None,
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
            The size of meta dendrogram relative to the base dendrogram.
            Exact unless `height_scale` is "minmax".
        height_scale : {"minmax", "group", "shared"}, default: "minmax"
            What the merge heights are measured against. "minmax" stretches
            each group over the full height, so every group looks equally
            deep; "shared" measures them all against the tallest merge
            anywhere, so the heights can be compared between groups.
        height_transform : {None, "sqrt", "log", "rank"} or callable
            Bend the heights without reordering them, to spread out merges
            that bunch up near the leaves. Needs `height_scale` other than
            "minmax".

        .. note::

            With `add_base` on, a meta leaf attaches to the apex of its base
            dendrogram; with it off, there is no apex to attach to and the
            leaf sits at the centre of its chunk instead, so the meta
            dendrogram shifts slightly between the two.

        """

        meta_color = ".1" if meta_color is None else meta_color
        linewidth = 0.7 if linewidth is None else linewidth
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
        elif np.ndim(spacing) == 0:
            spacing = [spacing for _ in range(self.n - 1)]
        elif len(spacing) != self.n - 1:
            raise ValueError(
                f"Got {len(spacing)} spacings for {self.n} dendrograms, "
                f"expected {self.n - 1}, one for each gap between them"
            )

        # mirrors layout._split, so the dendrogram lands on its data chunks
        canvas_size = 1 - np.sum(spacing)
        if canvas_size <= 0:
            raise ValueError(
                f"Spacing {np.sum(spacing)} leaves no room for the dendrograms, "
                f"the total must be less than 1"
            )
        render_xlim = self.den_xlim / canvas_size

        # scipy puts leaf i at icoord 5 + 10i, which __init__ divided by 5.
        # Take the leaf positions from that rather than looking for zeros in y:
        # a merge at height zero (two groups sharing a centroid) is not a leaf.
        skeleton = 1.0 + 2.0 * np.arange(self.n_leaves)

        draw_dens = self.dens if add_meta else self.orig_dens

        # scale the bases first: the divider sits on top of the tallest one
        scales = _base_scales(draw_dens, height_scale, height_transform)
        legacy = scales[0] is None
        for den, scale in zip(draw_dens, scales):
            den.set_height_scale(scale)
        self.den_ylim = max(den.yrange for den in draw_dens)
        self.divider = self.den_ylim * (1.05 if legacy else 1.0)

        if add_base:
            x_start = 0
            for i, den in enumerate(draw_dens):
                den.set_lim(x_start=x_start, y_end=self.divider)
                if i != self.n - 1:
                    x_start = x_start + den.xrange + spacing[i] * render_xlim
            # a meta leaf attaches to the apex of its base dendrogram
            skeleton_x = [den.render_root[0] for den in draw_dens]
        else:
            # with no base to attach to, a meta leaf sits at its chunk centre
            xstart = 0
            skeleton_x = []
            for i, den in enumerate(draw_dens):
                if i > 0:
                    xstart += spacing[i - 1] * render_xlim
                skeleton_x.append(xstart + den.xrange / 2)
                xstart += den.xrange

        # leaves land on their skeleton position, internal nodes interpolate
        # between the two they sit above
        self._render_x_coords = np.interp(self.x_coords, skeleton, skeleton_x)
        meta_scale = _resolve_height_scale(
            height_scale, self.y_coords, height_transform
        )
        if add_base:
            if add_meta:
                if legacy:
                    amplify = self.den_ylim * meta_ratio
                    self._render_y_coords = (
                        self._minmax_heights() * amplify + self.divider
                    )
                else:
                    # meta leaves land exactly on the divider and the apex
                    # exactly meta_ratio above it, so the knob means what it says
                    self.set_height_scale(
                        meta_scale,
                        band=meta_ratio * self.divider,
                        offset=self.divider,
                    )
            else:
                self._render_y_coords = np.full_like(self.y_coords, self.den_ylim)
        else:
            if legacy:
                self._render_y_coords = self._minmax_heights() / 5
            else:
                self.set_height_scale(meta_scale)

        if add_meta:
            # Add meta dendrogram
            self._draw_dendrogram(
                ax,
                orient=orient,
                color=meta_color,
                linewidth=linewidth,
                rasterized=rasterized,
            )

        if divide & add_base & add_meta:
            xmin = np.min(draw_dens[0]._render_x_coords)
            xmax = np.max(draw_dens[-1]._render_x_coords)
            if orient in ["top", "bottom"]:
                ax.hlines(
                    self.divider,
                    xmin,
                    xmax,  # 0, xlim,
                    linestyles=divide_style,
                    color=meta_color,
                    linewidth=linewidth,
                    rasterized=rasterized,
                )
            else:
                ax.vlines(
                    self.divider,
                    xmin,
                    xmax,  # 0, ylim,
                    linestyles=divide_style,
                    color=meta_color,
                    linewidth=linewidth,
                    rasterized=rasterized,
                )

        if add_base:
            for den, color in zip(draw_dens, base_colors):
                # The singleton dendrogram will only be drawn if meta is drawn
                if not den.is_singleton or add_meta:
                    den.draw(
                        ax,
                        orient=orient,
                        add_root=add_meta,
                        color=color,
                        linewidth=linewidth,
                        root_color=meta_color,
                        control_ax=False,
                        rasterized=rasterized,
                    )

        xlim = render_xlim
        # reserve room to avoid clipping of the top
        ylim = np.max(self._render_y_coords) * (1.05 if legacy else 1.02)
        if orient in ["right", "left"]:
            xlim, ylim = ylim, xlim

        ax.set_xlim(0, xlim)
        ax.set_ylim(0, ylim)
        if orient == "left":
            ax.invert_xaxis()
        if orient != "top":
            ax.invert_yaxis()
