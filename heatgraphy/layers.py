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
                 shrink=(1, 1)
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
        Y, X = cluster_data.shape
        main_aspect = Y * 3 / X
        super().__init__(cluster_data, main_aspect=main_aspect)

        self.add_layer(mesh)


class Piece:
    frac_x = 1
    frac_y = 1
    label = None
    legend_entry = True

    def get_label(self):
        if self.label is None:
            return self.__class__.__name__
        else:
            return self.label

    def set_label(self, label):
        self.label = label

    def set_frac(self, frac):
        self.frac_x, self.frac_y = frac

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

    def __init__(self, color="C0", label=None, legend=True):
        self.color = color
        self.label = label
        self.legend_entry = legend

    def __repr__(self):
        return f"{self.__class__.__name__}(color='{self.color}', " \
               f"label='{self.label}')"

    def draw(self, x, y, w, h) -> Artist:
        return Rectangle((x, y), w, h, facecolor=self.color)


class Bg(Piece):

    def __init__(self, color="C0", label=None, legend=True):
        self.color = color
        self.label = label
        self.legend_entry = legend

    def __repr__(self):
        return f"{self.__class__.__name__}(color='{self.color}', " \
               f"label='{self.label}')"

    def draw(self, x, y, w, h):
        return Rectangle((x, y), w, h, fc=self.color)


class FracRect(Piece):
    def __init__(self, color="C0", frac=(.9, .5), label=None, legend=True):
        self.color = color
        self.label = label
        self.set_frac(frac)
        self.legend_entry = legend

    def __repr__(self):
        return f"{self.__class__.__name__}(color='{self.color}', " \
               f"label='{self.label}')"

    def draw(self, x, y, w, h):
        x, y, w, h = self.transform_frac(x, y, w, h)
        return Rectangle((x, y), w, h, fc=self.color)


class FrameRect(Piece):
    def __init__(self, color="C0", width=1, label=None, legend=True):
        self.color = color
        self.width = width
        self.label = label
        self.legend_entry = legend

    def __repr__(self):
        return f"{self.__class__.__name__}(color={self.color}, " \
               f"label={self.label})"

    def draw(self, x, y, w, h):
        return Rectangle((x, y), w, h,
                         fill=False,
                         ec=self.color,
                         linewidth=self.width)


class RightTri(Piece):

    def __init__(self, color="C0", right_angle="lower left",
                 frac=(1, 1), label=None, legend=True):
        self.color = color
        self.pos = right_angle
        self.label = label
        self.set_frac(frac)
        self.legend_entry = legend

    def __repr__(self):
        return f"{self.__class__.__name__}(color={self.color}, " \
               f"label={self.label})"

    def draw(self, x, y, w, h):

        x, y, w, h = self.transform_frac(x, y, w, h)
        p0 = (x, y)
        p1 = (x, y + h)
        p2 = (x + w, y + h)
        p3 = (x + w, y)
        if self.pos == "lower left":
            ps = [p1, p0, p3]
        elif self.pos == "upper left":
            ps = [p0, p1, p2]
        elif self.pos == "upper right":
            ps = [p1, p2, p3]
        else:
            ps = [p2, p0, p3]
        return Polygon(ps, fc=self.color)


def preview(piece: Piece, figsize=(1, 1)):
    figure = plt.figure(figsize=figsize)
    ax = figure.add_axes([0, 0, 1, 1])
    close_ticks(ax)
    arts = piece.draw(0, 0, 1, 1)
    ax.add_artist(arts)
