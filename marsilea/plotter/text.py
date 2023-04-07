from __future__ import annotations

import warnings
from dataclasses import dataclass
from typing import List, Iterable

import matplotlib.pyplot as plt
import numpy as np
# from icecream import ic
from matplotlib.axes import Axes
from matplotlib.colors import is_color_like
from matplotlib.patches import Rectangle
from matplotlib.text import Text

from .base import RenderPlan
from ..utils import pairwise, relative_luminance


class Segment:
    """
    The total length is unchanged
    """
    up: float
    low: float

    # limit
    max: float = None
    min: float = None

    def __repr__(self):
        return f"Segments({self.label}: {self.low:.2f} - {self.up:.2f})"

    def __init__(self, low, up, label=""):
        self.low = low
        self.up = up
        self._length = up - low

        self.side = None
        self.label = label

    @property
    def length(self):
        return self._length

    @property
    def mid(self):
        return self.length / 2 + self.low

    def overlap(self, other):
        # Other on the right or left
        if self.low >= other.up or other.low >= self.up:
            return False
        else:
            return True

    def set_lim(self, lim):
        if lim.length < self.length:
            raise ValueError("Length of the limit is too short")
        self.max = lim.up
        self.min = lim.low
        # If lower than the lim
        if self.low < self.min:
            self.low = self.min
            self.up = self.low + self.length
        # If upper than the lim
        if self.up > self.max:
            self.up = self.max
            self.low = self.up - self.length

    def move_up(self, offset):
        # check if move across lim
        final_up = self.up + offset
        if final_up <= self.max:
            self.set_up(final_up)
        else:
            self.set_up(self.max)

    def move_down(self, offset):
        # check if move across lim
        final_low = self.low - offset
        if final_low >= self.min:
            self.set_low(final_low)
        else:
            self.set_low(self.min)

    def set_up(self, up):
        if up <= self.max:
            final_low = up - self.length
            if final_low >= self.min:
                self.low = final_low
                self.up = up

    def set_low(self, low):
        if low >= self.min:
            final_up = low + self.length
            if final_up <= self.max:
                self.low = low
                self.up = final_up


def adjust_segments(lim: Segment, segments: List[Segment]):
    """Assume the segments is ascending"""
    # Check the order
    sl = []
    for s in segments:
        sl.append(s.length)
        s.set_lim(lim)

    segments_length = np.sum(sl)
    space = lim.length
    if segments_length > space:
        warnings.warn("No enough space to place all labels, "
                      "try reducing the fontsize.")

    segments_length_r = segments_length
    space_r = space

    for ix, (s1, s2) in enumerate(pairwise(segments)):
        if ix == 0:
            distance = s1.low - lim.low
            offset = segments_length - (space - distance)
            if offset > 0:
                if offset > distance:
                    s1.set_low(lim.low)
                else:
                    s1.move_down(offset)

        space -= s1.length
        segments_length -= s1.length
        if s1.overlap(s2) or s2.up < s1.low:
            # if overlapped, make s2 next to s1
            s2.set_low(s1.up)
        else:
            # space between s1 and s2
            distance = s2.low - s1.up

            offset = segments_length - (space - distance)
            # if what's left is not enough to place remaining
            # The total segments is longer than remain space
            if offset > 0:
                # This means no enough space
                # We could only overlay them
                if offset > distance:
                    s2.set_low(s1.up)
                else:
                    s2.move_down(offset)

    for ix, (s1, s2) in enumerate(pairwise(segments[::-1])):
        if ix == 0:
            distance = s1.up - lim.up
            offset = segments_length_r - (space_r - distance)
            if offset > 0:
                if offset > distance:
                    s1.set_up(lim.up)
                else:
                    s1.move_up(offset)

        space_r -= s1.length
        segments_length_r -= s1.length
        if s1.overlap(s2) or s2.low > s1.up:
            # if overlapped, make s2 next to s1
            s2.set_up(s1.low)
        else:
            # space between s1 and s2
            distance = s2.low - s1.up

            offset = segments_length_r - (space_r - distance)
            # if what's left is not enough to place remaining
            # The total segments is longer than remain space
            if offset > 0:
                # This means no enough space
                # We could only overlay them
                if offset > distance:
                    s2.set_up(s1.low)
                else:
                    s2.move_up(offset)


