class DuplicateName(Exception):

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return f"Axes with name `{self.name}` already exists."


class SplitTwice(Exception):

    def __init__(self, axis="col"):
        self.axis = axis

    def __str__(self):
        return f"Split {self.axis} more than once is ambiguous."


class SplitConflict(Exception):
    pass


class AppendLayoutError(Exception):

    def __str__(self):
        return "Append a concatenated plot is not allowed," \
               "you can only append " \
               "plots to a concatenated plot."


class DataError(Exception):
    pass
