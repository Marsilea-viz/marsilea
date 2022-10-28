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
                 shrink=(.9, .9)
                 ):
        self._mesh = LayersMesh(data=data, layers=layers, pieces=pieces,
                                shrink=shrink)
        if cluster_data is None:
            self._allow_cluster = False
            if self._mesh.mode == "cell":
                data_shape = self._mesh.data.shape
            else:
                data_shape = self._mesh.data[0].shape
            # create numeric data explicitly
            # in case user input string data
            cluster_data = np.random.randn(*data_shape)
        super().__init__(cluster_data)

    def render(self, figure=None, aspect=1):
        if figure is None:
            self.figure = plt.figure()
        else:
            self.figure = figure

        deform = self.get_deform()
        if self._mesh.mode == "cell":
            trans_data = deform.transform(self._mesh.data)
            self._mesh.set_render_data(trans_data)
        else:
            trans_layers = [
                deform.transform(layer) for layer in self._mesh.data]
            if deform.is_split:
                self._mesh.set_render_data(
                    [chunk for chunk in zip(*trans_layers)])
            else:
                self._mesh.set_render_data(trans_layers)

        self._setup_axes()
        self.grid.freeze(figure=self.figure, aspect=aspect)
        self.main_axes = self.grid.get_main_ax()

        self._mesh.render(self.main_axes)
        # render other plots
        self._render_dendrogram()
        self._render_plan()


class Piece:
    frac_x = 1
    frac_y = 1

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

    def __init__(self, color="C0"):
        self.color = color

    def draw(self, x, y, w, h) -> Artist:
        return Rectangle((x, y), w, h, facecolor=self.color)


class Bg(Piece):

    def __init__(self, color="C0"):
        self.color = color

    def draw(self, x, y, w, h):
        return Rectangle((x, y), w, h, fc=self.color)


class FracRect(Piece):
    def __init__(self, color="C0", frac=(.9, .5)):
        self.color = color
        self.set_frac(frac)

    def draw(self, x, y, w, h):
        x, y, w, h = self.transform_frac(x, y, w, h)
        return Rectangle((x, y), w, h, fc=self.color)


class FrameRect(Piece):
    def __init__(self, color="C0", width=1):
        self.color = color
        self.width = width

    def draw(self, x, y, w, h):
        return Rectangle((x, y), w, h,
                         fill=False,
                         ec=self.color,
                         linewidth=self.width)


class RTri(Piece):

    def __init__(self, color="C0", right_angle="lower left", frac=(1, 1)):
        self.color = color
        self.pos = right_angle
        self.set_frac(frac)

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