# For debug purpose
def plot_segments(segments, lim=None):
    ys = []
    xmin = []
    xmax = []
    for ix, s in enumerate(segments):
        ys.append(ix % 2 + 1)
        xmin.append(s.low)
        xmax.append(s.up)

    _, ax = plt.subplots()

    if lim is not None:
        # Draw the lim
        ax.axhline(y=0, xmin=lim.low, xmax=lim.up, color="black")
        ax.axvline(x=lim.low, color="black", linestyle="dashed")
        ax.axvline(x=lim.up, color="black", linestyle="dashed")

    ax.hlines(ys, xmin, xmax)
    ax.set_ylim(-0.5, 5)


class AdjustableText:

    def __init__(self, x, y, text,
                 ax=None, renderer=None,
                 pointer=None,
                 expand=(1.05, 1.05),
                 va=None, ha=None, rotation=None,
                 connectionstyle=None, relpos=None,
                 linewidth=None,
                 **kwargs):
        if ax is None:
            ax = plt.gca()
        if renderer is None:
            fig = plt.gcf()
            renderer = fig.canvas.get_renderer()
        self.ax = ax
        self.renderer = renderer
        if pointer is None:
            pointer = (x, y)
        self.pointer = pointer
        self.x = x
        self.y = y
        self.text = text

        self.va = va
        self.ha = ha
        self.rotation = rotation
        self.connectionstyle = connectionstyle
        self.relpos = relpos
        self.linewidth = linewidth
        self.text_obj = Text(x, y, text, va=va, ha=ha,
                             rotation=rotation,
                             transform=self.ax.transAxes,
                             **kwargs)
        self.text_options = kwargs
        ax.add_artist(self.text_obj)
        self._bbox = self.text_obj.get_window_extent(self.renderer) \
            .expanded(*expand)
        self.annotation = None

    def get_display_coordinate(self):
        return self.text_obj.get_transform().transform((self.x, self.y))

    def get_bbox(self):
        return self._bbox

    def get_segment_x(self):
        return Segment(self._bbox.xmin, self._bbox.xmax, label=self.text)

    def get_segment_y(self):
        return Segment(self._bbox.ymin, self._bbox.ymax, label=self.text)

    def set_display_coordinate(self, tx, ty):
        x, y = self.ax.transAxes.inverted().transform((tx, ty))
        self.x = x
        self.y = y

    def set_display_x(self, tx):
        x, _ = self.ax.transAxes.inverted().transform((tx, 0))
        self.x = x

    def set_display_y(self, ty):
        _, y = self.ax.transAxes.inverted().transform((0, ty))
        self.y = y

    def redraw(self):
        self.text_obj.set_position((self.x, self.y))

    def draw_annotate(self):
        self.text_obj.remove()
        self.annotation = self.ax.annotate(
            self.text,
            xy=self.pointer,
            xytext=(self.x, self.y),
            va=self.va,
            ha=self.ha,
            rotation=self.rotation,
            transform=self.ax.transAxes,
            arrowprops=dict(
                arrowstyle="-",
                connectionstyle=self.connectionstyle,
                linewidth=self.linewidth,
                relpos=self.relpos),
            **self.text_options
        )


# A container class for store arbitrary text params
class TextParams:
    _ha: str
    _va: str
    rotation = 0

    def __init__(self, **params):
        self._params = {}
        self.update_params(params)

    def update_params(self, params):
        for k, v in params.items():
            if k in ["ha", "horizontalalignment"]:
                self._ha = v
            elif k in ["va", "verticalalignment"]:
                self._va = v
            else:
                self._params[k] = v

    def to_dict(self):
        p = dict(
            va=self._va,
            ha=self._ha,
            rotation=self.rotation
        )
        p.update(self._params)
        return p


