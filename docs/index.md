# canonical-geometries

Exact 2D profiles of canonical high-speed test geometries, and a CLI that writes their moldlines.

Each profile is parametrized by arc length s from the stagnation point and gives
points, unit tangents, unit normals and curvature at any s, exactly.

| Geometry | CLI |
|---|---|
| Blunted flat plate | `geometry plate` |
| Blunted wedge (planar) | `geometry wedge` |
| Sphere-cone (axisymmetric) | `geometry cone` |
| Spherically blunted tangent ogive (axisymmetric), optional cylinder | `geometry tangent-ogive` |

## Quick start

```bash
geometry cone init             # write cone.toml
geometry cone run cone.toml    # write the moldline next to the config
```

See [Installation](installation.md) to get started. More documentation will follow.
