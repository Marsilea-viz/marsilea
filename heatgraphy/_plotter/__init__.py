from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict

from .mesh import ColorMesh
from .stripe import ColorStrip
from .bar import Bar


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

    render_data = None

    _Chart_Renderer = {
        Chart.Colors: ColorStrip,
        Chart.Bar: Bar,
    }

    def render(self, axes, orient):
        plotter = self._Chart_Renderer[self.chart]
        p = plotter(axes, self.get_render_data(), **self.options)
        p.render(orient)

    def set_render_data(self, data):
        self.render_data = data

    def get_render_data(self):
        if self.render_data is None:
            return self.data
        else:
            return self.render_data

