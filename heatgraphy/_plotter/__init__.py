from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict

from .mesh import ColorMesh
from .stripe import ColorStrip
from .bar import Bar
from .label import Label
from .anno_label import AnnoLabel
from .chunk import Chunk


class Chart(Enum):
    Bar = "bar"
    Box = "box"
    Colors = "colors"
    Scatter = "scatter"
    Dendrogram = "dendrogram"
    Violin = "violin"
    Line = "line"
    Label = "label"
    AnnotatedLabel = "annotated_label"
    Chunk = "chunk"


@dataclass
class RenderPlan:
    name: str
    orient: str
    data: Any
    size: float
    chart: Chart
    options: Dict
    no_split: bool = False

    render_data = None

    _Chart_Renderer = {
        Chart.Colors: ColorStrip,
        Chart.Bar: Bar,
        Chart.Label: Label,
        Chart.AnnotatedLabel: AnnoLabel,
        Chart.Chunk: Chunk,
    }

    def render(self, axes):
        plotter = self._Chart_Renderer[self.chart]
        p = plotter(axes, self.get_render_data(), **self.options)
        p.set_orient(self.orient)
        p.render()

    def set_render_data(self, data):
        self.render_data = data

    def get_render_data(self):
        if self.render_data is None:
            return self.data
        else:
            return self.render_data

