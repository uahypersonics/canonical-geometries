"""Column layout shared by all moldline writers."""

# --------------------------------------------------
# load necessary modules
# --------------------------------------------------
from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from canonical_geometries.moldline import Moldline

# --------------------------------------------------
# constants
# --------------------------------------------------

# column order with units; normal components are dimensionless. Coordinates come
# first so readers that take "column 0 = x, column 1 = y" (and Tecplot's default
# axes) get them right
COLUMN_NAMES = ("x [m]", "y [m]", "z [m]", "s [m]", "nx", "ny", "nz", "curvature [1/m]")


# --------------------------------------------------
# public API
# --------------------------------------------------
def moldline_table(moldline: Moldline) -> NDArray[np.float64]:
    """Arrange a moldline as a table with one row per point, columns as in COLUMN_NAMES.

    The profile lies in the z = 0 plane, so z and nz are zero; they are included so
    the files hold full 3D points and normals for tools that expect them.

    Args:
        moldline: Sampled moldline.

    Returns:
        Array of shape (n_points, len(COLUMN_NAMES)).
    """

    # the profile lies in the z = 0 plane
    z = np.zeros_like(moldline.x)
    nz = np.zeros_like(moldline.nx)

    # build one column per quantity, in COLUMN_NAMES order
    table = np.column_stack(
        [
            moldline.x,
            moldline.y,
            z,
            moldline.s,
            moldline.nx,
            moldline.ny,
            nz,
            moldline.curvature,
        ]
    )

    return table
