"""CSV writer for moldlines (.csv)."""

# --------------------------------------------------
# load necessary modules
# --------------------------------------------------
from __future__ import annotations

from pathlib import Path

import numpy as np

from canonical_geometries.moldline import Moldline
from canonical_geometries.writers.columns import COLUMN_NAMES, moldline_table


# --------------------------------------------------
# public API
# --------------------------------------------------
def write_csv(moldline: Moldline, path: str | Path) -> Path:
    """Write a moldline as CSV: one header line with column names and units, then the data.

    Example::

        x [m],y [m],z [m],s [m],nx,ny,nz,curvature [1/m]
        0.0000000000000000e+00,0.0000000000000000e+00,...

    Args:
        moldline: Sampled moldline.
        path: Output file.

    Returns:
        Path of the written file.
    """

    # convert to Path object
    path = Path(path)

    # build the table
    table = moldline_table(moldline)

    # write with a plain header line (no comment marker, so any CSV reader takes it)
    path.parent.mkdir(parents=True, exist_ok=True)
    header = ",".join(COLUMN_NAMES)
    np.savetxt(path, table, delimiter=",", header=header, comments="", fmt="%.16e")

    return path
