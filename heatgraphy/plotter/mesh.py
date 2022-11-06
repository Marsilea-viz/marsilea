import warnings
from itertools import cycle
from typing import Mapping, Iterable

import numpy as np
from matplotlib.colors import ListedColormap, TwoSlopeNorm, Normalize, \
    is_color_like
from matplotlib.offsetbox import AnchoredText
from legendkit import ColorArt, CatLegend, ListLegend, SizeLegend

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
    norm = None
    cmap = None

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

        if norm is None:
            self.norm = Normalize(vmin=self.vmin, vmax=self.vmax)

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
        if cbar_kws is None:
            cbar_kws = {}
        self._legend_kws = cbar_kws

    def get_render_data(self):
        data = self.data
        texts = self.annotated_texts
        if self.h:
            data = data.T
            texts = texts.T
        if not self.is_deform:
            return data, texts

        data = self.deform_func(data)
        texts = self.deform_func(texts)
        if self.deform.is_split:
            return [d for d in zip(data, texts)]
        else:
            return data, texts

    def render_ax(self, ax, data):
        values, texts = data
        mesh = ax.pcolormesh(values, cmap=self.cmap, norm=self.norm,
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
        return ColorArt(self._mesh, **self._legend_kws)


# transform input data to numeric
def encode_numeric(arr, encoder):
    orig_shape = arr.shape
    re_arr = [encoder[e] for e in arr.flatten()]
    re_arr = np.array(re_arr).reshape(orig_shape)
    return re_arr


def _enough_colors(n_colors, n_cats):
    # Inform the user if the same color
    # will be used more than once
    if n_colors < n_cats:
        warnings.warn(f"Current colormap has only {n_colors} colors "
                      f"which is less that your input "
                      f"with {n_cats} elements")


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
                 label=None, label_loc=None, props=None, ):
        data = np.asarray(data)
        if data.ndim == 1:
            data = data.reshape(1, -1)
        self.data = data
        self.label = label
        self.label_loc = label_loc
        self.props = props

        encoder = {}
        render_colors = []
        # get unique color
        if palette is not None:
            if isinstance(palette, Mapping):
                self.palette = palette
            else:
                self.palette = dict(zip(data.flat, palette.flat))

            for i, (label, color) in enumerate(palette.items()):
                encoder[label] = i
                render_colors.append(color)

        else:
            if cmap is not None:
                colors = get_colormap(cmap).colors
            else:
                colors = ECHARTS16

            cats = np.unique(data)
            _enough_colors(len(colors), len(cats))
            palette = {}
            encoder = {}
            render_colors = []
            for i, (label, color) in enumerate(zip(cats, cycle(colors))):
                encoder[label] = i
                render_colors.append(color)
                palette[label] = color
            self.palette = palette

        self.render_cmap = ListedColormap(render_colors)
        self.vmax = len(render_colors)
        self.data = encode_numeric(data, encoder)

    label_props = {
        "left": dict(loc="center right", bbox_to_anchor=(0, 0.5)),
        "right": dict(loc="center left", bbox_to_anchor=(1, 0.5)),
        "top": dict(loc="lower center", bbox_to_anchor=(0.5, 1),
                    prop=dict(rotation=90)),
        "bottom": dict(loc="upper center", bbox_to_anchor=(0.5, 0),
                       prop=dict(rotation=90)),
    }

    def _add_label(self, ax):
        if self.side != "main":
            label_props = self.label_props[self.label_loc]
            loc = label_props["loc"]
            bbox_to_anchor = label_props['bbox_to_anchor']
            prop = label_props.get('prop')
            if self.props is not None:
                prop = self.props

            title = AnchoredText(self.label, loc=loc,
                                 bbox_to_anchor=bbox_to_anchor,
                                 prop=prop, pad=0.3, borderpad=0,
                                 bbox_transform=ax.transAxes, frameon=False)
            ax.add_artist(title)

    def get_legends(self):
        colors = []
        labels = []
        for label, color in self.palette.items():
            labels.append(label)
            colors.append(color)
        return CatLegend(colors=colors, labels=labels, size=1,
                         title=self.label)

    def get_render_data(self):
        data = self.data
        if self.h:
            data = self.data.T

        if not self.is_deform:
            return data

        return self.deform_func(data)

    def render_ax(self, ax, data):
        ax.pcolormesh(data, cmap=self.render_cmap, vmin=0, vmax=self.vmax)
        ax.set_axis_off()
        if self.h:
            ax.invert_yaxis()

    default_label_loc = {
        "top": "right",
        "bottom": "right",
        "left": "bottom",
        "right": "bottom",
    }

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
    """Circle/Pie mesh

    .. note::
        If encode color as categorical data, `palette` must be used
        to assign color for each category.

    Parameters
    ----------
    size : 2d array
        Control the radius of circles, must be numeric
    color: color-like or 2d array
        The color of circles, could be numeric / categorical matrix
        If using one color name, all circles will have the same color.



    """

    def __init__(self, size, color=None, cmap=None, norm=None,
                 vmin=None, vmax=None, alpha=None,
                 center=None, robust=None,
                 sizes=(1, 200), size_norm=None,
                 edgecolor=None, linewidth=1,
                 frameon=True,
                 palette=None, ):
        # normalize size
        size = np.asarray(size)
        if size_norm is None:
            size_norm = Normalize()
            size_norm.autoscale(size)
        self.orig_size = size
        self.size = size_norm(size) * (sizes[1] - sizes[0]) + sizes[0]
        self.color = None
        self.color2d = None
        self.palette = palette
        # process color
        # By default, the circles colors are uniform
        if color is None:
            color = "C0"
        if color is not None:
            if is_color_like(color):
                self.color = color
                self.color2d = np.repeat(color, size.size).reshape(size.shape)
            else:
                color = np.asarray(color)
                # categorical circle color
                if palette is not None:
                    encoder = {}
                    render_colors = []
                    for i, (label, c) in enumerate(palette.items()):
                        encoder[label] = i
                        render_colors.append(c)
                    self.cmap = ListedColormap(render_colors)
                    self.color2d = encode_numeric(color, encoder)
                else:
                    self._process_cmap(color, vmin, vmax, cmap,
                                       norm, center, robust)
                    self.color2d = color
        self.alpha = alpha
        self.frameon = frameon
        self.edgecolor = edgecolor
        self.linewidth = linewidth

        self._collections = None

    def get_legends(self):
        if self.color is not None:
            size_color = self.color
        else:
            size_color = "black"
        handler_kw = dict(edgecolor=self.edgecolor,
                          linewidth=self.linewidth)
        size_legend = SizeLegend(self.size,
                                 array=self.orig_size,
                                 colors=size_color,
                                 dtype=self.orig_size.dtype,
                                 handler_kw=handler_kw,
                                 )

        if self.color2d is not None:
            if self.palette is not None:
                labels, colors = [], []
                for label, c in self.palette.items():
                    labels.append(label)
                    colors.append(c)
                color_legend = CatLegend(labels=labels, colors=colors,
                                         size="large",
                                         handle="circle",
                                         handle_kw=handler_kw,
                                         frameon=True,
                                         )
            else:
                color_legend = ColorArt(self._collections)
            return [size_legend, color_legend]
        else:
            return size_legend

    def get_render_data(self):
        size = self.size
        color = self.color2d
        if self.h:
            size = size.T
            color = color.T
        if not self.is_deform:
            return size, color

        size = self.deform_func(size)
        color = self.deform_func(color)
        if self.deform.is_split:
            return [d for d in zip(size, color)]
        else:
            return size, color

    def render_ax(self, ax, data):
        size, color = data
        Y, X = size.shape
        xticks = np.arange(X) + 0.5
        yticks = np.arange(Y) + 0.5
        xv, yv = np.meshgrid(xticks, yticks)

        if self.color is not None:
            ax.scatter(xv, yv, s=size, c=self.color, edgecolor=self.edgecolor,
                       linewidths=self.linewidth)
        else:
            self._collections = ax.scatter(xv, yv, s=size, c=color,
                                           norm=self.norm, cmap=self.cmap,
                                           edgecolor=self.edgecolor,
                                           linewidths=self.linewidth)

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

    def get_render_data(self):
        data = self.data
        if self.h:
            data = self.data.T

        if not self.is_deform:
            return data

        if self.mode == "cell":
            return self.deform_func(data)
        else:
            trans_layers = [
                self.deform_func(layer) for layer in self.data]
            if self.deform.is_split:
                return [chunk for chunk in zip(*trans_layers)]
            else:
                return trans_layers

    def get_legends(self):
        if self.mode == "cell":
            handles = list(self.pieces_mapper.values())
        else:
            handles = self.pieces
        labels = [h.get_label() for h in handles]
        handle_map = {h: h for h in handles}
        return ListLegend(handles=handles, labels=labels,
                          handler_map=handle_map)

    def render_ax(self, ax, data):
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
