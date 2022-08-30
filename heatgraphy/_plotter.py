from enum import Enum

from matplotlib.axes import Axes


class Chart(Enum):
    Bar = "bar"
    Box = "box"
    Colors = "colors"
    Scatter = "scatter"
    Dendrogram = "dendrogram"
    Violin = "violin"
    Line = "line"


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
