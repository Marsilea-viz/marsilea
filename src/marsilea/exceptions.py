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
            f"The `{name}` added"
            f"to the `{self.plotter.side}` has been registered,"
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
    def __init__(self, plot, existing):
        self.plot = plot
        self.existing = existing

    def __str__(self):
        name = self.plot.__class__.__name__
        other = self.existing.__class__.__name__
        return (
            f"`{name}` and `{other}` cannot share the main canvas. "
            f"A seaborn plot scales its axes to the data values, a mesh to the "
            f"grid of cells, so the categories end up offset by half a cell and "
            f"the mesh loses its value axis. "
            f"Add `{name}` to a side instead, with `add_top`, `add_bottom`, "
            f"`add_left` or `add_right`, or give it a main canvas of its own."
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
