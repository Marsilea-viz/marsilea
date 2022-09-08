import warnings
from enum import Enum

import numpy as np
from matplotlib import cm
from matplotlib.axes import Axes
import matplotlib.colors as mcolors
from natsort import natsorted


class Chart(Enum):
    Bar = "bar"
    Box = "box"
    Colors = "colors"
    Scatter = "scatter"
    Dendrogram = "dendrogram"
    Violin = "violin"
    Line = "line"


class _PlotBase:

    def render(self, axes):
        raise NotImplemented


class ColorMesh:

    def __init__(self,
                 axes,
                 render_data,
                 cmap=None,
                 vmin=None,
                 vmax=None,
                 alpha=None,
                 mode="mesh"  # mesh or collection
                 ):
        self.axes = axes
        self.render_data = render_data

        self.cmap = cmap
        self.vmin = vmin
        self.vmax = vmax
        self._render_mesh()

    def _render_mesh(self):
        count = 1
        if isinstance(self.axes, Axes):
            # print(self.render_data)
            self.axes.invert_yaxis()
            self.axes.set_axis_off()
            self.axes.pcolormesh(self.render_data, cmap=self.cmap)
        else:
            for hax, data in zip(self.axes, self.render_data):
                # print(data)
                hax.invert_yaxis()
                hax.set_axis_off()
                hax.pcolormesh(data, cmap=self.cmap,
                               vmin=self.vmin, vmax=self.vmax)
                # hax.text(0.5, 0.5, f"AXES {count}")
                # count += 1


class CatMesh:

    def __init__(self,
                 axes,
                 data,
                 labels,
                 color_mapping=None,
                 ):
        pass



    # @staticmethod
    # def _cat2int(data, color_mapper=None):
    #     # color_lists =
    #     if color_mapper is not None:
    #
    #     cats = []
    #     if isinstance(data, list):
    #         for arr in data:
    #             cats += np.unique(arr).tolist()
    #         cats = np.unique(cats)
    #     else:
    #         cats = np.unique(data)
    #     vmax = len(cats)
    #
    #     if cmap is None:
    #         cmap = cm.get_cmap('tab20')
    #     if cmap.N > vmax:
    #         warnings.warn(f"Current colormap has only {cmap.N} colors "
    #                       f"which is less that your input "
    #                       f"with {vmax} elements")
    #     mapper = {c: i for i, c in enumerate(cats)}

    @staticmethod
    def _color_mapper(arr, cmap):
        cats = natsorted(np.unique(arr))
        vmax = len(cats)
        if cmap is None:
            cmap = cm.get_cmap('tab20')
        if cmap.N > vmax:
            warnings.warn(f"Current colormap has only {cmap.N} colors "
                          f"which is less that your input "
                          f"with {vmax} elements")
        mapper = {c: i for i, c in enumerate(cats)}
