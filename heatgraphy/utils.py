from itertools import tee, islice, zip_longest
from uuid import uuid4

import numpy as np
import matplotlib as mpl
from matplotlib import colors as mcolors
from matplotlib.colors import Colormap


ECHARTS16 = [
    "#5470c6", "#91cc75", "#fac858", "#ee6666",
    "#9a60b4", "#73c0de", "#3ba272", "#fc8452",
    "#27727b", "#ea7ccc", "#d7504b", "#e87c25",
    "#b5c334", "#fe8463", "#26c0c0", "#f4e001"
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
    "Batch data into lists of length n. The last batch may be shorter."
    # batched('ABCDEFG', 3) --> ABC DEF G
    if n < 1:
        raise ValueError('n must be at least one')
    it = iter(iterable)
    while (batch := list(islice(it, n))):
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
    rgb = np.where(rgb <= .03928, rgb / 12.92, ((rgb + .055) / 1.055) ** 2.4)
    lum = rgb.dot([.2126, .7152, .0722])
    try:
        return lum.item()
    except ValueError:
        return lum


def get_colormap(cmap):
    if isinstance(cmap, Colormap):
        return cmap
    try:
        return mpl.colormap.get(cmap)
    except AttributeError:
        return mpl.cm.get_cmap(cmap)


def get_canvas_size(width=None, height=None, aspect=1):
    """
    To adaptively determine the size a canvas

    Parameters
    ----------
    width : float
    height : float
    aspect : float
        The ratio of height to width

    Returns
    -------
    (height, width)

    """
    set_w = width is not None
    set_h = height is not None
    # if user set both side, the aspect is ignored

    if set_w & set_h:
        box = height, width
    # if only width is set
    elif set_w:
        box = width * aspect, width
    # if only height is set
    elif set_h:
        box = height, height / aspect
    # if none is set, we explicitly give it a value
    else:
        width = 5
        box = width * aspect, width
    return np.array(box, dtype=float)


def get_plot_name(name=None, side=None, chart=None):
    if name is None:
        return f"{chart}-{side}-{uuid4().hex}"
    else:
        return name


