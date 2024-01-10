from pathlib import Path

if __name__ == "__main__":
    SAVE_PATH = Path(__file__).parent / "publication"
    SAVE_PATH.mkdir(exist_ok=True)

    examples = Path(__file__).parent.parent / "examples"
    # Generate SVG for all examples
    for p in examples.glob("*.py"):
        # read the python file and execute it
        with open(p, "r") as f:
            code = f.read()
            code += "\n" + ("import matplotlib.pyplot as plt; "
                            f"plt.savefig(r'{SAVE_PATH / p.stem.lstrip('plot_')}.svg')")
            exec(code)
