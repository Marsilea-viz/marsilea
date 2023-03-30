__all__ = ["ColorMesh", "Colors", "SizedMesh", "MarkerMesh",
           "TextMesh", "PatchMesh"]

import warnings
from itertools import cycle
from typing import Mapping

import numpy as np
import pandas as pd
from legendkit import ColorArt, CatLegend, SizeLegend
from matplotlib.cm import ScalarMappable
from matplotlib.colors import ListedColormap, TwoSlopeNorm, Normalize, \
    is_color_like
from matplotlib.offsetbox import AnchoredText

from .base import RenderPlan
from ..layout import close_ticks
from ..utils import relative_luminance, get_colormap, ECHARTS16, \
    get_canvas_size_by_data

default_label_props = {
    "left": dict(loc="center right", bbox_to_anchor=(0, 0.5)),
    "right": dict(loc="center left", bbox_to_anchor=(1, 0.5)),
    "top": dict(loc="lower center", bbox_to_anchor=(0.5, 1),
                prop=dict(rotation=90)),
    "bottom": dict(loc="upper center", bbox_to_anchor=(0.5, 0),
                   prop=dict(rotation=90)),
}

default_label_loc = {
    "top": "right",
    "bottom": "right",
    "left": "bottom",
    "right": "bottom",
}


def _mask_data(data, mask=None):
    if isinstance(data, pd.DataFrame):
        data = data.to_numpy()
    else:
        data = np.asarray(data)
    if mask is not None:
        data = np.ma.masked_where(np.asarray(mask), data)
    if data.ndim == 1:
        data = data.reshape(1, -1)
    return data


class MeshBase(RenderPlan):
    norm = None
    cmap = None
    render_main = True
    label: str = ""
    label_loc = None
    props = None
    _legend_kws = {}

    def _process_cmap(self, data, vmin, vmax,
                      cmap, norm, center):
        self.cmap = "coolwarm" if cmap is None else cmap
        self.norm = norm

        self.vmin = np.nanmin(data) if vmin is None else vmin
        self.vmax = np.nanmax(data) if vmax is None else vmax

        if norm is None:
            self.norm = Normalize(vmin=self.vmin, vmax=self.vmax)

        if center is not None:
            self.norm = TwoSlopeNorm(center, vmin=vmin, vmax=vmax)

    def _add_label(self, ax):
        if self.side != "main":
            if self.label_loc is None:
                self.label_loc = default_label_loc[self.side]
            label_props = default_label_props[self.label_loc]
            loc = label_props["loc"]
            bbox_to_anchor = label_props['bbox_to_anchor']
            prop = label_props.get('prop')
            if self.props is not None:
                prop.update(self.props)

            title = AnchoredText(self.label, loc=loc,
                                 bbox_to_anchor=bbox_to_anchor,
                                 prop=prop, pad=0.3, borderpad=0,
                                 bbox_transform=ax.transAxes, frameon=False)
            ax.add_artist(title)

    def render(self, axes):
        render_data = self.get_render_data()
        if self.is_split:
            for hax, arr in zip(axes, render_data):
                self.render_ax(hax, arr)

            if self.label_loc in ["top", "left"]:
                label_ax = axes[0]
            else:
                label_ax = axes[-1]
        else:
            self.render_ax(axes, render_data)
            label_ax = axes
        self._add_label(label_ax)

    def set_legends(self, **kwargs):
        self._legend_kws.update(kwargs)


