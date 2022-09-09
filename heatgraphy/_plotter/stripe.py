import warnings
from itertools import cycle

import numpy as np
from matplotlib import cm
from matplotlib.colors import ListedColormap
from matplotlib.offsetbox import AnchoredText

from ._base import _PlotBase

ECHARTS16 = [
    "#5470c6", "#91cc75", "#fac858", "#ee6666",
    "#9a60b4", "#73c0de", "#3ba272", "#fc8452",
    "#27727b", "#ea7ccc", "#d7504b", "#e87c25",
    "#b5c334", "#fe8463", "#26c0c0", "#f4e001"
]


class ColorStrip(_PlotBase):

    def __init__(self,
                 axes,
                 data,  # must be 2d data or a list of 2d
                 label=None,
                 label_loc=None,
                 color_mapping=None,
                 cmap=None
                 ):
        self.axes = axes
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
            self.render_cmap = ListedColormap([c for c, _ in zip(cycle(colors), range(self.vmax))])

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

    def render(self, orient="top"):
        if self.label_loc is None:
            self.label_loc = self.default_label_loc[orient]
        if isinstance(self.data, list):
            if self.label_loc in ["top", "left"]:
                self._add_label(self.axes[0])
            else:
                self._add_label(self.axes[-1])
            for hax, arr in zip(self.axes, self.data):
                if orient in ["left", "right"]:
                    hax.invert_yaxis()
                hax.set_axis_off()
                render_data = self._remap(arr, self.mapper)
                hax.pcolormesh(render_data, cmap=self.render_cmap,
                               vmin=0, vmax=self.vmax)
        else:
            render_data = self._remap(self.data, self.mapper)
            if orient in ["left", "right"]:
                self.axes.invert_yaxis()
            self.axes.pcolormesh(render_data, cmap=self.render_cmap,
                                 vmin=0, vmax=self.vmax)
            self.axes.set_axis_off()
            if self.label is not None:
                self._add_label(self.axes)
