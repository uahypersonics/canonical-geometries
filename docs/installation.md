# Installation

Requires Python 3.11 or newer. The only dependencies are numpy, pydantic and typer.

## From PyPI

```bash
pip install canonical-geometries
```

To upgrade an existing installation:

```bash
pip install --upgrade canonical-geometries
```

## From source

From a clone of the repository:

```bash
pip install -e .            # package and the geometry CLI
pip install -e ".[dev]"     # plus pytest, pytest-cov, ruff
pip install -e ".[docs]"    # plus zensical, mkdocstrings
```

## Check the installation

```bash
geometry --version
```