class _LabelBase(RenderPlan):
    is_flex = True
    texts_size = None
    padding = 0
    text_pad = 0
    text_gap = 0

    def __init__(self):
        # Params hard set by user
        self._user_params = {}

    def _sort_params(self, **params):
        for k, v in params.items():
            if v is not None:
                self._user_params[k] = v

    def get_text_params(self) -> TextParams:
        raise NotImplementedError

    @staticmethod
    def get_axes_coords(labels):
        coords = []
        use = False
        for i, c in enumerate(np.linspace(0, 1, len(labels) * 2 + 1)):
            if use:
                coords.append(c)
            use = not use
        return coords

    def get_expand(self):
        if self.is_flank:
            return 1. + self.text_pad, 1. + self.text_gap
        else:
            return 1. + self.text_gap, 1. + self.text_pad

    def silent_render(self, figure, expand=(1., 1.)):

        renderer = figure.canvas.get_renderer()
        ax = figure.add_axes([0, 0, 1, 1])
        params = self.get_text_params()

        locs = self.get_axes_coords(self.data)
        sizes = []
        for s, c in zip(self.data, locs):
            x, y = (0, c) if self.is_flank else (c, 0)
            t = ax.text(x, y, s=s, transform=ax.transAxes, **params.to_dict())
            bbox = t.get_window_extent(renderer).expanded(*expand)
            if self.is_flank:
                sizes.append(bbox.xmax - bbox.xmin)
            else:
                sizes.append(bbox.ymax - bbox.ymin)

        ax.remove()
        return np.max(sizes) / figure.get_dpi()

    def get_canvas_size(self, figure):
        self.texts_size = self.silent_render(figure, expand=self.get_expand())
        return self.texts_size + self.padding / 72


@dataclass
class AnnoTextConfig:
    va: str
    ha: str
    rotation: int
    relpos: tuple

    angleA: int
    angleB: int
    armA: int = 10
    armB: int = 10

    def get_connectionstyle(self, armA=None, armB=None):
        armA = self.armA if armA is None else armA
        armB = self.armB if armB is None else armB
        return f"arc,angleA={self.angleA}," \
               f"angleB={self.angleB}," \
               f"armA={armA}," \
               f"armB={armB}," \
               f"rad=0"


anno_default_params = {
    "top": AnnoTextConfig(va="bottom", ha="center", rotation=90,
                          angleA=-90, angleB=90,
                          relpos=(0.5, 0)),
    "bottom": AnnoTextConfig(va="top", ha="center", rotation=-90,
                             angleA=90, angleB=-90,
                             relpos=(0.5, 1)),
    "right": AnnoTextConfig(va="center", ha="left", rotation=0,
                            angleA=-180, angleB=0,
                            relpos=(0, 0.5)),
    "left": AnnoTextConfig(va="center", ha="right", rotation=0,
                           angleA=0, angleB=-180,
                           relpos=(1, 0.5)),
}


