from itertools import product

import pytest
import numpy as np
from heatgraphy import Deformation

matrix = np.random.randn(7, 5)

col1d = np.array([1, 2, 3, 4, 5])
col2d = np.array([[1, 2, 3, 4, 5],
                  [1, 2, 3, 4, 5]])

row1d = np.array([1, 2, 3, 4, 5, 6, 7])
row2d = np.array([[1, 2, 3, 4, 5, 6, 7],
                  [1, 2, 3, 4, 5, 6, 7]])

row_cluster = [True, False]
col_cluster = [True, False]
split_row = [True, False]
split_col = [True, False]


@pytest.mark.parametrize(
    "row_cluster,col_cluster,split_row,split_col,tdata",
    product(row_cluster, col_cluster, split_row, split_col, [col1d, col2d]))
def test_deform_trans_col(row_cluster, col_cluster, split_row, split_col,
                          tdata):
    deform = Deformation(matrix)
    deform.set_cluster(col=col_cluster, row=row_cluster)
    if split_col:
        deform.set_split_col([2])
    if split_row:
        deform.set_split_row([2])
    results = deform.transform_col(tdata)

    total = 0
    if isinstance(results, np.ndarray):
        total = results.size
    else:
        for i in results:
            total += i.size

    assert total == tdata.size


@pytest.mark.parametrize(
    "row_cluster,col_cluster,split_row,split_col,tdata",
    product(row_cluster, col_cluster, split_row, split_col, [row1d, row2d]))
def test_deform_trans_row(row_cluster, col_cluster, split_row, split_col,
                          tdata):
    deform = Deformation(matrix)
    deform.set_cluster(col=col_cluster, row=row_cluster)
    if split_col:
        deform.set_split_col([2])
    if split_row:
        deform.set_split_row([2])
    results = deform.transform_row(tdata)

    total = 0
    if isinstance(results, np.ndarray):
        total = results.size
    else:
        for i in results:
            total += i.size

    assert total == tdata.size


@pytest.mark.parametrize(
    "row_cluster,col_cluster,split_row,split_col",
    product(row_cluster, col_cluster, split_row, split_col))
def test_deform_trans_both(row_cluster, col_cluster, split_row, split_col):
    deform = Deformation(matrix)
    deform.set_cluster(col=col_cluster, row=row_cluster)
    if split_col:
        deform.set_split_col([2])
    if split_row:
        deform.set_split_row([2])
    results = deform.transform(matrix)

    total = 0
    if isinstance(results, np.ndarray):
        total = results.size
    elif isinstance(results[0], np.ndarray):
        for i in results:
            total += i.size
    else:
        for row in results:
            for i in row:
                total += i.size

    assert total == matrix.size
