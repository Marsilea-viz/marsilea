:html_theme.sidebar_secondary.remove:

API Reference
#############


Declarative API Cheat Sheet
===========================

.. list-table::
    :header-rows: 1

    * - Operator
      - Description
      - Example

    * - :meth:`~marsilea.base.WhiteBoard.add_layer`
      - Add a plotter to main canvas.
      - .. code-block:: python

            wb.add_layer(ColorMesh(data))

    * - :meth:`~marsilea.base.WhiteBoard.add_left`
      - Add to the **left-side** of main canvas.
      - .. code-block:: python

            wb.add_left(Numbers(data),
                        size=1, pad=.1,
                        name='left-plot')

    * - :meth:`~marsilea.base.WhiteBoard.add_right`
      - Add a plotter to the **right-side** of main canvas.
      - .. code-block:: python

            wb.add_right(Numbers(data))

    * - :meth:`~marsilea.base.WhiteBoard.add_top`
      - Add a plotter to the **top-side** of main canvas.
      - .. code-block:: python

            wb.add_top(Numbers(data))

    * - :meth:`~marsilea.base.WhiteBoard.add_bottom`
      - Add a plotter to the **bottom-side** of main canvas.
      - .. code-block:: python

            wb.add_bottom(Numbers(data))

    * - :meth:`~marsilea.base.WhiteBoard.add_title`
      - Add titles to the plot.
      - .. code-block:: python

            wb.add_title(top='Top Title', bottom='Bottom Title'
                         left='Left Title', right='Right Title')

    * - :meth:`~marsilea.base.ClusterBoard.add_dendrogram`
      - Add a dendrogram to the plot, only available to ClusterBoard.
      - .. code-block:: python

            cb.add_dendrogram("left", data)

    * - :meth:`~marsilea.base.ClusterBoard.group_cols`
      - Split the main canvas horizontally, only available to ClusterBoard.
      - .. code-block:: python

            cb.group_cols(labels=[1, 1, 2, 2], order=[2, 1])

    * - :meth:`~marsilea.base.ClusterBoard.group_rows`
      - Split the main canvas vertically, only available to ClusterBoard.
      - .. code-block:: python

            cb.group_rows(labels=[1, 1, 2, 2], order=[2, 1])

    * - :meth:`~marsilea.base.ClusterBoard.cut_cols`
      - Split the main canvas horizontally, only available to ClusterBoard.
      - .. code-block:: python

            cb.cut_cols([5])

    * - :meth:`~marsilea.base.ClusterBoard.cut_rows`
      - Split the main canvas vertically, only available to ClusterBoard.
      - .. code-block:: python

            cb.cut_rows([5])

    * - :meth:`~marsilea.base.LegendMaker.add_legends`
      - Add legends to the plots.
      - .. code-block:: python

            wb.add_legends()

    * - :meth:`~marsilea.base.WhiteBoard.add_canvas`
      - Add a plotter to a chosen side of main plot.
      - .. code-block:: python

            wb.add_canvas("right", Numbers(data))

    * - :meth:`~marsilea.base.WhiteBoard.add_pad`
      - Add white space between plot.
      - .. code-block:: python

            wb.add_pad("right", 1)

    * - :meth:`~marsilea.base.WhiteBoard.set_margin`
      - Add white space surrounding the figure.
      - .. code-block:: python

            wb.set_margin(1)

    * - :meth:`~marsilea.base.WhiteBoard.render`
      - Render the plot.
      - .. code-block:: python

            wb.render()

    * - :meth:`~marsilea.base.WhiteBoard.save`
      - Save the plot to a file.
      - .. code-block:: python

            wb.save("output.png", dpi=300)

    * - :code:`+`
      - Two canvas side by side, number will be added as white space
      - .. code-block:: python

            (wb1 + 1 + wb2).render()

    * - :code:`/`
      - Two canvas top and bottom, number will be added as white space
      - .. code-block:: python

            (wb1 / 1 / wb2).render()


High-Level Visualizations
=========================

Heatmap Variants
----------------

.. currentmodule:: marsilea
.. autosummary::
    :toctree: APIs/
    :template: autosummary.rst
    :nosignatures:

    Heatmap
    SizedHeatmap
    CatHeatmap

Layers Heatmap
--------------

.. currentmodule:: marsilea.layers
.. autosummary::
    :toctree: APIs/
    :template: autosummary.rst
    :nosignatures:

    Layers
    LayersMesh

UpSet plots
-----------

.. currentmodule:: marsilea.upset
.. autosummary::
    :toctree: APIs/
    :template: autosummary.rst
    :nosignatures:

    Upset
    UpsetData


OncoPrint
---------

.. currentmodule:: oncoprinter
.. autosummary::
    :toctree: APIs/
    :template: autosummary.rst
    :nosignatures:

    OncoPrint


Plotters
========

.. currentmodule:: marsilea.plotter

Mesh
----

.. autosummary::
    :toctree: APIs/
    :template: autosummary.rst
    :nosignatures:

    ColorMesh
    Colors
    SizedMesh
    MarkerMesh
    TextMesh

Seaborn plots
-------------

.. autosummary::
    :toctree: APIs/
    :template: autosummary.rst
    :nosignatures:

    Bar
    Box
    Boxen
    Violin
    Point
    Strip
    Swarm

Other plots
-----------

.. autosummary::
    :toctree: APIs/
    :template: autosummary.rst
    :nosignatures:

    Area
    Arc
    Numbers
    StackBar
    CenterBar
    SeqLogo
    Image
    Emoji


Text Label
----------

.. autosummary::
    :toctree: APIs/
    :template: autosummary.rst
    :nosignatures:

    Labels
    AnnoLabels
    Title
    Chunk
    FixedChunk



Main Canvas
===========


.. currentmodule:: marsilea.base
.. autosummary::
    :toctree: APIs/
    :template: autosummary.rst
    :nosignatures:

    WhiteBoard
    ClusterBoard
    LegendMaker
    ZeroWidth
    ZeroHeight
    ZeroWidthCluster
    ZeroHeightCluster

Layout Engine
=============

.. currentmodule:: marsilea.layout
.. autosummary::
    :toctree: APIs/
    :template: autosummary.rst
    :nosignatures:

    CrossLayout
    CompositeCrossLayout


Data Manipulation
=================

.. currentmodule:: marsilea
.. autosummary::
    :toctree: APIs/
    :template: autosummary.rst
    :nosignatures:

    Deformation

Render plan
===========

.. currentmodule:: marsilea.plotter.base
.. autosummary::
    :toctree: APIs/
    :template: autosummary.rst
    :nosignatures:

    RenderPlan
    RenderSpec

