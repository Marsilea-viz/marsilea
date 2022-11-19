from itertools import tee

import numpy as np
import matplotlib as mpl
from matplotlib import colors as mcolors
from matplotlib.colors import Colormap


def pairwise(iterable):
    """This is not available in itertools until 3.10"""
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


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


