from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict

from .mesh import ColorMesh
from .stripe import ColorStrip


class Chart(Enum):
    Bar = "bar"
    Box = "box"
    Colors = "colors"
    Scatter = "scatter"
    Dendrogram = "dendrogram"
    Violin = "violin"
    Line = "line"


@dataclass
class RenderPlan:
    name: str
    side: str
    data: Any
    size: float
    chart: Chart
    options: Dict

    _Chart_Renderer = {
        Chart.Colors: ColorStrip
    }

    def render(self, axes, orient):
        plotter = self._Chart_Renderer[self.chart]
        p = plotter(axes, self.data, **self.options)
        p.render(orient)

