import numpy as np

from marsilea.plotter.base import StatsBase


class Area(StatsBase):

    def __init__(self, data, group_kws=None, **kwargs):

        self.set_data(data)
        if group_kws is not None:
            self.set_group_params(group_kws)

    def render_ax(self, spec):
        ax = spec.ax
        data = spec.data
        gp = spec.group_params
        if gp is None:
            gp = {}

        x = np.arange(len(data))
        if self.get_orient() == "h":
            ax.fill_betweenx(x, data, color="skyblue", alpha=0.4)
            ax.plot(data, x, color="Slateblue", alpha=0.6, linewidth=2)
            ax.set_ylim(-.5, len(data)-.5)
            if self.side == "left":
                ax.invert_xaxis()
        else:
            ax.fill_between(x, data, color="skyblue", alpha=0.4)
            ax.plot(x, data, color="Slateblue", alpha=0.6, linewidth=2)
            ax.set_xlim(-.5, len(data)-.5)
        return ax
