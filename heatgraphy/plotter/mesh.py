import warnings
from itertools import cycle

import numpy as np
from matplotlib import cm, pyplot as plt
from matplotlib.artist import Artist
from matplotlib.colors import ListedColormap, TwoSlopeNorm, Normalize
from matplotlib.offsetbox import AnchoredText

from .base import RenderPlan
from ..layout import close_ticks
from ..utils import relative_luminance

ECHARTS16 = [
    "#5470c6", "#91cc75", "#fac858", "#ee6666",
    "#9a60b4", "#73c0de", "#3ba272", "#fc8452",
    "#27727b", "#ea7ccc", "#d7504b", "#e87c25",
    "#b5c334", "#fe8463", "#26c0c0", "#f4e001"
]


class _MeshBase:

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
            norm = TwoSlopeNorm(center, vmin=vmin, vmax=vmax)
            self.norm = norm

    @staticmethod
    def _annotate_text(ax, mesh, texts, fmt, **annot_kws):
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
                annotation = ("{:" + fmt + "}").format(val)
                text_kwargs = dict(color=text_color, ha="center", va="center")
                text_kwargs.update(annot_kws)
                ax.text_obj(x, y, annotation, **text_kwargs)


class ColorMesh(RenderPlan, _MeshBase):

    def __init__(self, data, cmap=None, norm=None, vmin=None, vmax=None,
                 center=None, robust=None, alpha=None,
                 linewidth=None, edgecolor=None):
        self.data = data
        self.alpha = alpha
        self.linewidth = linewidth
        self.edgecolor = edgecolor
        self._process_cmap(data, vmin, vmax, cmap, norm, center, robust)

    def render_ax(self, ax, data):
        print(data.shape)

        ax.pcolormesh(data, cmap=self.cmap,
                      vmin=self.vmin, vmax=self.vmax,
                      linewidth=self.linewidth,
                      edgecolor=self.edgecolor
                      )
        ax.invert_yaxis()
        ax.set_axis_off()

    def get_legend(self):
        pass


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


class Colors(RenderPlan):
    def __init__(self, data, label=None, label_loc=None,
                 color_mapping=None, cmap=None):
        self.data = data
        self.label = label
        self.label_loc = label_loc
        # get unique color
        if color_mapping is not None:
            self.mapper = {}
            colors = []
            for i, (label, color) in enumerate(color_mapping.items()):
                self.mapper[label] = i
                colors.append(color)
            self.render_cmap = ListedColormap(colors)
            self.vmax = len(colors)
        else:
            if cmap is not None:
                if isinstance(cmap, str):
                    colors = cm.get_cmap(cmap).colors
                else:
                    colors = cmap.colors
            else:
                colors = ECHARTS16

            # data to int
            cats = []
            if isinstance(data, list):
                for arr in data:
                    cats += np.unique(arr).tolist()
                cats = np.unique(cats)
            else:
                cats = np.unique(data)
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

    # transform input data to numeric
    @staticmethod
    def _remap(orig_arr, remapper):
        orig_shape = orig_arr.shape
        re_arr = [remapper[e] for e in orig_arr.flatten()]
        re_arr = np.array(re_arr).reshape(orig_shape)
        return re_arr

    def _add_label(self, ax):
        pos = self.label_loc
        prop = None
        if pos == "left":
            loc = "center right"
            bbox_to_anchor = (0, 0.5)
        elif pos == "right":
            loc = "center left"
            bbox_to_anchor = (1, 0.5)
        elif pos == "top":
            prop = dict(rotation=90)
            loc = "lower center"
            bbox_to_anchor = (0.5, 1)
        else:
            prop = dict(rotation=90)
            loc = "upper center"
            bbox_to_anchor = (0.5, 0)
        title = AnchoredText(self.label,
                             prop=prop,
                             pad=0.3,
                             borderpad=0,
                             loc=loc,
                             bbox_transform=ax.transAxes,
                             bbox_to_anchor=bbox_to_anchor,
                             frameon=False)
        ax.add_artist(title)

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
                if self.h:
                    hax.invert_yaxis()
                hax.set_axis_off()
                render_data = self._remap(arr, self.mapper)
                hax.pcolormesh(render_data, cmap=self.render_cmap,
                               vmin=0, vmax=self.vmax)
        else:
            render_data = self._remap(render_data, self.mapper)
            if self.h:
                axes.invert_yaxis()
            axes.pcolormesh(render_data, cmap=self.render_cmap,
                            vmin=0, vmax=self.vmax)
            axes.set_axis_off()
            if self.label is not None:
                self._add_label(axes)


class Pieces:

    def draw(self, x, y, w, h) -> Artist:
        raise NotImplemented

    def legend(self, x, y, w, h) -> Artist:
        return self.draw(x, y, w, h)

    def legend_artist(self, legend, orig_handle, fontsize, handlebox):
        x, y = handlebox.xdescent, handlebox.ydescent
        w, h = handlebox.width, handlebox.height
        p = self.legend(-x, -y, w, h)
        handlebox.add_artist(p)
        return p


def preview(element: Pieces, figsize=(1, 1)):
    figure = plt.figure(figsize=figsize)
    ax = figure.add_axes([0, 0, 1, 1])
    close_ticks(ax)
    arts = element.draw(0, 0, 1, 1)
    ax.add_artist(arts)


class CatMesh:
    """Mesh with custom graphic elements"""
    pass
