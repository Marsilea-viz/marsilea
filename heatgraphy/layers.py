import numpy as np
from matplotlib import pyplot as plt
from matplotlib.artist import Artist
from matplotlib.patches import Rectangle, Polygon

from .plotter import LayersMesh
from .base import MatrixBase
from .layout import close_ticks


class Layers(MatrixBase):

    def __init__(self,
                 data=None,
                 layers=None,
                 pieces=None,
                 cluster_data=None,
                 shrink=(1., 1.),
                 height=None,
                 width=None,
                 aspect=1.,
                 name=None,
                 ):

        mesh = LayersMesh(data=data, layers=layers, pieces=pieces,
                          shrink=shrink)
        if cluster_data is None:
            self._allow_cluster = False
            if mesh.mode == "cell":
                data_shape = mesh.data.shape
            else:
                data_shape = mesh.data[0].shape
            # create numeric data explicitly
            # in case user input string data
            cluster_data = np.random.randn(*data_shape)
        if (width is not None) & (height is not None):
            main_aspect = height / width
        else:
            Y, X = cluster_data.shape
            main_aspect = Y * aspect / X
        super().__init__(cluster_data, main_aspect=main_aspect, 
                         w=width, h=height, name=name)

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
        cx = x + w / 2.
        cy = y + h / 2.
        return cx, cy

    def transform_frac(self, x, y, w, h):
        x = x + w * ((1 - self.frac_x) / 2)
        y = y + h * ((1 - self.frac_y) / 2)
        w = w * self.frac_x
        h = h * self.frac_y
        return x, y, w, h

    def draw(self, x, y, w, h) -> Artist:
        raise NotImplemented

    def legend(self, x, y, w, h) -> Artist:
        return self.draw(x, y, w, h)

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
        return f"{self.__class__.__name__}(color='{self.color}', " \
               f"label='{self.label}')"

    def draw(self, x, y, w, h) -> Artist:
        return Rectangle((x, y), w, h, facecolor=self.color)


# class Bg(Piece):
#
#     def __init__(self, color="C0", label=None, legend=True):
#         self.color = color
#         self.label = label
#         self.legend_entry = legend
#
#     def __repr__(self):
#         return f"{self.__class__.__name__}(color='{self.color}', " \
#                f"label='{self.label}')"
#
#     def draw(self, x, y, w, h):
#         return Rectangle((x, y), w, h, fc=self.color)


class FracRect(Piece):
    def __init__(self, color="C0", frac=(.9, .5), label=None, legend=True, zorder=0):
        self.color = color
        self.label = label
        self.frac = frac
        self.legend_entry = legend
        self.zorder = zorder

    def __repr__(self):
        return f"{self.__class__.__name__}(color='{self.color}', " \
               f"label='{self.label}')"

    def draw(self, x, y, w, h):
        fx, fy = self.frac
        draw_w, draw_h = w * fx, h * fy
        # compute the actual drawing bbox
        # Lower-left corner
        draw_x = x + (w - draw_w) / 2.
        draw_y = y + (h - draw_h) / 2.
        return Rectangle((draw_x, draw_y), draw_w, draw_h, fc=self.color)


class FrameRect(Piece):
    def __init__(self, color="C0", width=1, label=None, legend=True, zorder=0):
        self.color = color
        self.width = width
        self.label = label
        self.legend_entry = legend
        self.zorder = zorder

    def __repr__(self):
        return f"{self.__class__.__name__}(color={self.color}, " \
               f"label={self.label})"

    def draw(self, x, y, w, h):
        return Rectangle((x, y), w, h,
                         fill=False,
                         ec=self.color,
                         linewidth=self.width)


class RightTri(Piece):

    point_order = {
        "lower left": [1, 0, 3],
        "lower right": [2, 0, 3],
        "upper left": [0, 1, 2],
        "upper right": [1, 2, 3],
    }

    def __init__(self, color="C0", right_angle="lower left",
                 label=None, legend=True, zorder=0):
        self.color = color
        self.pos = right_angle
        self.label = label
        self.legend_entry = legend
        self.zorder = zorder

    def __repr__(self):
        return f"{self.__class__.__name__}(color={self.color}, " \
               f"label={self.label})"

    def draw(self, x, y, w, h):
        p0 = (x, y)
        p1 = (x, y + h)
        p2 = (x + w, y + h)
        p3 = (x + w, y)
        points = np.array([p0, p1, p2, p3])
        ps = points[self.point_order[self.pos]]
        return Polygon(ps, fc=self.color)


def preview(piece: Piece, figsize=(1, 1)):
    figure = plt.figure(figsize=figsize)
    ax = figure.add_axes([0, 0, 1, 1])
    close_ticks(ax)
    arts = piece.draw(0, 0, 1, 1)
    ax.add_artist(arts)