class AnnoLabels(_LabelBase):
    """Annotate a few rows or columns

    This is useful when your heatmap contains many rows/columns,
    and you only want to annotate a few of them.

    Parameters
    ----------
    labels : list, np.ma.MaskedArray
        The length of the labels should match the main canvas side where
        it attaches to, the labels that won't be displayed should be masked.
    mark : list
        If your labels is not a mask array, this will help you mark the labels
        that you want to draw
    side : str
    text_pad : float
        Add extra space and the start and end of the label
    text_gap : float
        Add extra spacing between the labels, relative to the fontsize
    pointer_size : float
        The size of the pointer in inches
    linewidth : float
        The linewidth of the pointer
    connectionstyle :
    relpos : 2-tuple
    armA, armB : float
    options :
        Pass to :class:`matplotlib.text.Text`


    Examples
    --------

    .. plot::
        :context: close-figs

        >>> labels = np.arange(100)

        >>> import marsilea as hg
        >>> from marsilea.plotter import AnnoLabels
        >>> matrix = np.random.randn(100, 10)
        >>> h = hg.Heatmap(matrix)
        >>> marks = AnnoLabels(labels, mark=[3, 4, 5])
        >>> h.add_right(marks)
        >>> h.render()

    """

    def __init__(self,
                 labels: Iterable | np.ma.MaskedArray,
                 mark=None,
                 text_pad=.5,
                 text_gap=.5, pointer_size=0.5,
                 linewidth=None, connectionstyle=None, relpos=None,
                 armA=None, armB=None,
                 **options):

        if not np.ma.isMaskedArray(labels):
            if mark is not None:
                labels = np.ma.masked_where(~np.in1d(labels, mark), labels)
            else:
                raise TypeError("Must be numpy masked array or "
                                "use `marks` to mark "
                                "the labels you want to draw")
        self.data = self.data_validator(labels, target="1d")

        self.pointer_size = pointer_size
        self.linewidth = linewidth
        self.text_anchor = 0.4
        self.text_gap = text_gap
        self.text_pad = text_pad
        self.armA = armA
        self.armB = armB
        self.relpos = relpos
        self.connectionstyle = connectionstyle

        super().__init__()
        self._sort_params(**options)

    def get_text_params(self):
        default_params = anno_default_params[self.side]
        self.relpos = default_params.relpos
        self.connectionstyle = (default_params
                                .get_connectionstyle(armA=self.armA,
                                                     armB=self.armB))
        params = dict(va=default_params.va, ha=default_params.ha,
                      rotation=default_params.rotation)
        p = TextParams(**params)
        p.update_params(self._user_params)
        return p

    def get_canvas_size(self, figure):
        expand = self.get_expand()
        canvas_size = self.silent_render(figure, expand)
        size = canvas_size + self.pointer_size
        self.text_anchor = self.pointer_size / size
        return size

    def render_ax(self, ax, labels):
        renderer = ax.get_figure().canvas.get_renderer()
        locs = self.get_axes_coords(labels)

        ax_bbox = ax.get_window_extent(renderer)
        params = self.get_text_params()

        text_options = dict(ax=ax, renderer=renderer,
                            expand=self.get_expand(),
                            linewidth=self.linewidth,
                            relpos=self.relpos,
                            connectionstyle=self.connectionstyle,
                            **params.to_dict())

        texts = []
        segments = []
        if self.is_body:
            y = self.text_anchor
            for x, s in zip(locs, labels):
                if not np.ma.is_masked(s):
                    t = AdjustableText(x=x, y=y, text=s, pointer=(x, 0),
                                       **text_options)
                    texts.append(t)
                    segments.append(t.get_segment_x())

            lim = Segment(ax_bbox.xmin, ax_bbox.xmax)
            adjust_segments(lim, segments)
            for t, s in zip(texts, segments):
                t.set_display_x(s.mid)
                t.draw_annotate()
        else:
            x = self.text_anchor
            for y, s in zip(locs, labels):
                if not np.ma.is_masked(s):
                    t = AdjustableText(x=x, y=y, text=s, pointer=(0, y),
                                       **text_options)
                    texts.append(t)
                    segments.append(t.get_segment_y())
            lim = Segment(ax_bbox.ymin, ax_bbox.ymax)
            adjust_segments(lim, segments)
            for t, s in zip(texts, segments):
                t.set_display_y(s.mid)
                t.draw_annotate()

        ax.set_axis_off()
        if self.side != "top":
            ax.invert_yaxis()
        if self.side == "left":
            ax.invert_xaxis()


label_default_params = {
    'right': dict(align='left', rotation=0),
    'left': dict(align='right', rotation=0),
    'top': dict(align='bottom', rotation=90),
    'bottom': dict(align='top', rotation=90)
}


class Labels(_LabelBase):
    """Add text labels

    Parameters
    ----------
    labels : array of str
    align : str
        Which side of the text to align
    padding : float
        The buffer space between text and the adjcent plots, in points unit
    options : dict
        Pass to :class:`matplotlib.text.Text`


    Examples
    --------

    .. plot::
        :context: close-figs

        >>> row = [str(i) for i in range(15)]
        >>> col = [str(i) for i in range(10)]

        >>> import marsilea as hg
        >>> from marsilea.plotter import Labels
        >>> matrix = np.random.randn(15, 10)
        >>> h = hg.Heatmap(matrix)
        >>> label_row = Labels(row)
        >>> label_col = Labels(col)
        >>> h.add_right(label_row)
        >>> h.add_bottom(label_col)
        >>> h.render()

    """

    def __init__(self, labels, align=None,
                 padding=2,
                 **options):
        self.data = self.data_validator(labels, target="1d")
        self.text_pad = 0
        self.text_gap = 0
        self.align = align
        self.padding = padding

        super().__init__()
        self._sort_params(**options)

    def _align_compact(self, align):
        """Make align keyword compatible to any side"""
        if self.is_flank:
            checker = {"top": "right", "bottom": "left"}
        else:
            checker = {"right": "top", "left": "bottom"}
        return checker.get(align, align)

    def get_text_params(self) -> TextParams:
        default_params = label_default_params[self.side]
        if self.align is None:
            self.align = default_params['align']

        self.align = self._align_compact(self.align)
        va, ha = self.align, 'center'
        if self.is_flank:
            va, ha = ha, va

        p = TextParams(va=va, ha=ha, rotation=default_params['rotation'])
        p.update_params(self._user_params)

        return p

    def render_ax(self, ax: Axes, data):
        coords = self.get_axes_coords(data)
        params = self.get_text_params()
        if self.texts_size is not None:
            offset_ratio = self.padding / 72 / self.texts_size
        else:
            offset_ratio = 0

        if self.is_flank:
            coords = coords[::-1]
        if self.align == "center":
            const = .5
        elif self.align in ["right", "top"]:
            const = 1 - offset_ratio / 2
        else:
            const = offset_ratio / 2  # self.text_pad / (1 + self.text_pad) / 2

        for s, c in zip(data, coords):
            x, y = (const, c) if self.is_flank else (c, const)
            ax.text(x, y, s=s, transform=ax.transAxes,
                    **params.to_dict())
        ax.set_axis_off()
        # from matplotlib.patches import Rectangle
        # ax.add_artist(Rectangle((0, 0), 1, 1, edgecolor="r",
        #                         transform=ax.transAxes))


