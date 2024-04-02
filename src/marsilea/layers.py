import numpy as np
from legendkit import ListLegend
from matplotlib import pyplot as plt
from matplotlib.artist import Artist
from matplotlib.collections import PathCollection
from matplotlib.lines import Line2D
from matplotlib.markers import MarkerStyle
from matplotlib.patches import Rectangle, Polygon
from matplotlib.transforms import IdentityTransform
from typing import Mapping, Iterable

from .base import ClusterBoard
from .layout import close_ticks
from .plotter import RenderPlan


class LayersMesh(RenderPlan):
    """The mesh that draw customized elements in multi-layers

    LayersMesh is a powerful solution for drawing and visualizing customized
    elements in multi-layered formats.
    It offers two flexible ways to specify layers:

    #. A single layer of data containing different elements.
    #. Multiple layers of data, where each layer represents a customized element, \
    overlaying elements on top of one another.

    When supplying multiple layers,
    the drawing order follows the order of the input array.
    Override this order by controlling the `zorder` attribute in your :class:`Pieces`.

    Parameters
    ----------

    data : np.ndarray, optional
        Use this parameter for a single layer
    layers : list of data
        For multiple layers, use this parameter.
        Each layer must be a boolean matrix indicating
        whether the element is rendered at a specific cell.
    pieces : dict or array
        For a single layer, use a dict to define how to render each element.
        For multiple layers, use an array to define the rendering of each layer.
    label : str
        The mesh label, displayed only when added to the side plot.
    label_loc : str
        The label location.
    props : dict
        See :class:`matplotlib.text.Text`


    Examples
    --------

    Drawing a single layer:

    .. plot::
        :context: close-figs

        >>> from marsilea.layers import LayersMesh, Rect, FrameRect
        >>> data = np.random.choice([1, 2, 3], (10, 10))
        >>> pieces = {1: Rect(color="r", label="1"),
        ...           2: FrameRect(color="g", label="2"),
        ...           3: Rect(color="b", label="3")}
        >>> _, ax = plt.subplots()
        >>> LayersMesh(data=data, pieces=pieces).render(ax)

    Drawing multiple layers:

    .. plot::
        :context: close-figs

        >>> d1 = np.random.choice([1, 2, 3], (10, 10))
        >>> d2 = np.random.choice([1, 2, 3], (10, 10))
        >>> d3 = np.random.choice([1, 2, 3], (10, 10))
        >>> pieces = [Rect(color="r", label="1"),
        ...           FrameRect(color="g", label="2"),
        ...           Rect(color="b", label="3")]
        >>> _, ax = plt.subplots()
        >>> LayersMesh(layers=[d1, d2, d3], pieces=pieces).render(ax)


    """

    render_main = True

    def __init__(
        self,
        data=None,
        layers=None,
        pieces=None,
        shrink=(1.0, 1.0),
        label=None,
        label_loc=None,
        props=None,
        legend_kws=None,
    ):
        # render one layer
        # with different elements
        if data is not None:
            if not isinstance(pieces, Mapping):
                msg = f"Expect pieces to be dict " f"but found {type(pieces)} instead."
                raise TypeError(msg)
            self.pieces_mapper = pieces
            self.mode = "cell"
            self.set_data(data)
            self._one_layer = True
        # render multiple layers
        # each layer is an elements
        else:
            if not isinstance(pieces, Iterable):
                msg = f"Expect pieces to be list " f"but found {type(pieces)} instead."
                raise TypeError(msg)
            self.pieces, data = self._sort_by_zorder(pieces, layers)
            self.mode = "layer"
            self.set_data(*data)
            self._one_layer = len(data) == 1
        self.x_offset = (1 - shrink[0]) / 2
        self.y_offset = (1 - shrink[1]) / 2
        self.width = shrink[0]
        self.height = shrink[1]
        self.label = label
        self.label_loc = label_loc
        self.props = props
        default_legend_kws = dict(frameon=False, handlelength=1, handleheight=1)
        if legend_kws is not None:
            default_legend_kws.update(legend_kws)
        self._legend_kws = default_legend_kws

    @staticmethod
    def _sort_by_zorder(pieces, layers):
        ix_pieces = sorted(enumerate(pieces), key=lambda x: x[1].zorder)
        sorted_pieces = []
        sorted_layers = []
        for ix, piece in ix_pieces:
            sorted_pieces.append(piece)
            sorted_layers.append(layers[ix])
        return sorted_pieces, sorted_layers

    def get_legends(self):
        if self.mode == "cell":
            handles = list(self.pieces_mapper.values())
        else:
            handles = self.pieces
        new_handles = []
        labels = []
        handler_map = {}
        for h in handles:
            if h.legend_entry:
                new_handles.append(h)
                labels.append(h.get_label())
                handler_map[h] = h
        return ListLegend(
            handles=new_handles,
            labels=labels,
            handler_map=handler_map,
            **self._legend_kws,
        )

    def render_ax(self, spec):
        ax = spec.ax
        data = spec.data

        if self.mode == "layer":
            if self.is_flank:
                data = [d.T for d in data]
            if self._one_layer:
                data = [data]
            Y, X = data[0].shape
        else:
            if self.is_flank:
                data = data.T
            Y, X = data.shape
        ax.set_axis_off()
        ax.set_xlim(0, X)
        ax.set_ylim(0, Y)
        if self.mode == "layer":
            for layer, piece in zip(data, self.pieces):
                for iy, row in enumerate(layer):
                    for ix, v in enumerate(row):
                        if v:
                            art = piece.draw(
                                ix + self.x_offset,
                                iy + self.y_offset,
                                self.width,
                                self.height,
                                ax,
                            )
                            ax.add_artist(art)
        else:
            for iy, row in enumerate(data):
                for ix, v in enumerate(row):
                    piece = self.pieces_mapper[v]
                    art = piece.draw(
                        ix + self.x_offset,
                        iy + self.y_offset,
                        self.width,
                        self.height,
                        ax,
                    )
                    ax.add_artist(art)
        ax.invert_yaxis()


