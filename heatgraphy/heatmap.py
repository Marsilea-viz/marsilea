from __future__ import annotations

import logging

import matplotlib.pyplot as plt
import numpy as np

from .base import MatrixBase, Base, get_plot_name
from .plotter import ColorMesh, SizedMesh, Colors

log = logging.getLogger("heatgraphy")


class WhiteBoard(Base):
    """Create an empty canvas

    """
    def __init__(self, width=None, height=None, aspect=1):
        super().__init__(w=width, h=height, main_aspect=aspect)

    def render(self, figure=None, aspect=1, scale=1):
        self._freeze_legend()
        if figure is None:
            self.figure = plt.figure()
        else:
            self.figure = figure

        if not self.grid.is_freeze:
            self.grid.freeze(figure=self.figure, aspect=aspect, scale=scale)

        self._render_plan()
        self._render_legend()


class ClusterCanvas(MatrixBase):
    """Create an empty canvas that can be split and reorder by dendrogram

    """
    def __init__(self, cluster_data, width=None, height=None, aspect=1):
        super().__init__(cluster_data, w=width, h=height, main_aspect=aspect)


class Heatmap(MatrixBase):
    """Heatmap

    See :class:`ColorMesh <heatgraphy.plotter.ColorMesh>` for details

    Other Parameters
    ----------------
    square : bool
        If True, the cell will render in equal
    cluster_data : matrix data
        You can override the data used to perform cluster
        By default will use the plotting data.
    name : str
        The name of this Heatmap
    width, height : float
        The size in inches to define the size of main canvas

    """

    def __init__(self, data: np.ndarray, vmin=None, vmax=None,
                 cmap=None, norm=None, center=None,
                 mask=None, alpha=None, linewidth=0, linecolor="white",
                 annot=None, fmt=None, annot_kws=None, label=None,
                 cbar_kws=None, square=False, name=None,
                 width=None, height=None, cluster_data=None
                 ):
        self.square = square

        main_aspect = 1
        if (width is not None) & (height is not None):
            main_aspect = height / width
        if square:
            Y, X = data.shape
            main_aspect = Y / X
        if cluster_data is None:
            cluster_data = data
        super().__init__(cluster_data, w=width, h=height,
                         main_aspect=main_aspect)
        mesh = ColorMesh(data, vmin=vmin, vmax=vmax, cmap=cmap,
                         norm=norm, center=center,
                         mask=mask, alpha=alpha, linewidth=linewidth,
                         linecolor=linecolor, annot=annot, fmt=fmt,
                         annot_kws=annot_kws, label=label, cbar_kws=cbar_kws)
        name = get_plot_name(name, "main", mesh.__class__.__name__)
        mesh.set(name=name)
        self.add_layer(mesh)


class CatHeatmap(MatrixBase):
    """Categorical Heatmap

    See :class:`Colors <heatgraphy.plotter.Colors>` for details

    Other Parameters
    ----------------
    name : str
        The name of this Heatmap
    cluster_data : matrix data
        You can override the data used to perform cluster
        By default will use the plotting data.
    width, height : float
        The size in inches to define the size of main canvas

    """

    def __init__(self, data, palette=None, cmap=None, mask=None,
                 name=None, width=None, height=None, cluster_data=None):
        mesh = Colors(data, palette=palette, cmap=cmap, mask=mask)
        if cluster_data is None:
            cluster_data = mesh.cluster_data
        super().__init__(cluster_data, w=width, h=height)
        name = get_plot_name(name, "main", mesh.__class__.__name__)
        mesh.set(name=name)
        self.add_layer(mesh)


class SizedHeatmap(MatrixBase):
    """Sized Heatmap

    See :class:`SizedMesh <heatgraphy.plotter.SizedMesh>` for details

    Other Parameters
    ----------------
    name : str
        The name of this Heatmap
    cluster_data : matrix data
        You can override the data used to perform cluster
        By default will use the size data.
    width, height : float
        The size in inches to define the size of main canvas

    """

    def __init__(self, size, color=None, cluster_data=None,
                 **kwargs):
        if cluster_data is None:
            cluster_data = size
        y, x = cluster_data.shape
        super().__init__(cluster_data, main_aspect=y / x)

        mesh = SizedMesh(size=size, color=color, **kwargs)
        self.add_layer(mesh)
