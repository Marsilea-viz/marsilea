"""Declarative creation of composable visualization"""

__version__ = "0.3.6"

import marsilea.plotter as plotter
from ._deform import Deformation
from .base import (
    WhiteBoard,
    ClusterBoard,
    ZeroWidth,
    ZeroHeight,
    ZeroWidthCluster,
    ZeroHeightCluster,
)
from .dataset import load_data
from .dendrogram import Dendrogram, GroupDendrogram
from .heatmap import Heatmap, SizedHeatmap, CatHeatmap
from .layers import Piece, Layers
from .layout import CrossLayout, CompositeCrossLayout
from .upset import UpsetData, Upset
