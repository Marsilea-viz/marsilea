class DuplicateName(Exception):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return f"Axes with name `{self.name}` already exists."


class DuplicatePlotter(Exception):
    def __init__(self, plotter):
        self.plotter = plotter

    def __str__(self):
        name = self.plotter.__class__.__name__
        return (
            f"The `{name}` added "
            f"to the `{self.plotter.side}` has been registered, "
            f"please create a new `{name}` if you want to add the same plotter again."
        )


class SplitTwice(Exception):
    def __init__(self, axis="col"):
        self.axis = axis

    def __str__(self):
        return f"Split {self.axis} more than once is ambiguous."


class SplitConflict(Exception):
    pass


class LayerConflict(Exception):
    def __init__(self, seaborn_plot, mesh_plot):
        self.seaborn_plot = seaborn_plot
        self.mesh_plot = mesh_plot

    def __str__(self):
        name = self.seaborn_plot.__class__.__name__
        mesh = self.mesh_plot.__class__.__name__
        return (
            f"`{name}` and `{mesh}` cannot share the main canvas. "
            f"`{name}` scales the Axes to the data values while `{mesh}` draws "
            f"a grid of cells, so whichever renders last leaves the other "
            f"misplaced: the categories shift by half a cell, and the cell grid "
            f"loses the axis it is drawn on. "
            f"Move `{name}` to a side with `add_top`, `add_bottom`, `add_left` "
            f"or `add_right`, or give it a main canvas of its own."
        )


class AppendLayoutError(Exception):
    def __str__(self):
        return (
            "Append a concatenated plot is not allowed,"
            "you can only append "
            "plots to a concatenated plot."
        )


class DataError(Exception):
    pass


class PerformanceWarning(UserWarning):
    pass
