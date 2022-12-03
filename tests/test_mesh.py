import pytest
import numpy as np
from matplotlib import pyplot as plt

from heatgraphy.plotter.mesh import ColorMesh, Colors, LayersMesh, \
    TextMesh, SizedMesh, MarkerMesh


def test_colormesh():
    data = np.random.randn(10, 30)
    ax = plt.subplot(111)
    ColorMesh(data).render(ax)
