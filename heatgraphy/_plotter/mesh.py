from matplotlib.axes import Axes

from ._base import _PlotBase


class ColorMesh(_PlotBase):

    def __init__(self,
                 axes,
                 data,
                 cmap=None,
                 vmin=None,
                 vmax=None,
                 alpha=None,
                 mode="mesh"  # mesh or collection
                 ):
        self.axes = axes
        self.data = data

        self.cmap = cmap
        self.vmin = vmin
        self.vmax = vmax
        self.render()

    def render(self):
        count = 1
        if isinstance(self.axes, Axes):
            self._draw_ax(self.axes, self.data)
        else:
            for hax, data in zip(self.axes, self.data):
                self._draw_ax(hax, data)

    def _draw_ax(self, ax, data):
        ax.invert_yaxis()
        ax.set_axis_off()
        ax.pcolormesh(data, cmap=self.cmap,
                      vmin=self.vmin, vmax=self.vmax)

    def get_legend(self):
        pass


class CatMesh(_PlotBase):
    """Draw a different element based on categorical data"""
    pass
