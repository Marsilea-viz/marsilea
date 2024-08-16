import pandas as pd
from legendkit import cat_legend

from marsilea.plotter.base import StatsBase, RenderSpec


class Range(StatsBase):
    """Range plot

    The range plot shows the range between two categories.
    The input data should be a DataFrame with two columns.

    Parameters
    ----------
    data : array-like or DataFrame
        The input data.
    items : array-like, default: None
        The names of the items.
    marker : str, default: 'o'
        The marker style.
    markersize : float, default: 50
        The size of the marker.
    color1 : str, default: '#F75940'
        The color of the first range.
    color2 : str, default: '#3DC7BE'
        The color of the second range.
    edgecolor1 : str, default: 'black'
        The edge color of the first range.
    edgecolor2 : str, default: 'black'
        The edge color of the second range.
    edgewidth : float, default: 1
        The width of the edge.
    linecolor : str, default: 'black'
        The color of the line.
    linewidth : float, default: 1
        The width of the line.
    label : str, default: None
        The label of the plot.

    Examples
    --------

    .. plot::
        :context: close-figs

        >>> import marsilea as ma
        >>> import numpy as np
        >>> data = np.random.rand(10, 2)
        >>> range_data = np.random.randint(1, 100, (10, 2))
        >>> h = ma.Heatmap(data)
        >>> h.add_left(ma.plotter.Range(range_data, items=["A", "B"]))
        >>> h.render()


    """

    def __init__(self,
                 data,
                 items=None,
                 marker='o',
                 markersize=50,
                 color1='#F75940',
                 color2='#3DC7BE',
                 edgecolor1='black',
                 edgecolor2='black',
                 edgewidth=1,
                 linecolor='black',
                 linewidth=1,
                 label=None,
                 ):
        if isinstance(data, pd.DataFrame):
            if items is None:
                items = data.columns
            data = data.to_numpy()
        else:
            data = data
            if items is None:
                items = [f"Item {i}" for i in range(data.shape[1])]
        data = self.data_validator(data, target="2d")
        self.set_data(data.T)
        self.set_label(label)
        self.items = items
        self.marker = marker
        self.markersize = markersize
        self.color1 = color1
        self.color2 = color2
        self.edgecolor1 = edgecolor1
        self.edgecolor2 = edgecolor2
        self.edgewidth = edgewidth
        self.linecolor = linecolor
        self.linewidth = linewidth

    def render_ax(self, spec: RenderSpec):
        ax = spec.ax
        data = spec.data.T

        for ix, (r1, r2) in enumerate(data):
            ix += .5
            x, y = [ix, ix], [r1, r2]
            if self.is_flank:
                x, y = y, x
            ax.scatter([x[0]], [y[0]], s=self.markersize, marker=self.marker, color=self.color1, edgecolor=self.edgecolor1, zorder=1)
            ax.scatter([x[1]], [y[1]], s=self.markersize, marker=self.marker, color=self.color2, edgecolor=self.edgecolor2, zorder=1)
            ax.plot(x, y, color=self.linecolor, linewidth=self.linewidth, zorder=0)

        if self.is_flank:
            ax.set_ylim(0, len(data))
        else:
            ax.set_xlim(0, len(data))
        if self.side == "left":
            ax.invert_xaxis()

    def get_legends(self):
        return [cat_legend(colors=[self.color1, self.color2], labels=self.items, title=self.label)]
