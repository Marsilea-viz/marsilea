import warnings

import numpy as np
import pandas as pd
import seaborn
from legendkit import CatLegend
from seaborn import color_palette
from typing import Mapping, Sequence

from ._stats_annot import (
    POSITION_KWS,
    SUPPORTED_PLOTS,
    DrawnChunk,
    StatsConfig,
    annotate,
    cross_annotations,
    draw_cross_brackets,
    load_annotator,
    plan_pairs,
)
from .base import StatsBase
from ..utils import ECHARTS16


def _extract_names(data):
    """The column labels of the wide input, if it carries any."""
    if isinstance(data, Mapping):
        data = next(iter(data.values()), None)
    columns = getattr(data, "columns", None)
    return None if columns is None else np.asarray(columns)


class _SeabornBase(StatsBase):
    _seaborn_plot = None
    datasets = None
    hue = None
    data = None
    _stats = None

    def __init__(
        self,
        data,
        hue_order=None,
        palette=None,
        orient=None,
        legend_kws=None,
        group_kws=None,
        label=None,
        label_loc=None,
        label_props=None,
        **kwargs,
    ):
        self._var_names = _extract_names(data)
        if isinstance(data, Mapping):
            datasets = []
            self.hue = []
            if hue_order is None:
                hue_order = data.keys()
            for name in hue_order:
                self.hue.append(name)
                datasets.append(self.data_validator(data[name]))
            if isinstance(palette, Mapping):
                self.palette = palette
            else:
                if palette is None:
                    colors = ECHARTS16
                else:
                    colors = color_palette(palette, as_cmap=False)
                self.palette = dict(zip(self.hue, colors))
            kwargs["palette"] = self.palette
            self.set_data(*datasets)
        else:
            data = self.data_validator(data)
            self.set_data(data)
            # kwargs.setdefault('color', 'C0')
            # if (palette is None) and ('color' not in kwargs):
            #     kwargs['palette'] = "dark:C0"
            if palette is not None:
                kwargs["palette"] = palette
                if isinstance(palette, Sequence):
                    self.set_params({"palette": palette})

        kwargs.pop("x", None)
        kwargs.pop("y", None)
        kwargs.pop("hue", None)
        # kwargs.pop("orient", None)
        kwargs.pop("ax", None)
        self.kws = kwargs

        self.orient = orient
        self.set_label(label, label_loc, label_props)
        self.legend_kws = {} if legend_kws is None else legend_kws
        if group_kws is not None:
            self.set_group_params(group_kws)

    def get_legends(self):
        if self.hue is not None:
            labels = []
            colors = []
            for label, color in self.palette.items():
                labels.append(label)
                colors.append(color)
            options = dict(handle="square", size=1, draw=False)
            options.update(self.legend_kws)
            return CatLegend(colors=colors, labels=labels, **options)

    def render_ax(self, spec):
        ax = spec.ax
        data = spec.data
        gp = spec.group_params

        if gp is None:
            gp = {}
        x, y = "var", "value"
        if self.hue is not None:
            dfs = []
            for d, hue in zip(data, self.hue):
                df = pd.DataFrame(d)
                df = df.melt(var_name="var", value_name="value")
                df["hue"] = hue
                dfs.append(df)

            pdata = pd.concat(dfs).reset_index(drop=True)
            self.kws["hue"] = "hue"
            self.kws["hue_order"] = self.hue
            if self.get_orient() == "h":
                x, y = y, x
            self.kws["x"] = x
            self.kws["y"] = y
            options = {**self.kws, **gp}

        else:
            pdata = pd.DataFrame(data).melt(var_name="var", value_name="value")
            if self.get_orient() == "h":
                x, y = y, x
            self.kws["x"] = x
            self.kws["y"] = y
            if spec.params is not None:
                palette = [p.get("palette", "C0") for p in spec.params]
                self.kws["palette"] = palette
            options = {**self.kws, **gp}
            if options.get("palette") is not None:
                options["hue"] = "var"

        orient = self.get_orient()
        if self.side == "left":
            if not ax.xaxis_inverted():
                ax.invert_xaxis()
        # barplot(data=data, orient=orient, ax=ax, **self.kws)
        plotter = getattr(seaborn, self._seaborn_plot)
        plotter(data=pdata, orient=orient, ax=ax, **options)
        ax.set(xlabel=None, ylabel=None)
        leg = ax.get_legend()
        if leg is not None:
            leg.remove()
        self._align_cat_axis(ax, data, orient)

        if self._stats is not None:
            names = self._chunk_names
            self._chunks.append(
                DrawnChunk(
                    ax=ax,
                    pdata=pdata,
                    x=x,
                    y=y,
                    # A per-column palette also sets hue, but on the category
                    # itself; statannotations only needs the real hue levels.
                    hue="hue" if self.hue is not None else None,
                    hue_order=self.hue,
                    orient=orient,
                    names=names[spec.current_ix] if self.is_split else names,
                )
            )

    def annotate_stats(
        self, pairs, test="Mann-Whitney", ref=None, pvalues=None, **configure_kws
    ):
        """Test pairs of categories and draw the result on the plot.

        Requires `statannotations <https://github.com/trevismd/statannotations>`_,
        installed with :code:`pip install marsilea[stats]`.

        Categories are named with the columns of the input data; when the input
        is a plain array they are named by position (0, 1, 2, ...). When the
        canvas is split, a pair whose two members land in different groups is
        bracketed across their axes, above the within-group brackets it passes
        over.

        Parameters
        ----------
        pairs : list of pairs, "hue" or "all"
            In an explicit list, each side of a pair is a category label,
            :code:`("A", "B")`, or a :code:`(category, hue_level)` tuple when
            the data has hue, :code:`(("A", "WT"), ("A", "KO"))`.
            :code:`"hue"` compares the hue levels inside every category;
            :code:`"all"` compares the categories with each other, staying
            inside each group when the canvas is split.
        test : str, default: "Mann-Whitney"
            The statistical test, see
            :meth:`statannotations.Annotator.Annotator.configure`. Ignored when
            *pvalues* is given.
        ref : str, optional
            Reduce a shorthand to comparisons against one reference: a hue level
            for :code:`pairs="hue"`, a category label for :code:`pairs="all"`.
            A category reference reaches into every group, not just its own.
        pvalues : array, optional
            Skip testing and annotate these p-values instead, one per pair, in
            the order the pairs were listed. Needs an explicit *pairs* list.
        configure_kws :
            Passed to :meth:`statannotations.Annotator.Annotator.configure`,
            e.g. :code:`text_format`, :code:`loc`, :code:`comparisons_correction`
            (the corrections need :code:`statsmodels`).

        Returns
        -------
        self

        Examples
        --------
        .. code-block:: python

            >>> import marsilea as ma
            >>> import marsilea.plotter as mp
            >>> box = mp.Box({"WT": wt, "KO": ko})  # doctest: +SKIP
            >>> box.annotate_stats(  # doctest: +SKIP
            ...     pairs="hue", test="Mann-Whitney", text_format="star"
            ... )
            >>> h = ma.Heatmap(data)  # doctest: +SKIP
            >>> h.add_top(box, size=2)  # doctest: +SKIP
            >>> h.render()  # doctest: +SKIP

        """
        if self._seaborn_plot not in SUPPORTED_PLOTS:
            supported = ", ".join(sorted(SUPPORTED_PLOTS))
            raise ValueError(
                f"statannotations cannot annotate {self._seaborn_plot}, "
                f"only {supported}."
            )
        load_annotator()  # fail here rather than at render time

        names = self._var_names
        if names is not None and len(np.unique(names)) != len(names):
            raise ValueError(
                f"{self.__class__.__name__} cannot annotate data with duplicated "
                "column labels, pairs would be ambiguous."
            )
        if (ref is not None) and not isinstance(pairs, str):
            raise ValueError("ref only applies to pairs='hue' or pairs='all'")
        if (pvalues is not None) and isinstance(pairs, str):
            raise ValueError(
                "pvalues needs an explicit list of pairs, so each value has a "
                "pair to belong to"
            )

        moved = [k for k in POSITION_KWS if k in self.kws]
        if moved:
            warnings.warn(
                f"statannotations places brackets at seaborn's default category "
                f"positions and ignores {', '.join(moved)}; the annotation may "
                f"not line up with the plot.",
                stacklevel=2,
            )

        self._stats = StatsConfig(
            pairs=pairs,
            ref=ref,
            test=test,
            pvalues=pvalues,
            configure_kws=configure_kws,
        )
        return self

    def _deform_names(self):
        """Chunk and reorder the category labels the same way as the data."""
        names = self._var_names
        if names is None:
            names = np.arange(self.get_data()[0].shape[1])
        deform_func = self.get_deform_func()
        return names if deform_func is None else deform_func(names)

    def _draw_stats(self, axes):
        chunk_names = [chunk.names for chunk in self._chunks]
        per_chunk, cross, unknown = plan_pairs(self._stats, chunk_names, self.hue)

        for chunk, plan in zip(self._chunks, per_chunk):
            if plan.pairs:
                annotate(chunk, plan, self._seaborn_plot, self._stats)

        if cross:
            # A cross-group bracket has to clear every within-group one it
            # passes over, so unify the chunks before measuring where to put it.
            self.align_lim(axes)
            texts = cross_annotations(cross, self._chunks, self._stats)
            draw_cross_brackets(
                axes[0].figure, axes, cross, texts, self.get_orient(), self.hue
            )

        if unknown:
            warnings.warn(
                f"{len(unknown)} pair(s) name a category that is not in the data "
                f"and were skipped: {sorted(unknown, key=str)}",
                stacklevel=4,
            )

    def render(self, axes):
        self._chunks = []
        if self._stats is not None:
            self._chunk_names = self._deform_names()
        super().render(axes)
        if self._stats is not None:
            self._draw_stats(axes if self.is_split else [axes])
            if self.is_split:
                # Brackets grew the value axis; unify the chunks again.
                self.align_lim(axes)

    def _align_cat_axis(self, ax, data, orient):
        """Pin the categorical axis so the plot stays aligned with other plots.

        Seaborn infers the categorical span from the tick count instead of the data,
        and sets the limits with ``auto=None``, which leaves matplotlib autoscaling
        enabled. Any later autoscale then snaps the axis to the artists' extent plus
        margins, breaking the alignment. Take the span from the data instead;
        ``set_xlim``/``set_ylim`` also turn autoscaling off.
        """
        # data is (n_observations, n_categories), one array per hue level
        first = data[0] if self.hue is not None else data
        n = np.asarray(first).shape[1]
        if orient == "v":
            ax.set_xlim(-0.5, n - 0.5)
        else:
            # A horizontal plot runs top-to-bottom, like the rows of the main
            # canvas, so the categorical axis is inverted. Set it rather than
            # inherit it: seaborn skips its own adjustment under native_scale,
            # which would leave the categories upside down.
            ax.set_ylim(n - 0.5, -0.5)


