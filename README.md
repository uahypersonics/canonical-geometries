# canonical-geometries

Exact 2D profiles of canonical high-speed test geometries, and a CLI that writes their moldlines.

[![Test](https://github.com/uahypersonics/canonical-geometries/actions/workflows/test.yml/badge.svg)](https://github.com/uahypersonics/canonical-geometries/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/uahypersonics/canonical-geometries/branch/main/graph/badge.svg)](https://codecov.io/gh/uahypersonics/canonical-geometries)
[![PyPI](https://img.shields.io/pypi/v/canonical-geometries)](https://pypi.org/project/canonical-geometries/)
[![Docs](https://img.shields.io/badge/docs-zensical-blue)](https://uahypersonics.github.io/canonical-geometries/)
[![License](https://img.shields.io/badge/license-BSD--3--Clause-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-≥3.11-blue.svg)](https://www.python.org/downloads/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

## Install

```bash
pip install canonical-geometries
```

To upgrade an existing installation:

```bash
pip install --upgrade canonical-geometries
```

## Quick Start

**API:**

```python
from canonical_geometries import BluntedWedge, sample_moldline, write_moldline

# 7 deg sphere-cone meridian; half_angle = 0 (the default) is the blunted flat plate
cone = BluntedWedge(nose_radius=100e-6, length=0.5, half_angle=7.0)

# exact surface quantities at any arc length s from the stagnation point
x, y = cone.point(1.0e-3)
nx, ny = cone.normal(1.0e-3)        # unit normal, pointing into the flow
print(cone.junction_point)          # nose-body tangency point

# sample (84 nose + 200 body points, junction included) and write;
# the extension picks the format: .csv or .dat (Tecplot ASCII)
moldline = sample_moldline(cone, [84, 200])
write_moldline(moldline, "cone.dat")
```

**CLI:**

```bash
geometry plate init            # write plate.toml (blunted flat plate)
geometry wedge init            # write wedge.toml (planar blunted wedge)
geometry cone init             # write cone.toml  (sphere-cone)
geometry tangent-ogive init    # write tangent-ogive.toml (blunted tangent ogive)

geometry cone run cone.toml    # write the moldline next to the config
```

## Documentation

Full documentation: https://uahypersonics.github.io/canonical-geometries

## Testing

Run the ruff check and pytest in the project root:

```bash
pip install -e ".[dev]"
ruff check src tests
pytest
```

## Code Style

This project follows established Python community conventions so that
contributors can focus on the physics rather than inventing formatting rules.

| Convention | What it covers | Reference |
|---|---|---|
| [PEP 8](https://peps.python.org/pep-0008/) | Code formatting, naming, whitespace | Python standard style guide |
| [PEP 257](https://peps.python.org/pep-0257/) | Docstring structure (triple-quoted, imperative mood) | Python standard docstring conventions |
| [Google style](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) | Docstring sections (`Args`, `Returns`, `Raises`) | Google Python style guide |
| [Ruff](https://docs.astral.sh/ruff/) | Automated linting and formatting | Enforces PEP 8 compliance automatically |
| [typing / TYPE_CHECKING](https://docs.python.org/3/library/typing.html#typing.TYPE_CHECKING) | Type hints for IDE support and static analysis | Python standard library |

## Releasing

This project uses [Semantic Versioning](https://semver.org/) (`vMAJOR.MINOR.PATCH`):

- **MAJOR** (`v1.0.0`, `v2.0.0`): Breaking API changes
- **MINOR** (`v0.3.0`, `v0.4.0`): New features, backward-compatible
- **PATCH** (`v0.3.1`, `v0.3.2`): Bug fixes, minor corrections

The version comes from the git tag. To publish a new version to
[PyPI](https://pypi.org/project/canonical-geometries/):

1. Commit and push to `main`
2. Tag and push:
   ```bash
   git tag -a vMAJOR.MINOR.PATCH -m "Release vMAJOR.MINOR.PATCH"
   git push origin vMAJOR.MINOR.PATCH
   ```

The GitHub Actions workflow will automatically build and publish to PyPI via Trusted Publishing.

## License

BSD 3-Clause License. See [LICENSE](LICENSE) for the complete license terms.