class Layers(ClusterBoard):
    def __init__(
        self,
        data=None,
        layers=None,
        pieces=None,
        cluster_data=None,
        shrink=(1.0, 1.0),
        height=None,
        width=None,
        aspect=1.0,
        name=None,
    ):
        mesh = LayersMesh(data=data, layers=layers, pieces=pieces, shrink=shrink)
        if cluster_data is None:
            self._allow_cluster = False
            data_shape = mesh.get_data()[0].shape
            # create numeric data explicitly
            # in case user input string data
            cluster_data = np.random.randn(*data_shape)
        # if (width is not None) & (height is not None):
        #     main_aspect = height / width
        # else:
        #     Y, X = cluster_data.shape
        #     main_aspect = Y * aspect / X
        super().__init__(cluster_data, width=width, height=height, name=name)

        self.add_layer(mesh)


class Piece:
    label = None
    legend_entry = True
    zorder = 0
    color = "C0"

    def get_label(self):
        if self.label is None:
            return self.__class__.__name__
        else:
            return self.label

    def set_label(self, label):
        self.label = label

    @staticmethod
    def draw_center(x, y, w, h):
        cx = x + w / 2.0
        cy = y + h / 2.0
        return cx, cy

    def draw(self, x, y, w, h, ax) -> Artist:
        raise NotImplementedError

    def legend(self, x, y, w, h) -> Artist:
        return self.draw(x, y, w, h, None)

    def legend_artist(self, legend, orig_handle, fontsize, handlebox):
        x, y = handlebox.xdescent, handlebox.ydescent
        w, h = handlebox.width, handlebox.height
        p = self.legend(-x, -y, w, h)
        handlebox.add_artist(p)
        return p


class Rect(Piece):
    def __init__(self, color="C0", label=None, legend=True, zorder=0):
        self.color = color
        self.label = label
        self.legend_entry = legend
        self.zorder = zorder

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(color='{self.color}', " f"label='{self.label}')"
        )

    def draw(self, x, y, w, h, ax) -> Artist:
        return Rectangle((x, y), w, h, facecolor=self.color)


class FracRect(Piece):
    def __init__(self, color="C0", frac=(0.9, 0.5), label=None, legend=True, zorder=0):
        self.color = color
        self.label = label
        self.frac = frac
        self.legend_entry = legend
        self.zorder = zorder

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(color='{self.color}', " f"label='{self.label}')"
        )

    def draw(self, x, y, w, h, ax):
        fx, fy = self.frac
        draw_w, draw_h = w * fx, h * fy
        # compute the actual drawing bbox
        # Lower-left corner
        draw_x = x + (w - draw_w) / 2.0
        draw_y = y + (h - draw_h) / 2.0
        return Rectangle((draw_x, draw_y), draw_w, draw_h, fc=self.color)


class FrameRect(Piece):
    def __init__(self, color="C0", width=1, label=None, legend=True, zorder=0):
        self.color = color
        self.width = width
        self.label = label
        self.legend_entry = legend
        self.zorder = zorder

    def __repr__(self):
        return f"{self.__class__.__name__}(color={self.color}, " f"label={self.label})"

    def draw(self, x, y, w, h, ax):
        return Rectangle((x, y), w, h, fill=False, ec=self.color, linewidth=self.width)


class RightTri(Piece):
    point_order = {
        "lower left": [1, 0, 3],
        "lower right": [2, 0, 3],
        "upper left": [0, 1, 2],
        "upper right": [1, 2, 3],
    }

    def __init__(
        self, color="C0", right_angle="lower left", label=None, legend=True, zorder=0
    ):
        self.color = color
        self.pos = right_angle
        self.label = label
        self.legend_entry = legend
        self.zorder = zorder

    def __repr__(self):
        return f"{self.__class__.__name__}(color={self.color}, " f"label={self.label})"

    def draw(self, x, y, w, h, ax):
        p0 = (x, y)
        p1 = (x, y + h)
        p2 = (x + w, y + h)
        p3 = (x + w, y)
        points = np.array([p0, p1, p2, p3])
        ps = points[self.point_order[self.pos]]
        return Polygon(ps, fc=self.color)


class Marker(Piece):
    def __init__(self, marker, color="C0", size=32, label=None, legend=True, zorder=0):
        self.color = color
        self.label = label
        self.legend_entry = legend
        self.zorder = zorder
        self.size = size
        m = MarkerStyle(marker)
        self.path = m.get_path().transformed(m.get_transform())

    def draw(self, x, y, w, h, ax):
        c = self.draw_center(x, y, w, h)
        collection = PathCollection(
            (self.path,),
            [self.size],
            offsets=[c],
            offset_transform=ax.transData,
            facecolors=self.color,
        )
        collection.set_transform(IdentityTransform())

        return collection

    def legend(self, x, y, w, h):
        return Line2D(
            [0], [0], marker=self.marker, color=self.color, markersize=self.size
        )


def preview(piece: Piece, figsize=(1, 1)):
    figure = plt.figure(figsize=figsize)
    ax = figure.add_axes([0, 0, 1, 1])
    close_ticks(ax)
    arts = piece.draw(0, 0, 1, 1, ax)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.add_artist(arts)
