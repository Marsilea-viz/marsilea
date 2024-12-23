import numpy as np

from marsilea.plotter.base import StatsBase


class Area(StatsBase):
    """Area plot

    Parameters
    ----------
    data : array-like
        The data to be plotted.
    color : color-like
        The color of the area
    add_outline : bool
        Whether to add outline to the area
    alpha : float
        The transparency of the area
    linecolor : color-like
        The color of the outline
    linewidth : float
        The width of the outline
    group_kws : dict
        The configurations that apply to each group
    **kwargs :
        Additional configurations for the area plot, \
        see :func:`matplotlib.pyplot.fill_between`

    Examples
    --------
    .. plot::
        :context: close-figs

        import numpy as np
        import matplotlib.pyplot as plt

        from marsilea.plotter import Area

        _, ax = plt.subplots()
        data = np.random.randint(0, 10, 10) + 1
        Area(data).render(ax)

    """

    def __init__(
        self,
        data,
        color=None,
        add_outline=True,
        alpha=0.4,
        linecolor=None,
        linewidth=1,
        group_kws=None,
        label=None,
        label_loc=None,
        label_props=None,
        **kwargs,
    ):
        if color is None:
            color = "skyblue"
        if linecolor is None:
            linecolor = "Slateblue"

        self.color = color
        self.add_outline = add_outline
        self.alpha = alpha
        self.linecolor = linecolor
        self.linewidth = linewidth
        self.kws = kwargs

        self.set_data(data)
        self.set_label(label, label_loc, label_props)
        if group_kws is not None:
            self.set_group_params(group_kws)

    def render_ax(self, spec):
        ax = spec.ax
        data = spec.data
        gp = spec.group_params
        if gp is None:
            gp = {}

        fill_options = {"color": self.color, "alpha": self.alpha, **self.kws, **gp}
        line_options = {"color": self.linecolor, "linewidth": self.linewidth, **gp}

        x = np.arange(len(data))
        if self.get_orient() == "h":
            ax.fill_betweenx(x, data, **fill_options)
            if self.add_outline:
                ax.plot(data, x, **line_options)
            ax.set_ylim(-0.5, len(data) - 0.5)
            if self.side == "left":
                if not ax.xaxis_inverted():
                    ax.invert_xaxis()
        else:
            ax.fill_between(x, data, **fill_options)
            if self.add_outline:
                ax.plot(x, data, **line_options)
            ax.set_xlim(-0.5, len(data) - 0.5)
        return ax


# TODO: Implement StackArea
class StackArea(StatsBase):
    pass