class ColorMesh(MeshBase):
    """Continuous Heatmap

    Parameters
    ----------
    data : np.ndarray, pd.DataFrame
        2D data
    cmap : str or :class:`matplotlib.colors.Colormap`
        The colormap used to map the value to the color
    norm : :class:`matplotlib.colors.Normalize`
        A Normalize instance to map data
    vmin, vmax : number, optional
        Value to determine the value mapping behavior
    center : number, optional
        The value to center on colormap, notice that this is different from
        seaborn; If set, a :class:`matplotlib.colors.TwoSlopeNorm` will be used
        to center the colormap.
    mask : array of bool
        Indicate which cell will be masked and not rendered
    alpha : float
        The transparency value
    linewidth : float
        The width of grid line 
    linecolor : 
        The color of grid line
    annot : bool
        Whether to show the value
    fmt : str
        The format string
    annot_kws : dict
        See :class:`matplotlib.text.Text`
    cbar_kws : dict
        See :class:`matplotlib.colorbar.Colorbar`,
    label : str
        The label of the plot, only show if added to the side plot
    label_loc : str
        Where to add the label
    props : dict
        See :class:`matplotlib.text.Text`
    kwargs :

    Examples
    --------

    .. plot::

        >>> from marsilea.plotter import ColorMesh
        >>> _, ax = plt.subplots(figsize=(5, .5))
        >>> data = np.arange(10)
        >>> ColorMesh(data, cmap="Blues", label="ColorMesh").render(ax)

    .. plot::
        :context: close-figs

        >>> import marsilea as hg
        >>> from marsilea.plotter import ColorMesh
        >>> data = np.random.randn(10, 8)
        >>> h = hg.Heatmap(data)
        >>> h.hsplit(cut=[5])
        >>> h.add_dendrogram("left")
        >>> cmap1, cmap2 = "Purples", "Greens"
        >>> colors1 = ColorMesh(np.arange(10)+1, cmap=cmap1, label=cmap1, annot=True)
        >>> colors2 = ColorMesh(np.arange(10)+1, cmap=cmap2, label=cmap2)
        >>> h.add_right(colors1, size=.2, pad=.05)
        >>> h.add_right(colors2, size=.2, pad=.05)
        >>> h.render()


    """

    def __init__(self, data, cmap=None, norm=None, vmin=None, vmax=None,
                 mask=None, center=None, alpha=None, linewidth=None,
                 linecolor=None, annot=None, fmt=None, annot_kws=None,
                 cbar_kws=None, label=None, label_loc=None, props=None,
                 **kwargs,
                 ):
        self.data = _mask_data(data, mask)
        self.alpha = alpha
        self.linewidth = linewidth
        self.linecolor = linecolor
        self.annotated_texts = self.data
        self.annot = False
        if annot is not None:
            if isinstance(annot, bool):
                self.annot = annot
            else:
                self.annot = True
                self.annotated_texts = annot
        self.fmt = "0" if fmt is None else fmt
        self.annot_kws = {} if annot_kws is None else annot_kws
        self._process_cmap(data, vmin, vmax, cmap, norm, center)

        self.label = label
        self.label_loc = label_loc
        self.props = props
        self._legend_kws = dict(title=self.label)
        if cbar_kws is not None:
            self.set_legends(**cbar_kws)

        self.kwargs = kwargs

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

    def get_render_data(self):
        return self.create_render_datasets(self.data, self.annotated_texts)

    def get_legends(self):
        mappable = ScalarMappable(norm=self.norm, cmap=self.cmap)
        return ColorArt(mappable, **self._legend_kws)

    def render_ax(self, ax, data):
        values, texts = data
        if self.is_flank:
            values = values.T
            texts = texts.T
        mesh = ax.pcolormesh(values, cmap=self.cmap, norm=self.norm,
                             linewidth=self.linewidth,
                             edgecolor=self.linecolor,
                             **self.kwargs, )
        if self.annot:
            self._annotate_text(ax, mesh, texts)
        # set the mesh for legend

        ax.invert_yaxis()
        ax.set_axis_off()


# transform input data to numeric
def encode_numeric(arr, encoder):
    orig_shape = arr.shape
    if np.ma.isMaskedArray(arr):
        re_arr = []
        for e in arr.flatten():
            if e is np.ma.masked:
                re_arr.append(np.nan)
            else:
                re_arr.append(encoder[e])
        re_arr = np.ma.masked_invalid(re_arr)
    else:
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


