"""Public package interface for canonical_geometries."""

# --------------------------------------------------
# load necessary modules
# --------------------------------------------------
from importlib.metadata import (
    PackageNotFoundError,
    version,
)

from canonical_geometries.blunted_wedge import BluntedWedge
from canonical_geometries.moldline import Moldline, sample_moldline
from canonical_geometries.profile import Profile2D
from canonical_geometries.writers import write_moldline

# --------------------------------------------------
# resolve package version
# --------------------------------------------------
try:
    __version__ = version("canonical-geometries")
except PackageNotFoundError:
    __version__ = "0+unknown"


__all__ = [
    "BluntedWedge",
    "Moldline",
    "Profile2D",
    "__version__",
    "sample_moldline",
    "write_moldline",
]
