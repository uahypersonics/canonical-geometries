"""Tecplot ASCII writer for moldlines (.dat).

Writes one ordered 1D zone in POINT format, laid out like cfd-io's Tecplot ASCII
table writer::

    TITLE = "moldline"
    VARIABLES = "x [m]", "y [m]", "z [m]", "s [m]", "nx", "ny", "nz", "curvature [1/m]"
    ZONE T="moldline", I=283, J=1, K=1, F=POINT
     0.0000000000000000e+00  0.0000000000000000e+00 ...
"""

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
def write_tecplot_ascii(moldline: Moldline, path: str | Path) -> Path:
    """Write a moldline as a Tecplot ASCII point file.

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
    n_points = table.shape[0]

    # build the three Tecplot header lines: title, quoted variable names, zone
    variables = ", ".join(f'"{name}"' for name in COLUMN_NAMES)
    header_lines = [
        'TITLE = "moldline"',
        f"VARIABLES = {variables}",
        f'ZONE T="moldline", I={n_points}, J=1, K=1, F=POINT',
    ]
    header = "\n".join(header_lines)

    # write: header, then one space-separated row per point
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savetxt(path, table, delimiter=" ", header=header, comments="", fmt="% .16e")

    return path
