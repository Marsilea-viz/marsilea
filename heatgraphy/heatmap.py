from __future__ import annotations

import logging

import numpy as np

from .base import ClusterBoard
from .plotter import ColorMesh, SizedMesh, Colors
from .utils import get_plot_name

log = logging.getLogger("heatgraphy")


class Heatmap(ClusterBoard):
    """Heatmap

    See :class:`ColorMesh <heatgraphy.plotter.ColorMesh>` for details

    Other Parameters
    ----------------
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
                 cbar_kws=None, name=None,
                 width=None, height=None, cluster_data=None
                 ):
        if cluster_data is None:
            cluster_data = data
        super().__init__(cluster_data, width=width, height=height,
                         name=name)
        mesh = ColorMesh(data, vmin=vmin, vmax=vmax, cmap=cmap,
                         norm=norm, center=center,
                         mask=mask, alpha=alpha, linewidth=linewidth,
                         linecolor=linecolor, annot=annot, fmt=fmt,
                         annot_kws=annot_kws, label=label, cbar_kws=cbar_kws)
        name = get_plot_name(name, "main", mesh.__class__.__name__)
        mesh.set(name=name)
        self.add_layer(mesh)


class CatHeatmap(ClusterBoard):
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
        super().__init__(cluster_data, width=width, height=height, name=name)
        name = get_plot_name(name, "main", mesh.__class__.__name__)
        mesh.set(name=name)
        self.add_layer(mesh)


class SizedHeatmap(ClusterBoard):
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
                 name=None, width=None, height=None,
                 **kwargs):
        if cluster_data is None:
            cluster_data = size
        super().__init__(cluster_data, width=width, height=height, name=name)

        mesh = SizedMesh(size=size, color=color, **kwargs)
        self.add_layer(mesh)
