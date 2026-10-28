"""Moldline writers, picked by file extension.

| Extension | Format | Writer |
|---|---|---|
| ``.csv`` | CSV with a header line | ``write_csv`` |
| ``.dat`` | Tecplot ASCII, one ordered zone | ``write_tecplot_ascii`` |

All writers share the column layout in ``writers.columns``.
"""

# --------------------------------------------------
# load necessary modules
# --------------------------------------------------
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from canonical_geometries.moldline import Moldline
from canonical_geometries.writers.columns import COLUMN_NAMES
from canonical_geometries.writers.csv import write_csv
from canonical_geometries.writers.tecplot_ascii import write_tecplot_ascii

# --------------------------------------------------
# registry: file extension -> writer
# --------------------------------------------------
WRITERS: dict[str, Callable[[Moldline, Path], Path]] = {
    ".csv": write_csv,
    ".dat": write_tecplot_ascii,
}


# --------------------------------------------------
# public API
# --------------------------------------------------
def write_moldline(moldline: Moldline, path: str | Path) -> Path:
    """Write a moldline in the format given by the file extension (see WRITERS).

    The extension is matched case-insensitively (".DAT" works like ".dat").

    Args:
        moldline: Sampled moldline.
        path: Output file; its extension picks the format.

    Returns:
        Path of the written file.

    Raises:
        ValueError: If the extension has no writer.
    """

    # convert to Path object
    path = Path(path)

    # pick the writer by extension
    extension = path.suffix.lower()
    if extension not in WRITERS:
        supported = ", ".join(WRITERS)
        raise ValueError(f"no moldline writer for '{path.suffix}' ({path}); supported: {supported}")
    writer = WRITERS[extension]

    # write
    written_path = writer(moldline, path)

    return written_path


__all__ = [
    "COLUMN_NAMES",
    "WRITERS",
    "write_csv",
    "write_moldline",
    "write_tecplot_ascii",
]