stick_pos = {
    "right": 0,
    "left": 1,
    "top": 0,
    "bottom": 1,
}


class Title(_LabelBase):
    """Add a title

    Parameters
    ----------
    title : str
        The title text
    align : {'center', 'left', 'right', 'bottom', 'top'}
        Where the title is placed
    padding : float
        The buffer space between text and the adjcent plots, in points unit
    fontsize : int, default: 12
        The title font size
    rotation :
    options : dict
        Pass to :class:`matplotlib.text.Text`

    Examples
    --------

    .. plot::
        :context: close-figs

        >>> import marsilea as hg
        >>> from marsilea.plotter import Title
        >>> matrix = np.random.randn(15, 10)
        >>> h = hg.Heatmap(matrix)
        >>> title = Title('Heatmap')
        >>> h.add_top(title)
        >>> h.render()


    """
    no_split = True

    def __init__(self, title, align="center",
                 padding=10,
                 fontsize=None,
                 fill_color=None,
                 bordercolor=None,
                 borderwidth=None,
                 borderstyle=None,
                 **options):
        self.data = title
        self.align = align
        if fontsize is None:
            fontsize = 12
        self.fontsize = fontsize
        self.text_pad = 0
        self.text_gap = 0
        self.rotation = 0
        self.padding = padding
        self.fill_color = fill_color
        self.bordercolor = bordercolor
        self.borderwidth = borderwidth
        self.borderstyle = borderstyle
        self._draw_bg = (self.fill_color is not None) \
            or (self.bordercolor is not None)

        super().__init__()
        self._sort_params(**options)

    align_pos = {
        'right': 1,
        'left': 0,
        'top': 1,
        'bottom': 0,
        'center': 0.5
    }

    default_rotation = {
        'right': -90,
        'left': 90,
        'top': 0,
        'bottom': 0,
    }

    def _align_compact(self, align):
        """Make align keyword compatible to any side"""
        if self.is_flank:
            checker = {"left": "top", "right": "bottom"}
        else:
            checker = {"top": "left", "bottom": "right"}
        return checker.get(align, align)

    def get_text_params(self) -> TextParams:
        self.align = self._align_compact(self.align)
        va, ha = 'center', self.align
        if self.is_flank:
            va, ha = ha, va

        p = TextParams(rotation=self.default_rotation[self.side],
                       va=va, ha=ha)
        p.update_params(self._user_params)
        return p

    def get_render_data(self):
        return self.data

    def render_ax(self, ax: Axes, title):
        params = self.get_text_params()
        fontdict = params.to_dict()

        if self._draw_bg:
            bgcolor = "white" if self.fill_color is None else self.fill_color
            ax.add_artist(Rectangle((0, 0), 1, 1,
                                    facecolor=self.fill_color,
                                    edgecolor=self.bordercolor,
                                    linewidth=self.borderwidth,
                                    linestyle=self.borderstyle,
                                    transform=ax.transAxes
                                    ))

            lum = relative_luminance(bgcolor)
            text_color = ".15" if lum > .408 else "w"
            fontdict.setdefault('color', text_color)

        const = self.align_pos[self.align]

        pos = .5
        x, y = (const, pos) if self.is_body else (pos, const)
        ax.text(x, y, title, fontsize=self.fontsize,
                transform=ax.transAxes, **fontdict)
        ax.set_axis_off()


