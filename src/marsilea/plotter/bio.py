import numpy as np
import pandas as pd
from matplotlib.patches import PathPatch
from matplotlib.textpath import TextPath
from matplotlib.transforms import Affine2D, Bbox

from .base import StatsBase
from ..utils import pairwise, ECHARTS16


def path_char(
    pos,
    extend,
    t,
    ax,
    width=1.0,
    flip=False,
    mirror=False,
    direction="h",
    prop=None,
    usetex=False,
    **kwargs,
):
    w = width
    h = extend[1] - extend[0]

    x = pos - w / 2
    y = extend[0]

    if prop is None:
        prop = dict(family="monospace")
    tmp_path = TextPath((0, 0), t, size=1, prop=prop, usetex=usetex)

    if flip:
        transformation = Affine2D().scale(sx=1, sy=-1)
        tmp_path = transformation.transform_path(tmp_path)

    if mirror:
        transformation = Affine2D().scale(sx=-1, sy=1)
        tmp_path = transformation.transform_path(tmp_path)

    if direction == "v":
        w, h = h, w
        x, y = y, x

        rotate = Affine2D().rotate_deg(90)
        tmp_path = rotate.transform_path(tmp_path)

    bbox = Bbox.from_bounds(x, y, w, h)
    tmp_bbox = tmp_path.get_extents()

    hs = bbox.width / tmp_bbox.width
    vs = bbox.height / tmp_bbox.height

    if direction == "h":
        char_width = hs * tmp_bbox.width
        char_shift = (bbox.width - char_width) / 2.0
        tx = bbox.xmin + char_shift
        ty = bbox.ymin

    else:
        char_height = vs * tmp_bbox.height
        char_shift = (bbox.height - char_height) / 2.0
        tx = bbox.xmin
        ty = bbox.ymin + char_shift

    transformation = (
        Affine2D()
        .translate(tx=-tmp_bbox.xmin, ty=-tmp_bbox.ymin)
        .scale(sx=hs, sy=vs)
        .translate(tx=tx, ty=ty)
    )

    char_path = transformation.transform_path(tmp_path)

    patch = PathPatch(char_path, **kwargs)
    ax.add_patch(patch)


class SeqLogo(StatsBase):
    """Sequence logo

    Parameters
    ----------
    matrix : pandas.DataFrame
        Drawing matrix, the data is the height of logo
        with columns as positions and rows as nucleotides/amino acids letters.
    width : float, optional
        The width of each letter, by default .9, should be within [0, 1]
    color_encode : dict, optional
        The color encoding for each letter,
        should be a dict with key as letter and value as color
    stack : {"descending", "ascending", "normal"}, default: "descending"
        The stacking order of letters, by height. If normal will stack
        as the order in matrix.

    Examples
    --------

    .. plot::
        :context: close-figs

        >>> import pandas as pd
        >>> from marsilea.plotter import SeqLogo
        >>> matrix = pd.DataFrame(
        ...     data=np.random.randint(1, 10, (4, 10)), index=list("ACGT")
        ... )
        >>> _, ax = plt.subplots()
        >>> colors = {"A": "r", "C": "b", "G": "g", "T": "black"}
        >>> SeqLogo(matrix, color_encode=colors).render(ax)

    """

    render_main = False

    def __init__(
        self,
        matrix: pd.DataFrame,
        width=0.9,
        color_encode=None,
        stack="descending",  # "descending", "ascending", "normal"
        **kwargs,
    ):
        self.matrix = matrix
        self.letters = matrix.index.to_numpy()
        self.set_data(matrix.to_numpy())
        if color_encode is None:
            color_encode = dict(zip(self.letters, ECHARTS16))
        self.color_encode = color_encode
        self.width = width
        self.stack = stack
        self.options = kwargs

    def render_ax(self, spec):
        ax = spec.ax
        data = spec.data

        direction = "h" if self.is_body else "v"
        flip = self.side != "top"
        mirror = self.side == "left"
        lim = np.max(data.sum(axis=0))
        for i, col in enumerate(data.T):
            letters = self.letters
            if self.stack != "normal":
                ix = np.argsort(col)
                if self.stack == "ascending":
                    ix = ix[::-1]
                letters = letters[ix]
                col = col[ix]

            extends = [0] + list(np.cumsum(col))
            pos = i + 0.5
            for t, extend in zip(letters, pairwise(extends)):
                facecolor = self.color_encode[t]
                options = {"facecolor": facecolor, "edgecolor": "none", **self.options}
                path_char(
                    pos,
                    extend,
                    t,
                    ax,
                    flip=flip,
                    mirror=mirror,
                    width=self.width,
                    direction=direction,
                    **options,
                )
        if self.is_body:
            ax.set_xlim(0, data.shape[1])
            ax.set_ylim(0, lim)
        else:
            ax.set_xlim(0, lim)
            ax.set_ylim(0, data.shape[1])
        if self.is_flank:
            ax.invert_yaxis()
        if self.side == "left":
            ax.invert_xaxis()
        if self.side == "bottom":
            ax.invert_yaxis()
        ax.set_axis_off()
