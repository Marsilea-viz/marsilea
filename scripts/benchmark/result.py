import tokenize
from pathlib import Path

import pandas as pd
import mpl_fontkit as fk
from scipy.stats import entropy


# Calculate the number of tokens in the given file
def count_tokens(file_path):
    with open(file_path, "rb") as f:
        tokens = tokenize.tokenize(f.readline)
        return sum(1 for _ in tokens)


# Calculate the number of lines of code in the given file
def count_loc(file_path):
    """
    Counts the number of lines of actual code in a Python file, ignoring blank lines and comments.

    :param file_path: The path to the Python file to be analyzed.
    :return: The number of lines of code.
    """
    lines_of_code = 0
    try:
        with open(file_path, "r") as file:
            for line in file:
                # Strip removes leading/trailing whitespace
                stripped_line = line.strip()

                # Increase count if the line is not a comment or blank
                if stripped_line and not stripped_line.startswith("#"):
                    lines_of_code += 1
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

    return lines_of_code


import ast
from collections import Counter


class CallVisitor(ast.NodeVisitor):
    def __init__(self, filter_calls=None):
        super().__init__()
        self.calls = []
        if filter_calls is None:
            filter_calls = []
        self.filter_calls = filter_calls

    def visit_Call(self, node):
        if isinstance(node.func, ast.Attribute):
            # Capture the full method call, including the parent object
            # We traverse the attribute chain to get the full dotted name
            call_name = self.get_full_call_name(node.func)
        elif isinstance(node.func, ast.Name):
            # For direct function calls, e.g., api_call()
            call_name = node.func.id
        skip = False
        for c in self.filter_calls:
            if call_name.startswith(c):
                skip = True
                break
        if not skip:
            self.calls.append(call_name)
        # Continue processing the subtree
        self.generic_visit(node)

    def get_full_call_name(self, node):
        """
        Recursively reconstruct the full dotted name of the method call.
        """
        if isinstance(node, ast.Attribute):
            # Recursively get the string representation of the left part (value)
            value_str = self.get_full_call_name(node.value)
            # Combine with the current attribute name
            return f"{value_str}.{node.attr}"
        elif isinstance(node, ast.Name):
            # Base case: just a simple name
            return node.id


def count_api_calls(file_path, filter_calls=None):
    with open(file_path, "r") as file:
        tree = ast.parse(file.read(), filename=file_path)

    visitor = CallVisitor(filter_calls=filter_calls)
    visitor.visit(tree)

    return Counter(visitor.calls)


def plot_ax(ax, data, xlabel):
    palette = ["#5847AD", "#F7B449"]
    kws = dict(orient="v", errorbar="sd", palette=palette, width=0.6)
    sns.barplot(data=data, ax=ax, **kws)
    data.melt().pipe((sns.scatterplot, "data"), y="value", x="variable", ax=ax,
                     zorder=100, color="grey", alpha=0.5)
    ax.get_xticklabels()[0].set_fontweight("bold")
    ax.tick_params(axis="x", rotation=45)
    ax.tick_params(bottom=False)
    ax.set_title(xlabel)
    ax.set_ylabel("")
    ax.set_xlabel("")
    sns.despine(ax=ax)


if __name__ == "__main__":
    marsilea_tokens = []
    marsilea_loc = []
    marsilea_napi = []
    marsilea_api_entropy = []

    matplotlib_tokens = []
    matplotlib_loc = []
    matplotlib_napi = []
    matplotlib_api_entropy = []

    for file in Path("marsilea").glob("marsilea_cooking_oils_*.py"):
        marsilea_tokens.append(count_tokens(file))
        marsilea_loc.append(count_loc(file))
        calls = count_api_calls(file)
        marsilea_napi.append(len(calls))
        marsilea_api_entropy.append(entropy(list(calls.values())))
    for file in Path("matplotlib").glob("matplotlib_cooking_oils_*.py"):
        matplotlib_tokens.append(count_tokens(file))
        matplotlib_loc.append(count_loc(file))
        calls = count_api_calls(file)
        matplotlib_napi.append(len(calls))
        matplotlib_api_entropy.append(entropy(list(calls.values())))

    # Plot the number of tokens using seaborn
    import seaborn as sns
    import matplotlib.pyplot as plt

    fk.install("Lato", verbose=False)
    data = pd.DataFrame({"Marsilea": marsilea_tokens, "Matplotlib": matplotlib_tokens})
    _, (ax1, ax2, ax3) = plt.subplots(ncols=3, figsize=(6, 5), gridspec_kw={"wspace": 0.5})
    # sns.set(style="whitegrid")
    plot_ax(ax1, data, "Tokens")
    # Plot the number of lines of code using seaborn
    data = pd.DataFrame({"Marsilea": marsilea_loc, "Matplotlib": matplotlib_loc})
    plot_ax(ax2, data, "Lines of Code")
    # Plot_NAPI
    data = pd.DataFrame({"Marsilea": marsilea_napi, "Matplotlib": matplotlib_napi})
    plot_ax(ax3, data, "# of API Calls")
    # Plot API entropy
    # data = pd.DataFrame({"Marsilea": marsilea_api_entropy, "Matplotlib": matplotlib_api_entropy})
    # plot_ax(ax4, data, "API Entropy")

    root = Path(__file__).parent
    plt.savefig(root / "marsilea_vs_matplotlib.png", dpi=300, bbox_inches="tight")
    plt.savefig(root / "marsilea_vs_matplotlib.svg", bbox_inches="tight")
    plt.show()