def _seaborn_doc(obj: _SeabornBase):
    cls_name = obj.__name__

    sdata = "np.random.rand(10, 10)"
    hue_data = "{'a': sdata, 'b': sdata}"
    kws = "color='#DB4D6D'"
    h_kws = "group_kws={'color': colors}"

    if cls_name == "Swarm":
        sdata = "np.random.rand(50, 10)"
        kws = "color='#DB4D6D', size=2, dodge=True"
        h_kws = "group_kws={'color': colors}, size=2"

    elif cls_name == "Strip":
        sdata = "np.random.rand(50, 10)"
        kws = "color='#DB4D6D', size=2, dodge=True"
        h_kws = "group_kws={'color': colors}, size=2"

    elif cls_name == "Point":
        hue_data = "{'a': sdata, 'b': sdata * 2}"

    base_doc = f"""Wrapper for seaborn's {obj._seaborn_plot}
    
    .. note::
        .. rubric:: About data format
        
        You can only use wide-format for this plot, the number of columns
        of your input data should match your main data, this allow the data
        to be split and reorder if split and cluster is applied.
        
    
    Parameters
    ----------
    data : np.ndarray, pd.DataFrame
        The wide-format data. To input 'hue' like data, 
        you need to input a dict.
        eg: :code:`{{'hue1': data1, 'hue2': data2}}`.
    hue_order : array of str
        The order of hue
    palette : dict of label, color
    label : str
        The label of your data
    legend_kws : dict
        Configurations for legend
    group_kws : dict
        Configurations that apply to each group, should be something like
        :code:`{{'colors': ['C0', 'C1', 'C2']}}` if you have three groups.
    kwargs : 
        See :func:`seaborn.{obj._seaborn_plot}`
        
    Examples
    --------
    
    To render seaborn plots as side plots
    
    .. plot::
        :context: close-figs
        
        >>> import marsilea as ma
        >>> from marsilea.plotter import {cls_name}
        >>> data = np.random.randn(10, 10)
        >>> sdata = {sdata}
        >>> plot = {cls_name}(sdata, {kws})
        >>> h = ma.Heatmap(data)
        >>> h.cut_rows(cut=[3, 7])
        >>> h.add_right(plot)
        >>> h.render()
    """

    extend_examples = f"""
    It's possible to add hue data
    
    .. plot::
        :context: close-figs
        
        >>> plot = {cls_name}({hue_data}, {kws})
        >>> h = ma.Heatmap(data)
        >>> h.cut_rows(cut=[3, 7])
        >>> h.add_right(plot)
        >>> h.render()
        
    You can also draw it on the main canvas
    
    .. plot::
        :context: close-figs
        
        >>> plot = {cls_name}(sdata, {kws})
        >>> colors = ['#66327C', '#FFB11B', '#A8D8B9']
        >>> anno = ma.plotter.Chunk(['C1', 'C2', 'C3'], colors, padding=10)
        >>> cb = ma.ClusterBoard(data, height=2, margin=.5)
        >>> cb.add_layer(plot)
        >>> cb.cut_cols([3, 7])
        >>> cb.add_bottom(anno)
        >>> cb.render()
        
    To layout in a different orient and style each group
    
    .. plot::
        :context: close-figs
        
        >>> plot = {cls_name}(sdata, orient='h',
        ...                   {h_kws})
        >>> anno = ma.plotter.Chunk(['C1', 'C2', 'C3'], colors, padding=10)
        >>> cb = ma.ClusterBoard(data.T, width=2)
        >>> cb.add_layer(plot)
        >>> cb.cut_rows([3, 7])
        >>> cb.add_left(anno)
        >>> cb.render()

    """

    # Not executed: statannotations is an optional extra, and the docs must
    # build without it.
    stats_doc = f"""
    Significance can be tested and drawn on the plot with
    :meth:`annotate_stats`, which needs :code:`pip install marsilea[stats]`

    .. code-block:: python

        >>> plot = {cls_name}({hue_data}, {kws})
        >>> plot.annotate_stats(pairs='hue', text_format='star')
        >>> h = ma.Heatmap(data)
        >>> h.add_right(plot)
        >>> h.render()

    """
    if cls_name == "Count":
        obj.__doc__ = base_doc
    else:
        obj.__doc__ = base_doc + extend_examples
        if obj._seaborn_plot in SUPPORTED_PLOTS:
            obj.__doc__ += stats_doc
    return obj


@_seaborn_doc
class Bar(_SeabornBase):
    _seaborn_plot = "barplot"


@_seaborn_doc
class Box(_SeabornBase):
    _seaborn_plot = "boxplot"


@_seaborn_doc
class Boxen(_SeabornBase):
    _seaborn_plot = "boxenplot"


@_seaborn_doc
class Violin(_SeabornBase):
    _seaborn_plot = "violinplot"


@_seaborn_doc
class Point(_SeabornBase):
    _seaborn_plot = "pointplot"


# @_seaborn_doc
# class Count(_SeabornBase):
#     _seaborn_plot = "countplot"


@_seaborn_doc
class Strip(_SeabornBase):
    _seaborn_plot = "stripplot"


@_seaborn_doc
class Swarm(_SeabornBase):
    _seaborn_plot = "swarmplot"
