# Contributing

We now use [uv](https://docs.astral.sh/uv/) to manage our development environment.

## Setup

Setup your development environment by running:

```bash
uv lock
uv run pre-commit install
```

Start a IPython/Jupyter session by running:

```bash
uv run --with ipython ipython
# or
uv run --with jupyter jupyter lab
```

## Test
To run the tests, use:

```bash
uv run task test
```

## Documentation

To build the documentation, use:

```bash
# Build doc with cache
uv run task doc-build
# Fresh build
uv run task doc-clean-build
```

To serve the documentation, use:

```bash
uv run task doc-serve
```
