from __future__ import annotations

import logging

import matplotlib.pyplot as plt
import numpy as np

from .base import MatrixBase, _Base
from .plotter import ColorMesh, CircleMesh

log = logging.getLogger("heatgraphy")


class Heatmap(MatrixBase):

    def __init__(self, data: np.ndarray, vmin=None, vmax=None,
                 cmap=None, norm=None, center=None, robust=None,
                 mask=None, alpha=None, linewidth=0, linecolor="white",
                 annot=None, fmt=None, annot_kws=None,
                 square=False,
                 ):
        if mask is not None:
            data = np.ma.masked_where(np.asarray(mask), data).filled(np.nan)
        self.data = data
        self.square = square

        data_aspect = 1
        if square:
            Y, X = data.shape
            data_aspect = Y / X
        super().__init__(data, data_aspect=data_aspect)
        self._mesh = ColorMesh(data, vmin=vmin, vmax=vmax, cmap=cmap,
                               norm=norm, center=center, robust=robust,
                               alpha=alpha, linewidth=linewidth,
                               linecolor=linecolor,
                               annot=annot, fmt=fmt,
                               annot_kws=annot_kws
                               )
        self._mesh.set_side("main")

    def render(self, figure=None, aspect=1):
        if figure is None:
            self.figure = plt.figure()
        else:
            self.figure = figure

        deform = self.get_deform()
        self._mesh.set_deform(deform)
        # trans_data = deform.transform(self.data)
        # trans_texts = deform.transform(self._mesh.annotated_texts)
        # if deform.is_split:
        #     self._mesh.set_render_data(
        #         [d for d in zip(trans_data, trans_texts)]
        #     )
        # else:
        #     self._mesh.set_render_data((trans_data, trans_texts))

        # Make sure all axes is split
        self._setup_axes()
        # Place axes
        aspect = 1 if self.square else aspect
        if not self.grid.is_freeze:
            self.grid.freeze(figure=self.figure, aspect=aspect)
        main_axes = self.get_main_ax()
        self._mesh.render(main_axes)

        # add row and col dendrogram
        self._render_dendrogram()

        # render other plots
        self._render_plan()
        self._render_legend()

    def get_main_legends(self):
        return self._mesh.get_legends()


class DotHeatmap(MatrixBase):

    def __init__(self, size, color, cluster_data=None, sizes=(1, 200),
                 alpha=1.0, cmap=None, norm=None):
        cluster_data = color
        y, x = cluster_data.shape
        super().__init__(cluster_data, data_aspect=y / x)

        self._mesh = CircleMesh(size=size, color=color)
        self._bg_mesh = None

    def add_matrix(self, data: np.ndarray, vmin=None, vmax=None, cmap=None,
                   norm=None, center=None, robust=None, mask=None,
                   alpha=None, linewidth=None, edgecolor=None,
                   ):
        self._bg_mesh = ColorMesh(data, cmap=cmap, norm=norm, vmin=vmin,
                                  vmax=vmax, center=center, robust=robust,
                                  alpha=alpha, linewidth=linewidth,
                                  edgecolor=edgecolor)

    def render(self, figure=None, aspect=1):
        if figure is None:
            self.figure = plt.figure()
        else:
            self.figure = figure

        deform = self.get_deform()

        if self._bg_mesh is not None:
            trans_matrix = deform.transform(self._bg_mesh.data)
            self._bg_mesh.set_render_data(trans_matrix)

        trans_size = deform.transform(self._mesh.size)
        trans_color = deform.transform(self._mesh.color)
        if deform.is_split:
            self._mesh.set_render_data(
                [(s, c) for s, c in zip(trans_size, trans_color)]
            )
        else:
            self._mesh.set_render_data((trans_size, trans_color))

        # Make sure all axes is split
        self._setup_axes()
        # Place axes
        # If freeze by other instance, we just draw on it
        # freeze again will clear the figure
        if not self.grid.is_freeze:
            self.grid.freeze(figure=self.figure, aspect=aspect)
        main_axes = self.get_main_ax()
        if self._bg_mesh is not None:
            self._bg_mesh.render(main_axes)
        self._mesh.render(main_axes)

        self._render_dendrogram()
        self._render_plan()

    def get_main_legends(self):
        if self._bg_mesh is None:
            return self._mesh.get_legends()
        else:
            return [*self._mesh.get_legends(), self._bg_mesh.get_legends()]


class CatHeatmap(_Base):
    pass
