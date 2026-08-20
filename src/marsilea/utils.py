import os
import re
import sys

import matplotlib as mpl
import numpy as np
from itertools import tee, islice
from matplotlib import colors as mcolors
from uuid import uuid4

#: Everything under here is marsilea's own code, so it is never the caller.
_PKG_DIR = os.path.dirname(os.path.abspath(__file__))

#: marimo compiles a cell from a temp file with the cell id in its name. Same
#: rule marimo reads it back with, kept here so nothing has to import marimo.
_MARIMO_CELL = re.compile(r"^__marimo__cell_(.*?)_")

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
        return mpl.colormaps.get_cmap(cmap)
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


def _inside_marsilea(filename):
    """Whether a frame's file is marsilea's own code.

    Compared at the directory boundary rather than as a string prefix: a
    sibling package such as ``marsilea_extra`` starts with the same path
    without being any of ours, and treating it as ours would walk straight
    past the caller.
    """
    return filename.startswith(_PKG_DIR + os.sep)


def _notebook_location(filename, lineno):
    """``Cell In[3]:12`` or ``marimo cell Hbol:12``, or None for a real file.

    A notebook compiles every cell from a throwaway path such as
    ``/tmp/ipykernel_913/2179451630.py``, which tells the reader nothing about
    where to go and look. Jupyter knows the execution count behind that path,
    and marimo writes the cell id into the name, so both can do better.
    """
    # Probe sys.modules rather than import, the way marsilea._sources detects
    # its data containers. No shell running means no cells can exist.
    ipython = sys.modules.get("IPython")
    if ipython is not None:
        try:
            label = ipython.get_ipython().compile.format_code_name(filename)
        except Exception:
            # Naming a frame is a nicety, never let it replace the real error.
            label = None
        if label is not None:
            kind, name = label
            return f"{kind} {name}:{lineno}"

    cell = _MARIMO_CELL.match(os.path.basename(filename))
    if cell is not None:
        return f"marimo cell {cell.group(1)}:{lineno}"
    return None


def caller_location():
    """Where the caller is, as ``file:line`` or ``Cell In[3]:12``, or None.

    A board is built lazily, so a plotter that fails at render was added
    somewhere the traceback never mentions. Recording the ``add_*`` call site
    is what lets the render-time error point back at it.
    """
    frame = sys._getframe(1)
    while frame is not None:
        filename = frame.f_code.co_filename
        if not _inside_marsilea(filename):
            lineno = frame.f_lineno
            return _notebook_location(filename, lineno) or f"{filename}:{lineno}"
        frame = frame.f_back
    return None


def find_stack_level():
    """The ``stacklevel`` that makes a warning point at the caller's own line.

    Counting frames by hand only holds until something between the warning and
    the user grows a layer, and then the warning quietly blames marsilea. Walk
    out of the package instead and let the number follow the code.
    """
    frame = sys._getframe(1)  # the warnings.warn() call site
    level = 1
    while frame is not None and _inside_marsilea(frame.f_code.co_filename):
        frame = frame.f_back
        level += 1
    return level
