import warnings
from itertools import cycle
from typing import Mapping, Iterable

import numpy as np
from matplotlib import cm
from matplotlib.axes import Axes
from matplotlib.colors import ListedColormap, TwoSlopeNorm, Normalize
from matplotlib.offsetbox import AnchoredText
from legendkit import ColorArt

from .base import RenderPlan
from ..layout import close_ticks
from ..utils import relative_luminance, get_colormap

ECHARTS16 = [
    "#5470c6", "#91cc75", "#fac858", "#ee6666",
    "#9a60b4", "#73c0de", "#3ba272", "#fc8452",
    "#27727b", "#ea7ccc", "#d7504b", "#e87c25",
    "#b5c334", "#fe8463", "#26c0c0", "#f4e001"
]


def _empty(x):
    return x


class _MeshBase:
    annot = False
    annotated_texts = None
    fmt = "0"
    annot_kws = {}

    def _process_cmap(self, data, vmin, vmax,
                      cmap, norm, center, robust):
        self.cmap = "coolwarm" if cmap is None else cmap
        self.norm = norm
        self.vmin = vmin
        self.vmax = vmax

        if robust:
            if isinstance(robust, bool):
                head, tail = (2, 98)
            else:
                head, tail = robust
            if vmin is None:
                self.vmin = np.nanpercentile(data, head)
            if vmax is None:
                self.vmax = np.nanpercentile(data, tail)
        else:
            self.vmin = np.nanmin(data) if vmin is None else vmin
            self.vmax = np.nanmax(data) if vmax is None else vmax

        if center is not None:
            self.norm = TwoSlopeNorm(center, vmin=vmin, vmax=vmax)

    def _annotate_text(self, ax, mesh, texts):
        """Add textual labels with the value in each cell."""
        mesh.update_scalarmappable()
        height, width = texts.shape
        xpos, ypos = np.meshgrid(np.arange(width) + .5, np.arange(height) + .5)
        for x, y, m, color, val in zip(xpos.flat, ypos.flat,
                                       mesh.get_array(), mesh.get_facecolors(),
                                       texts.flat):
            if m is not np.ma.masked:
                lum = relative_luminance(color)
                text_color = ".15" if lum > .408 else "w"
                annotation = ("{:" + self.fmt + "}").format(val)
                text_kwargs = dict(color=text_color, ha="center", va="center")
                text_kwargs.update(self.annot_kws)
                ax.text(x, y, annotation, **text_kwargs)


class ColorMesh(RenderPlan, _MeshBase):

    def __init__(self, data, cmap=None, norm=None, vmin=None, vmax=None,
                 center=None, robust=None,
                 alpha=None,
                 linewidth=None, linecolor=None,
                 annot=None, fmt=None, annot_kws=None, cbar_kws=None
                 ):
        data = np.asarray(data)
        if data.ndim == 1:
            data = data.reshape(1, -1)
        self.data = data
        self.alpha = alpha
        self.linewidth = linewidth
        self.linecolor = linecolor
        self.annotated_texts = data
        if annot is not None:
            if isinstance(annot, bool):
                self.annot = annot
            else:
                self.annot = True
                self.annotated_texts = annot
        if fmt is not None:
            self.fmt = fmt
        if annot_kws is not None:
            self.annot_kws = annot_kws
        self._process_cmap(data, vmin, vmax, cmap, norm, center, robust)
        self._mesh = None
        self._legend_kws = {}

    def get_render_data(self):
        data = self.deform_func(self.data)
        texts = self.deform_func(self.annotated_texts)
        if self.deform.is_split:
            return [d for d in zip(data, texts)]
        else:
            return data, texts

    def render_ax(self, ax, data):
        values, texts = data
        mesh = ax.pcolormesh(values, cmap=self.cmap, norm=self.norm,
                             vmin=self.vmin, vmax=self.vmax,
                             linewidth=self.linewidth,
                             edgecolor=self.linecolor
                             )
        if self.annot:
            self._annotate_text(ax, mesh, texts)
        # set the mesh for legend
        self._mesh = mesh

        ax.invert_yaxis()
        ax.set_axis_off()

    def set_legends(self, **kwargs):
        self._legend_kws = kwargs

    def get_legends(self):
        return ColorArt(self._mesh, height=4, width=1, fontsize=12,
                        **self._legend_kws)


