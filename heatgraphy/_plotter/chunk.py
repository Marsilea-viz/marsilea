from matplotlib.patches import Rectangle
from seaborn import despine

from ._base import _PlotBase

rotation_mapper = {
    "right": -90,
    "left": 90,
    "top": 0,
    "bottom": 0,
}


class Chunk(_PlotBase):

    def __init__(self,
                 axes,
                 data,
                 bordercolor=None,
                 borderwidth=None,
                 borderstyle=None,
                 **options,
                 ):
        self.axes = axes
        self.data = data
        self.bordercolor = bordercolor
        self.borderwidth = borderwidth
        self.borderstyle = borderstyle
        self.options = options

    def render(self):

        if self.is_whole():
            label, color = self.data[0]

            self._draw_ax(self.axes, label, color)
        else:
            for d, ax in zip(self.data, self.axes):
                label, color = d
                self._draw_ax(ax, label, color)

    def _draw_ax(self, ax, label, color):
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_axis_off()

        if color is not None:
            rect = Rectangle((0, 0), 1, 1,
                             facecolor=color,
                             edgecolor=self.bordercolor,
                             linewidth=self.borderwidth,
                             linestyle=self.borderstyle,
                             )
            ax.add_artist(rect)
        options = {
            **dict(
                va="center",
                ha="center",
                rotation=rotation_mapper[self.orient]
            ),
            **self.options
        }

        ax.text(0.5, 0.5, label, **options)