class Chunk(_LabelBase):
    """Mark splited chunks

    This is useful to mark each chunks after you split the plot

    Parameters
    ----------

    texts : array of str
        The label for each chunk
    fill_colors : color, array of color
        The color used as background color for each chunk
    borderwidth, bordercolor, borderstyle : 
        Control the style of border
        For borderstyle, see :meth:`linestyles <matplotlib.lines.Line2D.set_linestyle>`
    props : dict
        See :class:`matplotlib.text.Text`
    rotation : float
        How many to rotate the text
    padding : float
        The buffer space between text and the adjcent plots, in points unit

    Examples
    --------

    .. plot::
        :context: close-figs

        >>> import marsilea as hg
        >>> from marsilea.plotter import Chunk
        >>> matrix = np.random.randn(15, 10)
        >>> h = hg.Heatmap(matrix)
        >>> h.hsplit(cut=[4, 10])
        >>> h.vsplit(cut=[5])
        >>> chunk_row = Chunk(['Top','Middle','Bottom'],rotation=True)
        >>> chunk_col = Chunk(['Left','Right'],rotation=True)
        >>> h.add_right(chunk_row)
        >>> h.add_bottom(chunk_col)
        >>> h.render()
    
    """

    def __init__(self, texts,
                 fill_colors=None,
                 props=None, padding=2, bordercolor=None,
                 borderwidth=None, borderstyle=None,
                 **options):

        self.data = np.asarray(texts)
        self.padding = padding
        self.props = props if props is not None else {}
        if is_color_like(fill_colors):
            fill_colors = [fill_colors for _ in range(len(self.data))]
        if fill_colors is not None:
            fill_colors = np.asarray(fill_colors)
        self.fill_colors = fill_colors

        if is_color_like(bordercolor):
            bordercolor = [bordercolor for _ in range(len(self.data))]
        if bordercolor is not None:
            bordercolor = np.asarray(bordercolor)
        self.bordercolor = bordercolor
        self.borderwidth = borderwidth
        self.borderstyle = borderstyle
        self._draw_bg = (self.fill_colors is not None) \
            or (self.bordercolor is not None)
        self.text_pad = 0

        super().__init__()
        self._sort_params(**options)

    default_rotation = {
        "right": -90,
        "left": 90,
        "top": 0,
        "bottom": 0,
    }

    def get_text_params(self) -> TextParams:
        p = TextParams(va="center", ha="center",
                       rotation=self.default_rotation[self.side])
        p.update_params(self._user_params)
        p.update_params(self.props)
        return p

    def render(self, axes):

        params = self.get_text_params()

        text = self.data
        bg_colors = self.fill_colors
        border_colors = self.bordercolor
        if self.has_deform:
            if self.is_flank:
                reindex = self.deform.row_chunk_index
            else:
                reindex = self.deform.col_chunk_index
            if reindex is not None:
                text = text[reindex]
                if bg_colors is not None:
                    bg_colors = bg_colors[reindex]
                if border_colors is not None:
                    border_colors = border_colors[reindex]

        if isinstance(axes, Axes):
            axes = [axes]

        if len(axes) != len(self.data):
            raise ValueError(f"You have {len(axes)} axes "
                             f"but you only provide {len(self.data)} texts.")

        for i, ax in enumerate(axes):
            ax.set_axis_off()
            fontdict = params.to_dict()
            if self._draw_bg:
                bgcolor = "white"
                border_color = None
                if bg_colors is not None:
                    bgcolor = bg_colors[i]
                if border_colors is not None:
                    border_color = border_colors[i]
                rect = Rectangle((0, 0), 1, 1,
                                 facecolor=bgcolor,
                                 edgecolor=border_color,
                                 linewidth=self.borderwidth,
                                 linestyle=self.borderstyle,
                                 transform=ax.transAxes)
                ax.add_artist(rect)

                lum = relative_luminance(bgcolor)
                text_color = ".15" if lum > .408 else "w"
                fontdict.setdefault('color', text_color)

            ax.text(0.5, 0.5, text[i], fontdict=fontdict,
                    transform=ax.transAxes)
