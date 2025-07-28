__all__ = ["ColorMesh", "Colors", "SizedMesh", "MarkerMesh", "TextMesh", "PatchMesh"]

import numpy as np
import pandas as pd
import warnings
from itertools import cycle
from legendkit import ColorArt, CatLegend, SizeLegend
from matplotlib.cm import ScalarMappable
from matplotlib.colors import ListedColormap, TwoSlopeNorm, Normalize, is_color_like
from typing import Mapping

from ._utils import _format_label
from .base import RenderPlan
from ..layout import close_ticks
from ..utils import relative_luminance, get_colormap, ECHARTS16, get_canvas_size_by_data


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
    _legend_kws = {}

    def _process_cmap(self, data, vmin, vmax, cmap, norm, center):
        self.cmap = "coolwarm" if cmap is None else cmap
        self.norm = norm

        self.vmin = np.nanmin(data) if vmin is None else vmin
        self.vmax = np.nanmax(data) if vmax is None else vmax

        if norm is None:
            self.norm = Normalize(vmin=self.vmin, vmax=self.vmax)

        if center is not None:
            self.norm = TwoSlopeNorm(center, vmin=vmin, vmax=vmax)

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
    mask : array-like
        A bool matrix indicates which cell will be masked and not rendered
    alpha : float
        The transparency value
    linewidth : float
        The width of grid line
    linecolor : color
        The color of grid line
    annot : bool, array-like
        Whether to show the value / The text to show in each cell
    fmt : str, callable
        The format string or a function to format the value
    annot_kws : dict
        See :class:`matplotlib.text.Text`
    cbar_kws : dict
        See :class:`matplotlib.colorbar.Colorbar`,
    label : str
        The label of the plot, only show if added to the side plot
    label_loc : {'top', 'bottom', 'left', 'right'}
        Where to add the label
    label_props : dict
        See :class:`matplotlib.text.Text`
    kwargs :

    See Also
    --------
        :class:`marsilea.Heatmap`

    Examples
    --------

    .. plot::
        :context: close-figs

        >>> import marsilea as ma
        >>> from marsilea.plotter import ColorMesh
        >>> _, ax = plt.subplots(figsize=(5, 0.5))
        >>> ColorMesh(np.arange(10), cmap="Blues").render(ax)

    .. plot::
        :context: close-figs

        >>> data = np.random.randn(10, 8)
        >>> h = ma.Heatmap(data)
        >>> h.cut_rows(cut=[5])
        >>> h.add_dendrogram("left")
        >>> cmap1, cmap2 = "Purples", "Greens"
        >>> colors1 = ColorMesh(np.arange(10) + 1, cmap=cmap1, label=cmap1, annot=True)
        >>> colors2 = ColorMesh(np.arange(10) + 1, cmap=cmap2, label=cmap2)
        >>> h.add_right(colors1, size=0.2, pad=0.05)
        >>> h.add_right(colors2, size=0.2, pad=0.05)
        >>> h.render()


    """

    def __init__(
        self,
        data,
        cmap=None,
        norm=None,
        vmin=None,
        vmax=None,
        mask=None,
        center=None,
        alpha=None,
        linewidth=None,
        linecolor=None,
        annot=None,
        fmt=None,
        annot_kws=None,
        cbar_kws=None,
        label=None,
        label_loc=None,
        label_props=None,
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
        self.fmt = ".2g" if fmt is None else fmt
        self.annot_kws = {} if annot_kws is None else annot_kws
        self._process_cmap(data, vmin, vmax, cmap, norm, center)

        self.set_label(label, label_loc, label_props)
        self.set_data(self.data, self.annotated_texts)
        self._legend_kws = dict(title=self.label)
        if cbar_kws is not None:
            self.set_legends(**cbar_kws)

        self.kwargs = kwargs

    def _annotate_text(self, ax, mesh, texts):
        """Add textual labels with the value in each cell."""
        mesh.update_scalarmappable()
        height, width = texts.shape
        xpos, ypos = np.meshgrid(np.arange(width) + 0.5, np.arange(height) + 0.5)
        for x, y, m, color, val in zip(
            xpos.flat,
            ypos.flat,
            mesh.get_array().flatten(),
            mesh.get_facecolors(),
            texts.flat,
        ):
            if m is not np.ma.masked:
                lum = relative_luminance(color)
                text_color = ".15" if lum > 0.408 else "w"
                annotation = _format_label(val, self.fmt)
                text_kwargs = dict(color=text_color, ha="center", va="center")
                text_kwargs.update(self.annot_kws)
                ax.text(x, y, annotation, **text_kwargs)

    def get_legends(self):
        mappable = ScalarMappable(norm=self.norm, cmap=self.cmap)
        return ColorArt(mappable, **self._legend_kws)

    def render_ax(self, spec):
        values, texts = spec.data
        ax = spec.ax
        if self.is_flank:
            values = values.T
            texts = texts.T
        mesh = ax.pcolormesh(
            values,
            cmap=self.cmap,
            norm=self.norm,
            linewidth=self.linewidth,
            edgecolor=self.linecolor,
            **self.kwargs,
        )
        if self.annot:
            self._annotate_text(ax, mesh, texts)
        # set the mesh for legend

        if not ax.yaxis_inverted():
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
        warnings.warn(
            f"Current colormap has only {n_colors} colors "
            f"which is less that your input "
            f"with {n_cats} elements"
        )


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
    label_props : dict
        See :class:`matplotlib.text.Text`
    legend_kws :
        See :class:`legendkit.legend`
    kwargs :
        Pass to :meth:`pcolormesh <matplotlib.axes.Axes.pcolormesh>`

    See Also
    --------
        :class:`marsilea.CatHeatmap`

    Examples
    --------

    .. plot::
        :context: close-figs

        >>> import marsilea as ma
        >>> from marsilea.plotter import Colors
        >>> _, ax = plt.subplots(figsize=(5, 0.5))
        >>> data = np.random.choice(["A", "B", "C"], 10)
        >>> Colors(data).render(ax)

    .. plot::
        :context: close-figs

        >>> h = ma.Heatmap(np.random.randn(10, 8))
        >>> h.cut_rows(cut=[5])
        >>> h.add_dendrogram("left")
        >>> color = Colors(data, label="Colors")
        >>> h.add_right(color, size=0.2, pad=0.05)
        >>> h.render()


    """

    def __init__(
        self,
        data,
        palette=None,
        cmap=None,
        mask=None,
        linewidth=None,
        linecolor=None,
        label=None,
        label_loc=None,
        label_props=None,
        legend_kws=None,
        **kwargs,
    ):
        data = np.asarray(data)
        self.set_label(label, label_loc, label_props)
        self.linewidth = linewidth
        self.linecolor = linecolor
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
            cats = np.unique(data)
            if cmap is not None:
                cmap = get_colormap(cmap)
                colors = cmap(np.linspace(0, 1, len(cats)))
            else:
                colors = []
                for i, c in enumerate(cycle(ECHARTS16)):
                    colors.append(c)
                    if i == len(cats):
                        break

            _enough_colors(len(colors), len(cats))
            palette = {}
            render_colors = []
            for i, (label, color) in enumerate(zip(cats, cycle(colors))):
                encoder[label] = i
                render_colors.append(color)
                palette[label] = color
            self.palette = palette

        self.render_cmap = ListedColormap(render_colors)
        self.vmax = len(render_colors) - 1
        # Encode data into cmap range
        encode_data = encode_numeric(data, encoder)
        self.set_data(_mask_data(encode_data, mask=mask))
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

    def render_ax(self, spec):
        ax = spec.ax
        data = spec.data

        if self.is_flank:
            data = data.T
        ax.pcolormesh(
            data,
            cmap=self.render_cmap,
            linewidth=self.linewidth,
            edgecolor=self.linecolor,
            vmin=0,
            vmax=self.vmax,
            **self.kwargs,
        )
        ax.set_axis_off()
        if not ax.yaxis_inverted():
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
    grid : bool
        Whether to draw grid
    grid_color : color
        The color of grid
    grid_linewidth : float
        The width of grid line
    palette : dict
        Use to map color if input categorical data
    marker : str
        See :mod:`matplotlib.markers`
    label : str
        The label of the plot, only show if added to the side plot
    label_loc : {'top', 'bottom', 'left', 'right'}
        Where to add the label
    label_props : dict
        See :class:`matplotlib.text.Text`
    legend : bool, default: True
        Whether to add a legend
    size_legend_kws : dict
        Control the size legend, See :class:`legendkit.size_legend`
    color_legend_kws : dict
        Control the color legend, See :class:`legendkit.colorart`
    kwargs : dict
        Pass to :meth:`matplotlib.axes.Axes.scatter`

    See Also
    --------
        :class:`marsilea.SizedHeatmap`

    Examples
    --------

    .. plot::
        :context: close-figs

        >>> import marsilea as ma
        >>> from marsilea.plotter import SizedMesh
        >>> _, ax = plt.subplots(figsize=(5, 0.5))
        >>> size, color = np.random.rand(1, 10), np.random.rand(1, 10)
        >>> SizedMesh(size, color).render(ax)

    .. plot::
        :context: close-figs

        >>> h = ma.Heatmap(np.random.randn(10, 8))
        >>> h.cut_rows(cut=[5])
        >>> h.add_dendrogram("left")
        >>> mesh = SizedMesh(size, color, marker="*", label="SizedMesh")
        >>> h.add_right(mesh, size=0.2, pad=0.05)
        >>> h.render()

    """

    def __init__(
        self,
        size,
        color=None,
        cmap=None,
        norm=None,
        vmin=None,
        vmax=None,
        alpha=None,
        center=None,
        sizes=(1, 200),
        size_norm=None,
        edgecolor=None,
        linewidth=1,
        frameon=True,
        grid=False,
        grid_color=".8",
        grid_linewidth=1,
        palette=None,
        marker="o",
        label=None,
        label_loc=None,
        label_props=None,
        legend=True,
        size_legend_kws=None,
        color_legend_kws=None,
        **kwargs,
    ):
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
                    for i, (plabel, c) in enumerate(palette.items()):
                        encoder[plabel] = i
                        render_colors.append(c)
                    self.cmap = ListedColormap(render_colors)
                    self.color2d = encode_numeric(color, encoder)
                    if self.norm is None:
                        vs = encoder.values()
                        self.norm = Normalize(vmin=min(vs), vmax=max(vs))
                else:
                    self._process_cmap(color, vmin, vmax, cmap, norm, center)
                    self.color2d = color
                self._has_colormesh = True
        self.alpha = alpha
        self.frameon = frameon
        self.edgecolor = edgecolor
        self.linewidth = linewidth
        self.set_label(label, label_loc, label_props)
        self.grid = grid
        self.grid_color = grid_color
        self.grid_linewidth = grid_linewidth
        self.kwargs = kwargs

        self._collections = None
        self.set_data(self.size_matrix, self.color2d)

    def update_main_canvas_size(self):
        return get_canvas_size_by_data(self.orig_size.shape)

    def get_legends(self):
        if not self.legend:
            return None
        if self.color is not None:
            size_color = self.color
        else:
            size_color = "black"
        handler_kw = dict(edgecolor=self.edgecolor, linewidth=self.linewidth)
        options = dict(
            colors=size_color,
            handle=self.marker,
            show_at=(0.1, 0.25, 0.5, 0.75, 1.0),
            spacing="uniform",
            handler_kw=handler_kw,
        )
        options.update(self.size_legend_kws)
        size_legend = SizeLegend(self.size_matrix, array=self.orig_size, **options)

        if self._has_colormesh & (self.color != "none"):
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
                color_legend = CatLegend(labels=labels, colors=colors, **options)
            else:
                ScalarMappable(norm=self.norm, cmap=self.cmap)
                color_legend = ColorArt(self._collections, **self.color_legend_kws)
            return [size_legend, color_legend]
        else:
            return size_legend

    def render_ax(self, spec):
        ax = spec.ax
        size, color = spec.data
        if self.is_flank:
            size = size.T
            color = color.T
        Y, X = size.shape
        xticks = np.arange(X) + 0.5
        yticks = np.arange(Y) + 0.5
        xv, yv = np.meshgrid(xticks, yticks)

        if self.grid:
            for x in xticks:
                ax.axvline(
                    x, color=self.grid_color, linewidth=self.grid_linewidth, zorder=0
                )
            for y in yticks:
                ax.axhline(
                    y, color=self.grid_color, linewidth=self.grid_linewidth, zorder=0
                )

        options = dict(
            s=size,
            edgecolor=self.edgecolor,
            linewidths=self.linewidth,
            marker=self.marker,
        )
        if self.color is not None:
            options["c"] = color
        else:
            options.update(dict(c=color, norm=self.norm, cmap=self.cmap))
        self._collections = ax.scatter(xv, yv, **options, **self.kwargs)

        close_ticks(ax)
        if not self.frameon:
            ax.set_axis_off()
        ax.set_xlim(0, xticks[-1] + 0.5)
        ax.set_ylim(0, yticks[-1] + 0.5)
        if not ax.yaxis_inverted():
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
    frameon : bool
        Whether to draw the border of the plot
    label : str
        The label of the plot, only show when added to the side plot
    label_loc : {'top', 'bottom', 'left', 'right'}
        The position of the label
    label_props : dict
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

    def __init__(
        self,
        data,
        color="black",
        marker="*",
        size=35,
        frameon=False,
        label=None,
        label_loc=None,
        label_props=None,
        **kwargs,
    ):
        self.set_data(np.asarray(data))
        self.color = color
        self.marker = marker
        self.marker_size = size
        self.frameon = frameon
        self.set_label(label, label_loc, label_props)
        self.kwargs = kwargs

    def get_legends(self):
        return CatLegend(
            colors=[self.color], labels=[self.label], handle=self.marker, draw=False
        )

    def render_ax(self, spec):
        ax = spec.ax
        data = spec.data

        Y, X = data.shape
        xticks = np.arange(X) + 0.5
        yticks = np.arange(Y) + 0.5
        yv, xv = np.where(data)

        ax.scatter(
            xv + 0.5,
            yv + 0.5,
            s=self.marker_size,
            c=self.color,
            marker=self.marker,
            **self.kwargs,
        )

        close_ticks(ax)
        ax.set_xlim(0, xticks[-1] + 0.5)
        ax.set_ylim(0, yticks[-1] + 0.5)
        if not ax.yaxis_inverted():
            ax.invert_yaxis()
        if not self.frameon:
            ax.set_axis_off()


class TextMesh(MeshBase):
    """The mesh that draw text on each cell

    Parameters
    ----------
    texts : np.ndarray
        The text to draw
    color : color
        The color of the text
    frameon : bool
        Whether to draw the border of the plot
    label : str
        The label of the plot, only show when added to the side plot
    label_loc : {'top', 'bottom', 'left', 'right'}
        The position of the label
    label_props : dict
        Props for label :class:`matplotlib.text.Text`
    kwargs : dict
        Pass to :meth:`matplotlib.axes.Axes.text`

    """

    render_main = True

    def __init__(
        self,
        texts,
        color="black",
        frameon=False,
        label=None,
        label_loc=None,
        label_props=None,
        **kwargs,
    ):
        self.set_data(self.data_validator(texts))
        self.color = color
        self.frameon = frameon
        self.set_label(label, label_loc, label_props)
        self.kwargs = kwargs

    def render_ax(self, spec):
        ax = spec.ax
        data = spec.data

        Y, X = data.shape
        xticks = np.arange(X) + 0.5
        yticks = np.arange(Y) + 0.5

        text_options = {
            "ha": "center",
            "va": "center",
            "color": self.color,
            **self.kwargs,
        }
        for x in range(X):
            for y in range(Y):
                ax.text(x + 0.5, y + 0.5, data[y, x], **text_options)

        close_ticks(ax)
        ax.set_xlim(0, xticks[-1] + 0.5)
        ax.set_ylim(0, yticks[-1] + 0.5)
        if not ax.yaxis_inverted():
            ax.invert_yaxis()
        if not self.frameon:
            ax.set_axis_off()
