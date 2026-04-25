import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest


@pytest.fixture(autouse=True)
def close_figures():
    yield
    plt.close("all")


@pytest.fixture
def rng():
    return np.random.default_rng(42)


@pytest.fixture
def matrix_10x8(rng):
    return rng.standard_normal((10, 8))


@pytest.fixture
def matrix_5x4(rng):
    return rng.standard_normal((5, 4))


@pytest.fixture
def cat_data_10x8(rng):
    return rng.choice([1, 2, 3], size=(10, 8))


@pytest.fixture
def labels_10():
    return [f"row{i}" for i in range(10)]


@pytest.fixture
def labels_8():
    return [f"col{i}" for i in range(8)]
