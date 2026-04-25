from pathlib import Path
import shutil

root = Path(__file__).parent  # ./docs

target_folders = [
    root / "build",
    root / "examples" / "imgs",
    root / "source" / "api" / "APIs",
    root / "source" / "examples",
    root / "source" / "how_to",
]

# Sphinx-gallery generates these files at the source root level
target_files = [
    root / "source" / "sg_execution_times.rst",
]


if __name__ == "__main__":
    for folder in target_folders:
        if folder.exists():
            shutil.rmtree(folder)
    for fpath in target_files:
        if fpath.exists():
            fpath.unlink()
