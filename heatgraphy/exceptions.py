class SplitTwice(Exception):

    def __init__(self, axis="col"):
        self.axis = axis

    def __str__(self):
        return f"Split {self.axis} more than once is not allowed."

