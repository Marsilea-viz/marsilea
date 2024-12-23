"""Declarative creation of composable visualization"""

__version__ = "0.4.8"

import marsilea.plotter as plotter
from ._deform import Deformation
from .base import (
    WhiteBoard,
    ClusterBoard,
    ZeroWidth,
    ZeroHeight,
    ZeroWidthCluster,
    ZeroHeightCluster,
    CompositeBoard,
    StackBoard,
)
from .dataset import load_data
from .dendrogram import Dendrogram, GroupDendrogram
from .heatmap import Heatmap, SizedHeatmap, CatHeatmap
from .layers import Piece, Layers
from .layout import CrossLayout, CompositeCrossLayout, StackCrossLayout
from .upset import UpsetData, Upset