class Colors(MeshBase):
    """Categorical colors/heatmap

    Parameters
    ----------
    data : np.ndarray
    label : str
    label_loc : {'top', 'bottom', 'left', 'right'}
    palette : dict, array-like
        Could be a mapping of label and colors or an array match
        the shape of data
    cmap : str or :class:`matplotlib.colors.Colormap`
        The colormap used to map the value to the color
    mask : array of bool
        Indicate which cell will be masked and not rendered
    label : str
        The label of the plot, only show if added to the side plot
    label_loc : str
        Where to add the label
    props : dict
        See :class:`matplotlib.text.Text`
    legend_kws : 
        See :func:`legendkit.legend`
    kwargs : 
        Pass to :meth:`pcolormesh <matplotlib.axes.Axes.pcolormesh>`

    """

    def __init__(self, data, palette=None, cmap=None, mask=None,
                 label=None, label_loc=None, props=None, legend_kws=None,
                 **kwargs):
        data = np.asarray(data)
        self.label = label
        self.label_loc = label_loc
        self.props = props
        self.kwargs = kwargs

        self._legend_kws = dict(title=self.label, size=1)
        if legend_kws is not None:
            self.set_legends(**legend_kws)

        encoder = {}
        render_colors = []
        # get unique color
        if palette is not None:
            if isinstance(palette, Mapping):
                self.palette = palette
            else:
                palette = np.asarray(palette)
                self.palette = dict(zip(np.unique(data), palette.flat))

            for i, (label, color) in enumerate(self.palette.items()):
                encoder[label] = i
                render_colors.append(color)

        else:
            if cmap is not None:
                cmap = get_colormap(cmap)
                colors = cmap(np.arange(cmap.N))
            else:
                colors = ECHARTS16

            cats = np.unique(data)
            _enough_colors(len(colors), len(cats))
            palette = {}
            render_colors = []
            for i, (label, color) in enumerate(zip(cats, cycle(colors))):
                encoder[label] = i
                render_colors.append(color)
                palette[label] = color
            self.palette = palette

        self.render_cmap = ListedColormap(render_colors)
        self.vmax = len(render_colors)
        # Encode data into cmap range
        encode_data = encode_numeric(data, encoder)
        self.data = _mask_data(encode_data, mask=mask)
        # If the data is numeric, we don't change it
        if np.issubdtype(data.dtype, np.number):
            self.cluster_data = data
        else:
            self.cluster_data = encode_data

    def get_legends(self):
        colors = []
        labels = []
        for label, color in self.palette.items():
            labels.append(label)
            colors.append(color)
        return CatLegend(colors=colors, labels=labels, **self._legend_kws)

    def render_ax(self, ax, data):
        if self.is_flank:
            data = data.T
        ax.pcolormesh(data, cmap=self.render_cmap,
                      vmin=0, vmax=self.vmax, **self.kwargs)
        ax.set_axis_off()
        ax.invert_yaxis()


class SizedMesh(MeshBase):
    """Mesh for sized elements

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
    cmap : str or :class:`matplotlib.colors.Colormap`
        The colormap used to map the value to the color
    norm : :class:`matplotlib.colors.Normalize`
        A Normalize instance to map data
    vmin, vmax : number, optional
        Value to determine the value mapping behavior
    center : number, optional
        The value to center on colormap, notice that this is different from
        seaborn; If set, a :class:`matplotlib.colors.TwoSlopeNorm` will be used
        to center the colormap.
    alpha : float
        The transparency value
    sizes : tuple of float
        The range of the size of elements
    size_norm : :class:`matplotlib.colors.Normalize`
        A Normalize instance to map size
    edgecolor : color
        The border color of each elements
    linewidth : float
        The width of the border of each elements
    frameon : bool
        Whether to draw a frame
    palette : dict
        Use to map color if input categorical data
    marker : str
        See :mod:`matplotlib.markers`
    label : str
        The label of the plot, only show if added to the side plot
    label_loc : str
        Where to add the label
    props : dict
        See :class:`matplotlib.text.Text`
    legend : bool, default: True
        Whether to add a legend
    size_legend_kws : dict
        Control the size legend, See :func:`legendkit.size_legend`
    color_legend_kws : dict
        Control the color legend, See :func:`legendkit.legend`
    kwargs :

    """

    def __init__(self, size, color=None, cmap=None, norm=None,
                 vmin=None, vmax=None, alpha=None,
                 center=None, sizes=(1, 200), size_norm=None,
                 edgecolor=None, linewidth=1,
                 frameon=True, palette=None, marker="o",
                 label=None, label_loc=None, props=None,
                 legend=True, size_legend_kws=None, color_legend_kws=None,
                 **kwargs):
        # normalize size
        size = np.asarray(size)
        if size_norm is None:
            size_norm = Normalize()
            size_norm.autoscale(size)
        self.size_norm = size_norm
        self.orig_size = size
        self.size_matrix = size_norm(size) * (sizes[1] - sizes[0]) + sizes[0]
        self.color = None
        self.color2d = None
        self.palette = palette
        self.marker = marker
        self.legend = legend
        self.color_legend_kws = {} if color_legend_kws is None else color_legend_kws
        self.size_legend_kws = {} if size_legend_kws is None else size_legend_kws
        self._has_colormesh = False
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
                                       norm, center)
                    self.color2d = color
                self._has_colormesh = True
        self.alpha = alpha
        self.frameon = frameon
        self.edgecolor = edgecolor
        self.linewidth = linewidth
        self.label = label
        self.label_loc = label_loc
        self.props = props
        self.kwargs = kwargs

        self._collections = None

    def update_main_canvas_size(self):
        return get_canvas_size_by_data(self.orig_size.shape)

    def get_legends(self):
        if not self.legend:
            return None
        if self.color is not None:
            size_color = self.color
        else:
            size_color = "black"
        handler_kw = dict(edgecolor=self.edgecolor,
                          linewidth=self.linewidth)
        options = dict(
            colors=size_color,
            dtype=self.orig_size.dtype,
            handle=self.marker,
            show_at=(.1, .25, .5, .75, 1.),
            handler_kw=handler_kw)
        options.update(self.size_legend_kws)
        size_legend = SizeLegend(self.size_matrix,
                                 array=self.orig_size,
                                 **options
                                 )

        if (self._has_colormesh) & (self.color != "none"):
            if self.palette is not None:
                labels, colors = [], []
                for label, c in self.palette.items():
                    labels.append(label)
                    colors.append(c)
                options = dict(
                    size=1,
                    handle=self.marker,
                    handler_kw=handler_kw,
                    frameon=False,
                )
                options.update(self.color_legend_kws)
                color_legend = CatLegend(labels=labels, colors=colors,
                                         **options
                                         )
            else:
                mappable = ScalarMappable(norm=self.norm, cmap=self.cmap)
                color_legend = ColorArt(self._collections,
                                        **self.color_legend_kws)
            return [size_legend, color_legend]
        else:
            return size_legend

    def get_render_data(self):
        return self.create_render_datasets(self.size_matrix, self.color2d)

    def render_ax(self, ax, data):
        size, color = data
        if self.is_flank:
            size = size.T
            color = color.T
        Y, X = size.shape
        xticks = np.arange(X) + 0.5
        yticks = np.arange(Y) + 0.5
        xv, yv = np.meshgrid(xticks, yticks)

        options = dict(s=size, edgecolor=self.edgecolor,
                       linewidths=self.linewidth, marker=self.marker)

        if self.color is not None:
            options['c'] = self.color
        else:
            options.update(dict(c=color, norm=self.norm, cmap=self.cmap))
        self._collections = ax.scatter(xv, yv, **options, **self.kwargs)

        close_ticks(ax)
        if not self.frameon:
            ax.set_axis_off()
        ax.set_xlim(0, xticks[-1] + 0.5)
        ax.set_ylim(0, yticks[-1] + 0.5)
        ax.invert_yaxis()