class Colors(RenderPlan):
    """Categorical colors/heatmap

    Parameters
    ----------
    data : np.ndarray
    label : str
    label_loc : {'top', 'bottom', 'left', 'right'}
    palette : dict, array-like
        Could be a mapping of label and colors or an array match
        the shape of data
    cmap:

    """
    def __init__(self, data, palette=None, cmap=None,
                 label=None, label_loc=None, props=None,):
        data = np.asarray(data)
        if data.ndim == 1:
            data = data.reshape(1, -1)
        self.data = data
        self.label = label
        self.label_loc = label_loc
        self.props = props
        # get unique color
        if palette is not None:
            if isinstance(palette, Mapping):
                self.palette = palette
            else:
                self.palette = dict(zip(data.flat, palette.flat))

            self.mapper = {}
            colors = []
            for i, (label, color) in enumerate(palette.items()):
                self.mapper[label] = i
                colors.append(color)
            self.render_cmap = ListedColormap(colors)
            self.vmax = len(colors)

        else:
            if cmap is not None:
                colors = get_colormap(cmap).colors
            else:
                colors = ECHARTS16

            # data to int
            cats = np.unique(self.data)
            self.vmax = len(cats)
            # Inform the user if the same color
            # will be used more than once
            if len(colors) < self.vmax:
                warnings.warn(f"Current colormap has only {cmap.N} colors "
                              f"which is less that your input "
                              f"with {self.vmax} elements")
            self.mapper = {c: i for i, c in enumerate(cats)}
            self.render_cmap = ListedColormap(
                [c for c, _ in zip(cycle(colors), range(self.vmax))])
        self.data = self._to_numeric(data)

    # transform input data to numeric
    def _to_numeric(self, arr):
        orig_shape = arr.shape
        re_arr = [self.mapper[e] for e in arr.flatten()]
        re_arr = np.array(re_arr).reshape(orig_shape)
        return re_arr

    label_props = {
        "left": dict(loc="center right", bbox_to_anchor=(0, 0.5)),
        "right": dict(loc="center left", bbox_to_anchor=(1, 0.5)),
        "top": dict(loc="lower center", bbox_to_anchor=(0.5, 1),
                    prop=dict(rotation=90)),
        "bottom": dict(loc="upper center", bbox_to_anchor=(0.5, 0),
                       prop=dict(rotation=90)),
    }

    def _add_label(self, ax):
        label_props = self.label_props[self.label_loc]
        loc = label_props["loc"]
        bbox_to_anchor = label_props['bbox_to_anchor']
        prop = label_props.get('prop')
        if self.props is not None:
            prop = self.props

        title = AnchoredText(self.label,
                             loc=loc,
                             bbox_to_anchor=bbox_to_anchor,
                             prop=prop,
                             pad=0.3,
                             borderpad=0,
                             bbox_transform=ax.transAxes,
                             frameon=False)
        ax.add_artist(title)

    default_label_loc = {
        "top": "right",
        "bottom": "right",
        "left": "bottom",
        "right": "bottom",
    }

    def get_render_data(self):
        if self.is_deform:
            data = self.data
            if self.h:
                data = self.data.T
            return self.deform_func(data)
        else:
            return self.data

    def render_ax(self, ax: Axes, data):
        ax.pcolormesh(data, cmap=self.render_cmap, vmin=0, vmax=self.vmax)
        ax.set_axis_off()
        if self.h:
            ax.invert_yaxis()

    def render(self, axes):
        render_data = self.get_render_data()
        if self.label_loc is None:
            self.label_loc = self.default_label_loc[self.side]
        if self.is_split(axes):
            if self.label_loc in ["top", "left"]:
                self._add_label(axes[0])
            else:
                self._add_label(axes[-1])
            for hax, arr in zip(axes, render_data):
                self.render_ax(hax, arr)
        else:
            self.render_ax(axes, render_data)
            if self.label is not None:
                self._add_label(axes)


class CircleMesh(RenderPlan, _MeshBase):

    def __init__(self, size, color, cmap=None, norm=None,
                 vmin=None, vmax=None, alpha=None,
                 center=None, robust=None,
                 sizes=(1, 200), size_norm=None,
                 edgecolor=None, linewidth=1,
                 frameon=True):

        self.color = color
        if size_norm is None:
            size_norm = Normalize()
            size_norm.autoscale(size)
        self.size = size_norm(size) * (sizes[1] - sizes[0]) + sizes[0]
        self._process_cmap(color, vmin, vmax, cmap, norm, center, robust)
        self.alpha = alpha
        self.frameon = frameon
        self.edgecolor = edgecolor
        self.linewidth = linewidth

    def render_ax(self, ax, data):
        size, color = data
        Y, X = size.shape
        xticks = np.arange(X) + 0.5
        yticks = np.arange(Y) + 0.5
        xv, yv = np.meshgrid(xticks, yticks)
        ax.scatter(
            xv, yv, s=size, c=color,
            norm=self.norm, cmap=self.cmap,
            vmin=self.vmin, vmax=self.vmax,
            edgecolor=self.edgecolor, linewidths=self.linewidth
        )

        close_ticks(ax)
        if not self.frameon:
            ax.set_axis_off()
        ax.set_xlim(0, xticks[-1] + 0.5)
        ax.set_ylim(0, yticks[-1] + 0.5)
        ax.invert_yaxis()


class LayersMesh(RenderPlan):

    def __init__(self,
                 data=None,
                 layers=None,
                 pieces=None,
                 shrink=(.9, .9)
                 ):
        # render one layer
        # with different elements
        if data is not None:
            self.data = data
            if not isinstance(pieces, Mapping):
                msg = f"Expect pieces to be dict " \
                      f"but found {type(pieces)} instead."
                raise TypeError(msg)
            self.pieces_mapper = pieces
            self.mode = "cell"
        # render multiple layers
        # each layer is an elements
        else:
            self.data = layers
            if not isinstance(pieces, Iterable):
                msg = f"Expect pieces to be list " \
                      f"but found {type(pieces)} instead."
                raise TypeError(msg)
            self.pieces = pieces
            self.mode = "layer"
        self.x_offset = (1 - shrink[0]) / 2
        self.y_offset = (1 - shrink[1]) / 2
        self.width = shrink[0]
        self.height = shrink[1]

    def render_ax(self, ax: Axes, data):
        if self.mode == "layer":
            Y, X = data[0].shape
        else:
            Y, X = data.shape
        ax.set_axis_off()
        ax.set_xlim(0, X)
        ax.set_ylim(0, Y)
        if self.mode == "layer":
            for layer, piece in zip(data, self.pieces):
                for iy, row in enumerate(layer):
                    for ix, v in enumerate(row):
                        if v:
                            art = piece.draw(ix + self.x_offset,
                                             iy + self.y_offset,
                                             self.width, self.height)
                            ax.add_artist(art)
        else:
            for iy, row in enumerate(data):
                for ix, v in enumerate(row):
                    piece = self.pieces_mapper[v]
                    art = piece.draw(ix + self.x_offset, iy + self.y_offset,
                                     self.width, self.height)
                    ax.add_artist(art)
