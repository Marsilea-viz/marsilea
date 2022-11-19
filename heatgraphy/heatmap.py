from __future__ import annotations

import logging

import matplotlib.pyplot as plt
import numpy as np

from .base import MatrixBase, Base
from .plotter import ColorMesh, SizedMesh, Colors

log = logging.getLogger("heatgraphy")


class WhiteBoard(Base):
    """Create an empty canvas

    """
    def __init__(self, width=None, height=None, aspect=1):
        super().__init__(w=width, h=height, main_aspect=aspect)

    def render(self, figure=None, aspect=1):
        self._freeze_legend()
        if figure is None:
            self.figure = plt.figure()
        else:
            self.figure = figure

        if not self.grid.is_freeze:
            self.grid.freeze(figure=self.figure, aspect=aspect)

        self._render_plan()
        self._render_legend()


class ClusterCanvas(MatrixBase):
    """Create an empty canvas that can be split and reorder by dendrogram

    """
    def __init__(self, cluster_data, width=None, height=None, aspect=1):
        super().__init__(cluster_data, w=width, h=height, main_aspect=aspect)


class Heatmap(MatrixBase):

    def __init__(self, data: np.ndarray, vmin=None, vmax=None,
                 cmap=None, norm=None, center=None,
                 mask=None, alpha=None, linewidth=0, linecolor="white",
                 annot=None, fmt=None, annot_kws=None,
                 square=False, name=None, width=None, height=None,
                 ):
        # if mask is not None:
        #     data = np.ma.masked_where(np.asarray(mask), data).filled(np.nan)
        # self.data = data
        self.square = square

        data_aspect = 1
        if square:
            Y, X = data.shape
            data_aspect = Y / X
        super().__init__(data, w=width, h=height, main_aspect=data_aspect)
        mesh = ColorMesh(data, vmin=vmin, vmax=vmax, cmap=cmap,
                         norm=norm, center=center,
                         mask=mask, alpha=alpha, linewidth=linewidth,
                         linecolor=linecolor, annot=annot, fmt=fmt,
                         annot_kws=annot_kws)
        name = self._get_plot_name(name, "main", mesh.__class__.__name__)
        mesh.set(name=name)
        self.add_layer(mesh)


class CatHeatmap(MatrixBase):

    def __init__(self, data, palette=None, cmap=None, mask=None,
                 name=None, width=None, height=None,):
        mesh = Colors(data, palette=palette, cmap=cmap, mask=mask)
        super().__init__(mesh.cluster_data, w=width, h=height)
        name = self._get_plot_name(name, "main", mesh.__class__.__name__)
        mesh.set(name=name)
        self.add_layer(mesh)


class DotHeatmap(MatrixBase):

    def __init__(self, size, color=None, cluster_data=None,
                 **kwargs):
        cluster_data = size
        y, x = cluster_data.shape
        super().__init__(cluster_data, main_aspect=y / x)

        mesh = SizedMesh(size=size, color=color, **kwargs)
        self.add_layer(mesh)

    def add_matrix(self, data: np.ndarray, vmin=None, vmax=None, cmap=None,
                   norm=None, center=None, mask=None,
                   alpha=None, linewidth=None, linecolor=None,
                   ):
        bg_mesh = ColorMesh(data, cmap=cmap, norm=norm, vmin=vmin, vmax=vmax,
                            center=center, mask=mask,
                            alpha=alpha, linewidth=linewidth,
                            linecolor=linecolor)
        self.add_layer(bg_mesh, zorder=-1)

