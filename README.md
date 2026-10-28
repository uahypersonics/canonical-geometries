# canonical-geometries

Exact 2D profiles of canonical high-speed test geometries, parametrized by arc length,
with a `geometry` CLI that writes their moldlines.

Each profile gives points, unit tangents, unit normals and curvature at any arc
length s, vectorized over numpy arrays. Profiles carry no grid point distribution:
sampling the surface for a grid is left to the grid generator.

| Geometry | Class | Status |
|---|---|---|
| Blunted flat plate (`geometry plate`) | `BluntedWedge`, half-angle 0 | available |
| Blunted wedge, planar (`geometry wedge`) | `BluntedWedge` | available |
| Sphere-cone meridian (`geometry cone`) | `BluntedWedge` | available |
| Tangent ogive (sharp and blunted) | | planned |

## Install

From a clone of this repository:

```bash
python -m pip install -e .
```

## Quick Start

### CLI

One command group per geometry, each with `init` (write a starter config for that
geometry) and `run` (write the moldline):

```bash
geometry plate init            # plate.toml: nose_radius, length
geometry wedge init            # wedge.toml: nose_radius, length, half_angle (planar)
geometry cone init             # cone.toml:  nose_radius, length, half_angle (sphere-cone)

geometry cone run cone.toml    # writes cone.csv next to the config
```

The output file's extension picks the format:

| Extension | Format |
|---|---|
| `.csv` | CSV, one header line with column names and units |
| `.dat` | Tecplot ASCII, one ordered zone (`TITLE`, `VARIABLES`, `ZONE ... F=POINT`) |

Both have the columns `x, y, z, s` [m], `nx, ny, nz` (unit normal) and `curvature`
[1/m], with the units in the variable names. Coordinates come first, so readers that
take the first two columns as x and y (and Tecplot's default axes) get them right.
The profile lies in the z = 0 plane, so z = nz = 0.

Each config holds that geometry's parameters, the number of points on the nose and
on the body, and the output files. `run` checks the file's `type` matches the command:

```toml
[geometry]
# type marker
type = "cone"
# nose radius in [m]
nose_radius = 100.0e-6
# length of cone, measured axially from nose tip in [m]
length = 0.5
# cone half-angle in [deg]
half_angle = 7.0

[points]
# number of points on the nose arc (84 = 1 deg steps on the 83 deg arc)
n_nose = 84
# number of points on the cone surface
n_body = 200

[output]
# moldline file: .csv, or .dat for Tecplot ASCII
# columns: x, y, z, s in [m]; nx, ny, nz; curvature in [1/m]
file = "cone.csv"
```

### Python API

```python
import numpy as np
from canonical_geometries import BluntedWedge, sample_moldline, write_moldline

# blunted plate: half_angle defaults to 0
plate = BluntedWedge(nose_radius=100e-6, length=0.5)

# 7 deg sphere-cone meridian (or planar blunted wedge)
cone = BluntedWedge(nose_radius=100e-6, length=0.5, half_angle=7.0)

# evaluate anywhere along the surface
s = np.linspace(0.0, cone.total_length, 200)
x, y = cone.point(s)
nx, ny = cone.normal(s)         # unit normals, pointing into the flow
kappa = cone.curvature(s)       # 1/r_n on the nose, 0 on the body

# nose-body tangency point
print(cone.junctions)           # arc length s_j = r_n (pi/2 - theta)
print(cone.junction_point)      # (x_j, y_j) = (r_n (1 - sin theta), r_n cos theta)

# sample with the junction as an exact point: 91 nose + 200 body points
moldline = sample_moldline(cone, [91, 200])

# write; the extension picks the format
write_moldline(moldline, "cone.dat")
```

## Coordinates

The stagnation point is at the origin, with x downstream and y up (upper half only).
The nose is a circular arc with centre (r_n, 0). Its polar angle runs from 0 at the
stagnation point to 90 deg - half_angle, where the arc is tangent to the straight
body. The body ends at x = L. Arc length s runs from the stagnation point, around
the nose, to the end of the body.

The profile is continuous in position and slope at the junction; curvature jumps
from 1/r_n to 0 there. Equal steps in s on the nose are equal steps in angle, and the
nose normals point radially from the nose centre.

Planar (wedge, plate) versus axisymmetric (sphere-cone) is a choice for the grid and
the solver; the profile is the same.

## Development

```bash
python -m pip install -e ".[dev]"
pytest
ruff check src tests
```
