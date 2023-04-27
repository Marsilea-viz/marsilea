import numpy as np
from dataclasses import dataclass
from legendkit import cat_legend
from matplotlib.colors import Normalize, is_color_like
from matplotlib.patches import Arc as mArc
from numbers import Number

from .base import StatsBase


@dataclass
class LinkAttrs:
    width: float
    color: str


class Links:
    def __init__(self, links, weights=None, width=None,
                 colors=None, labels=None):
        self._links = {}
        self._links_attr = {}

        self.unweighted = True
        self.width = 1
        self.norm = None
        if weights is not None:
            self.unweighted = False
            self.norm = Normalize()
            self.norm.autoscale(weights)

        if colors is None:
            self.colors = ["C0" for _ in links]
        elif is_color_like(colors):
            self.colors = [colors for _ in links]
        else:
            if len(colors) != len(links):
                msg = f"Length of colors ({len(colors)}) does not " \
                      f"match length of links ({len(links)})"
                raise ValueError(msg)
            self.colors = colors

        self.legend_entries = None
        if labels is not None:
            if len(labels) != len(links):
                msg = f"Length of labels ({len(labels)}) does not " \
                      f"match length of links ({len(links)})"
                raise ValueError(msg)
            self.legend_entries = dict(zip(labels, colors))

        if width is not None:
            if weights is None:
                if isinstance(width, Number):
                    self.width = width
                else:
                    msg = "width must be a number if weights is not specify"
                    raise ValueError(msg)

            else:
                if isinstance(width, tuple):
                    self.width = (np.min(width), np.max(width))
                else:
                    msg = "width must be a tuple of numbers"
                    raise ValueError(msg)
        else:
            if weights is not None:
                self.width = (1, 10)

        if weights is None:
            for (e1, e2), c in zip(links, self.colors):
                self._links.setdefault(e1, []).append(e2)
                self._links_attr[(e1, e2)] = LinkAttrs(self.width, c)
        else:
            w0, w1 = self.width
            for (e1, e2), c, w in zip(links, self.colors, weights):
                self._links.setdefault(e1, []).append(e2)
                width = self.norm(w) * (w1 - w0) + w0
                self._links_attr[(e1, e2)] = LinkAttrs(width, c)

    def get(self, item):
        return self._links.get(item)

    def get_attr(self, link) -> LinkAttrs:
        attr = self._links_attr.get(link)
        if attr is None:
            return self._links_attr.get(link[::-1])
        return attr

    def get_legend_entries(self):
        labels = self.legend_entries.keys()
        colors = self.legend_entries.values()
        return labels, colors


class Arc(StatsBase):
    """Arc diagram.

    Parameters
    ----------
    anchors : array-like
        Anchors of the arcs.
    links : array-like
        Links of the arcs.
    weights : array-like, optional
        Weights of the links. If not specified, all links will have the same
        width.
    width : float or tuple of float, optional
        Width of the links. If `weights` is specified, `width` must be a tuple
        of two floats, where the first float is the minimum width and the
        second float is the maximum width. If `weights` is not specified,
        `width` must be a float.
    colors : str or array-like, optional
        Colors of the links. If not specified, all links will have the same
        color.
    labels : array-like, optional
        Labels of the links. If not specified, no legend will be shown.
    legend_kws : dict, optional
        Keyword arguments passed to `legendkit.cat_legend`.
    label : str, optional
        Label of the plot.
    label_loc : str, optional
        Location of the label. Must be one of the following:
        "left", "right", "top", "bottom", "center".
    props : dict, optional
        Keyword arguments passed to `matplotlib.text.Text`.
    **kwargs
        Keyword arguments passed to `matplotlib.patches.Arc`.

    Examples
    --------
    .. plot::
        :context: close-figs

        >>> import marsilea as ma
        >>> from marsilea.plotter import Arc
        >>> anchors = np.arange(10)
        >>> links = [(0, 7), (1, 5), (3, 10), (0, 9), (5, 8), (2, 6), (4, 8)]
        >>> weights = [1, 2, 3, 5, 2, 1, 2]
        >>> colors = ["C0", "C1", "C2", "C3", "C4", "C5", "C6"]
        >>> labels = ["A", "B", "C", "D", "E", "F", "G"]
        >>> h = ma.Heatmap(np.random.rand(10, 10))
        >>> h.add_top(Arc(anchors, links, weights=weights,
        ...               colors=colors, labels=labels))
        >>> h.render()



    """

    render_main = False

    def __init__(self, anchors, links, weights=None, width=None,
                 colors=None, labels=None, legend_kws=None,
                 label=None, label_loc=None, props=None,
                 **kwargs):
        if len(np.unique(anchors)) != len(anchors):
            raise ValueError("`anchors` must be unique")
        anchors = self.data_validator(anchors, target="1d")
        self.set_data(anchors)
        self.links = Links(links, weights=weights, width=width,
                           colors=colors, labels=labels)
        self.options = kwargs
        self.legend_kws = {} if legend_kws is None else legend_kws

        self.label = label
        self.label_loc = label_loc
        self.props = props

    def render_ax(self, spec):
        ax = spec.ax
        data = spec.data

        chunks = np.linspace(0, 1, len(data) + 1)
        mids = (chunks[1:] + chunks[:-1]) / 2
        anchors_coords = dict(zip(data, mids))

        sizes = []

        for anchor in data:
            # is this anchor has a link?
            links = self.links.get(anchor)
            if links is not None:
                # is this link exist in axes?
                for link in links:
                    link_in_data = anchors_coords.get(link)
                    if link_in_data is not None:

                        arc_start = anchors_coords[anchor]
                        arc_end = link_in_data
                        if arc_end < arc_start:
                            arc_start, arc_end = arc_end, arc_start
                        arc_mid = (arc_start + arc_end) / 2
                        arc_width = arc_end - arc_start

                        link_attr = self.links.get_attr((anchor, link))
                        options = dict(
                            theta1=0,
                            theta2=180,
                            color=link_attr.color,
                            linewidth=link_attr.width,
                            **self.options,
                        )

                        if self.side == "left":
                            xy = (1, arc_mid)
                            angle = 90
                        elif self.side == "right":
                            xy = (0, arc_mid)
                            angle = -90
                        elif self.side == "bottom":
                            xy = (arc_mid, 1)
                            angle = 180
                        else:
                            xy = (arc_mid, 0)
                            angle = 0
                        sizes.append(arc_width)
                        arc = mArc(xy, arc_width, arc_width * 2, angle,
                                   **options)

                        ax.add_patch(arc)

        lim = np.max(sizes) * 1.1
        if self.is_flank:
            ax.set_xlim(0, lim)
            ax.set_ylim(0, 1)
        else:
            ax.set_ylim(0, lim)
            ax.set_xlim(0, 1)
        if self.is_flank:
            ax.invert_yaxis()
        ax.set_axis_off()

    def get_legends(self):
        if self.links.legend_entries is not None:
            labels, colors = self.links.get_legend_entries()
            return cat_legend(labels=labels, colors=colors, **self.legend_kws)
