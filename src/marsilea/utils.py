import matplotlib as mpl
import numpy as np
from itertools import tee, islice
from matplotlib import colors as mcolors
from uuid import uuid4

ECHARTS16 = [
    "#5470c6",
    "#91cc75",
    "#fac858",
    "#ee6666",
    "#9a60b4",
    "#73c0de",
    "#3ba272",
    "#fc8452",
    "#27727b",
    "#ea7ccc",
    "#d7504b",
    "#e87c25",
    "#b5c334",
    "#fe8463",
    "#26c0c0",
    "#f4e001",
]


def pairwise(iterable):
    """This is not available in itertools until 3.10"""
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


def grouper(iterable, n):
    """Collect data into non-overlapping fixed-length chunks or blocks"""
    args = [iter(iterable)] * n
    return zip(*args)


def batched(iterable, n):
    """Batch data into lists of length n. The last batch may be shorter."""
    # batched('ABCDEFG', 3) --> ABC DEF G
    if n < 1:
        raise ValueError("n must be at least one")
    it = iter(iterable)
    while batch := list(islice(it, n)):
        yield batch


# Copy from seaborn/utils.py
def relative_luminance(color):
    """Calculate the relative luminance of a color according to W3C standards
    Parameters
    ----------
    color : matplotlib color or sequence of matplotlib colors
        Hex code, rgb-tuple, or html color name.
    Returns
    -------
    luminance : float(s) between 0 and 1
    """
    rgb = mcolors.colorConverter.to_rgba_array(color)[:, :3]
    rgb = np.where(rgb <= 0.03928, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    lum = rgb.dot([0.2126, 0.7152, 0.0722])
    try:
        return lum.item()
    except ValueError:
        return lum


def get_colormap(cmap):
    try:
        return mpl.cm.ColormapRegistry.get_cmap(cmap)
    except AttributeError:
        try:
            return mpl.colormaps.get(cmap)
        except AttributeError:
            return mpl.cm.get_cmap(cmap)


def get_canvas_size_by_data(
    shape, width=None, height=None, scale=0.3, aspect=1, max_side=15
):
    h, w = shape
    no_w = width is None
    no_h = height is None
    # if user set both side, the aspect is ignored

    if no_h & no_w:
        width = w * scale
        height = h * scale * aspect
    elif no_h:
        # recompute scale
        scale = width / w
        height = h * scale * aspect
    elif no_w:
        scale = height / h
        width = w * scale / aspect
    size = np.array([width, height])
    if size.max() > max_side:
        size = size / size.max() * max_side
    width, height = size

    return width, height


def get_plot_name(name=None, side=None, chart=None):
    if name is None:
        return f"{chart}-{side}-{uuid4().hex}"
    else:
        return name


def _check_side(side):
    """Check user input the correct word"""
    options = ["top", "bottom", "left", "right"]
    if side not in options:
        raise ValueError(f"`side` must be one of {options}.")
