import numpy as np
from heatgraphy.plotter.mesh import ColorMesh, Colors, LayersMesh, \
    TextMesh, SizedMesh, MarkerMesh

data = np.random.randn(10, 30)


def test_colormesh():
    ColorMesh(data).render()

