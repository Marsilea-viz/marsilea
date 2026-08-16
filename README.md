<p align="center">
  <picture align="center">
    <source media="(prefers-color-scheme: dark)" srcset="https://github.com/Marsilea-viz/marsilea/raw/main/img/banner-dark.jpg">
    <source media="(prefers-color-scheme: light)" srcset="https://github.com/Marsilea-viz/marsilea/raw/main/img/banner-blue.jpg">
    <img alt="Marsilea: declarative creation of composable visualization" src="https://github.com/Marsilea-viz/marsilea/raw/main/img/banner-dark.jpg" width="400">
  </picture>
</p>

[![Documentation Status](https://readthedocs.org/projects/marsilea/badge/?version=stable&style=flat-square)](https://marsilea.readthedocs.io/en/stable)
![pypi version](https://img.shields.io/pypi/v/marsilea?color=0098FF&logo=python&logoColor=white&style=flat-square)
![Conda Version](https://img.shields.io/conda/vn/conda-forge/marsilea?style=flat-square&logo=anaconda&logoColor=white&color=%2344A833)
![PyPI - License](https://img.shields.io/pypi/l/marsilea?color=FFD43B&style=flat-square)
[![DOI](https://img.shields.io/badge/DOI-10.1186%2Fs13059--024--03469--3-blue?color=0098FF&style=flat-square)](https://doi.org/10.1186/s13059-024-03469-3)

[Documentation](https://marsilea.readthedocs.io/en/stable/) |
[Tutorials](https://marsilea.readthedocs.io/en/stable/tutorial/index.html) |
[Gallery](https://marsilea.readthedocs.io/en/stable/examples/index.html) |
[llms.txt](https://marsilea.readthedocs.io/llms.txt) |
[Genome Biology](https://doi.org/10.1186/s13059-024-03469-3)

# Marsilea: Declarative creation of composable visualization

Marsilea builds **complex annotated heatmaps**, **oncoprints**, **UpSet plots**, **sequence
logos** and other composable visualizations in Python — declaratively, on top of Matplotlib.

## Quickstart (8 lines)

<table>
<tr>
<td width="55%" valign="top">

```python
import numpy as np
import marsilea as ma
import marsilea.plotter as mp

data = np.random.default_rng(0).standard_normal((10, 10))

h = ma.Heatmap(data, linewidth=0.5, height=4, width=4)
h.add_top(mp.Bar(data.mean(axis=0)), size=0.8, pad=0.1)
h.add_left(mp.Labels([f"Gene{i}" for i in range(10)]), pad=0.05)
h.add_dendrogram("right")
h.add_legends()
h.render()
```

</td>
<td width="45%" valign="top">
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://github.com/Marsilea-viz/marsilea/raw/main/img/quickstart-dark.png">
  <img alt="Heatmap with a bar chart on top, gene labels on the left, a dendrogram on the right and a colorbar" src="https://github.com/Marsilea-viz/marsilea/raw/main/img/quickstart.png">
</picture>
</td>
</tr>
</table>

Add a bar chart on top, labels on the left, a dendrogram on the right. Each side
is just another building block. [→ Full tutorial](https://marsilea.readthedocs.io/en/stable/tutorial/index.html)

> **Using scanpy/scverse?** Marsilea has an official how-to in the scanpy documentation:
> [Plotting with Marsilea](https://scanpy.scverse.org/en/stable/how-to/plotting-with-marsilea.html)

## Installation

PyPI
```shell
pip install marsilea
```
Conda
```shell
conda install -c conda-forge marsilea
```

## Use with Claude Code

Marsilea ships an official [Claude Code](https://claude.com/claude-code) skill:

```shell
/plugin marketplace add Marsilea-viz/marsilea-skill
/plugin install marsilea@marsilea-marketplace
```

Once installed, the skill activates automatically whenever you ask Claude for a
composable visualization. Marsilea itself still needs to be installed in your
Python environment (see above). See the
[marsilea-skill](https://github.com/Marsilea-viz/marsilea-skill) repository, or
[Use Marsilea with AI assistants](https://marsilea.readthedocs.io/en/stable/ai_assistants.html)
for other assistants and the machine-readable
[llms.txt](https://marsilea.readthedocs.io/llms.txt).

## What is Composable Visualization?

<p align="center">
  <picture align="center">
    <img alt="Animation of a heatmap gaining side plots one call at a time" src="https://github.com/Marsilea-viz/marsilea/raw/main/img/showcase.gif" width="300">
  </picture>
</p>

When we do visualization, we often need to combine multiple plots to show different aspects of the data.
For example, we may need to create a heatmap to show the expression of genes in different cells,
and then create a bar chart to show the expression of genes in different cell types.
A visualization contains multiple plots is called a composable visualization.
In Marsilea, we employ a declarative approach for user to create composable visualization incrementally.

## Examples

<table>
    <thead>
        <tr>
            <th>
                <a href="https://marsilea.readthedocs.io/en/stable/examples/Gallery/plot_tiobe_index.html">
                    Bar chart with images
                </a>
            </th>
            <th>
                <a href="https://marsilea.readthedocs.io/en/stable/examples/Gallery/plot_oil_well.html">
                    Stacked bar chart
                </a>
            </th>
            <th>
                <a href="https://marsilea.readthedocs.io/en/stable/examples/Gallery/plot_arc_diagram.html">
                    Arc diagram
                </a>
            </th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>
                <img alt="Bar chart of programming language ratings with language logos as labels" src="https://marsilea.readthedocs.io/en/stable/_images/sphx_glr_plot_tiobe_index_001_2_00x.png" height="300px">
            </td>
            <td>
                <img alt="Cross-layout stacked bar chart of fat content in cooking oils" src="https://marsilea.readthedocs.io/en/stable/_images/sphx_glr_plot_oil_well_001_2_00x.png" height="300px">
            </td>
            <td>
                <img alt="Arc diagram of the Les Misérables character network" src="https://marsilea.readthedocs.io/en/stable/_images/sphx_glr_plot_arc_diagram_001_2_00x.png" width="300px">
            </td>
        </tr>
    </tbody>
</table>

<table>
    <thead>
        <tr>
            <th>
                <a href="https://marsilea.readthedocs.io/en/stable/examples/Gallery/plot_pbmc3k.html">
                    Single-cell RNA-seq heatmap
                </a>
            </th>
            <th>
                <a href="https://marsilea.readthedocs.io/en/stable/examples/Gallery/plot_oncoprint.html">
                    Oncoprint
                </a>
            </th>
            <th>
                <a href="https://marsilea.readthedocs.io/en/stable/examples/Gallery/plot_upset.html">
                    UpSet plot
                </a>
            </th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>
                <img alt="Annotated heatmap of marker gene expression across PBMC 3k cell types" src="https://marsilea.readthedocs.io/en/stable/_images/sphx_glr_plot_pbmc3k_001_2_00x.png" width="300px">
            </td>
            <td>
                <img alt="Oncoprint of breast cancer mutations across samples and genes" src="https://marsilea.readthedocs.io/en/stable/_images/sphx_glr_plot_oncoprint_005_2_00x.png" width="300px">
            </td>
            <td>
                <img alt="UpSet plot of genre intersections in the IMDB top 1000 movies" src="https://marsilea.readthedocs.io/en/stable/_images/sphx_glr_plot_upset_001_2_00x.png" width="300px">
            </td>
        </tr>
    </tbody>
</table>

[More examples →](https://marsilea.readthedocs.io/en/stable/examples/index.html)

## Citation

If you use Marsilea in your research, please cite the following:

> Marsilea: an intuitive generalized paradigm for composable visualizations
> 
> Yimin Zheng, Zhihang Zheng, André F. Rendeiro & Edwin Cheung
> 
> _Genome Biology_ 2025 Jan 06. DOI: [10.1186/s13059-024-03469-3](https://doi.org/10.1186/s13059-024-03469-3)

## Getting help

Found a bug or have a question? [Open an issue](https://github.com/Marsilea-viz/marsilea/issues).
