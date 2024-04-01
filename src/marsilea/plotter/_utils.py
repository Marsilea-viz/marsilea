import numpy as np


def _format_labels(labels, fmt):
    f_labels = []
    for a in labels:
        label = _format_label(a, fmt)
        f_labels.append(label)
    return f_labels


def _format_label(a, fmt):
    if np.isnan(a):
        a = ""
    if isinstance(fmt, str):
        label = _auto_format_str(fmt, a)
    elif callable(fmt):
        label = fmt(a)
    else:
        raise TypeError("fmt must be a str or callable")
    return label


def _auto_format_str(fmt, value):
    """Format a value according to the given format string.
    matplotlib/cbook.py
    """
    try:
        return fmt % (value,)
    except (TypeError, ValueError):
        return fmt.format(value)
