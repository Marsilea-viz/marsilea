import pytest
import numpy as np
from matplotlib import pyplot as plt

from heatgraphy.plotter.mesh import ColorMesh, Colors, \
    TextMesh, SizedMesh, MarkerMesh

COLUMN = 20
ROW = 20

matrix = np.random.randint(0, 101, (ROW, COLUMN))
cat_matrix = np.random.choice([1, 2, 3, 4], (ROW, COLUMN))

label = np.random.choice(list("abcdefg"), ROW)

stats_data = np.random.randn(10, ROW)

numbers = np.random.randint(10, 100, ROW)


def test_colormesh():
    _, ax = plt.subplots()
    ColorMesh(matrix).render(ax)
    plt.close()


def test_colors():
    _, ax = plt.subplots()
    Colors(cat_matrix).render(ax)
    plt.close()
