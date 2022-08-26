"""
Utilities functions to check user input
"""


def check_in_list(options, **kwargs):
    for name, value in kwargs.items():
        if value not in options:
            raise ValueError(f"You input unknown {name}={value}, "
                             f"options are {options}")