# TODO: A patch mesh
class PatchMesh(MeshBase):
    pass


class MarkerMesh(MeshBase):
    """The mesh that draw marker shape

    Parameters
    ----------

    data : np.ndarray
        Must be bool matrix to indicate if a marker is drawn at specific cell
    color : color
        The color of the marker.
    marker : str
        See :mod:`matplotlib.markers`
    size : int
        The of marker in fontsize unit
    label : str
        The label of the plot, only show when added to the side plot
    label_loc : str
        The position of the label
    props : dict
        See :class:`matplotlib.text.Text`
    kwargs :


    Examples
    --------

    .. plot::
        :context: close-figs

        >>> from marsilea.plotter import MarkerMesh
        >>> data = np.random.randn(10, 10) > 0
        >>> _, ax = plt.subplots(figsize=(3, 3))
        >>> MarkerMesh(data, color="darkgreen", marker="x", size=50).render(ax)

    """
    render_main = True

    def __init__(self, data, color="black", marker="*", size=35,
                 label=None, label_loc=None, props=None, **kwargs):
        self.data = np.asarray(data)
        self.color = color
        self.marker = marker
        self.label = label
        self.label_loc = label_loc
        self.props = props
        self.kwargs = kwargs
        self.marker_size = size

    def get_legends(self):
        return CatLegend(colors=[self.color], labels=[self.label],
                         handle=self.marker, draw=False)

    def render_ax(self, ax, data):
        Y, X = data.shape
        xticks = np.arange(X) + 0.5
        yticks = np.arange(Y) + 0.5
        yv, xv = np.where(data)

        ax.scatter(xv + .5, yv + .5, s=self.marker_size,
                   c=self.color, marker=self.marker, **self.kwargs)

        close_ticks(ax)
        ax.set_xlim(0, xticks[-1] + 0.5)
        ax.set_ylim(0, yticks[-1] + 0.5)
        ax.invert_yaxis()


# TODO: Maybe a text mesh
class TextMesh(MeshBase):
    render_main = True
