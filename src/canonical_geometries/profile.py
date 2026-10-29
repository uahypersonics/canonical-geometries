"""Common interface for 2D body profiles parametrized by arc length."""

# --------------------------------------------------
# load necessary modules
# --------------------------------------------------
from __future__ import annotations

from typing import Protocol

import numpy as np
from numpy.typing import ArrayLike, NDArray

# --------------------------------------------------
# constants
# --------------------------------------------------

# relative tolerance for accepting arc lengths just outside [0, total_length]
# (round-off from computing s in the caller, e.g. np.linspace(0, total_length, n))
_ARC_LENGTH_RTOL = 1.0e-12


# --------------------------------------------------
# profile interface
# --------------------------------------------------
class Profile2D(Protocol):
    """Exact 2D body profile parametrized by arc length s.

    The arc length runs from s = 0 at the stagnation point along the surface to
    s = total_length at the downstream end. All methods are vectorized: they take
    a scalar or an array of s values and return arrays of the same shape.

    The profile carries no point distribution. Sampling the surface is left to
    the grid generator.
    """

    @property
    def total_length(self) -> float:
        """Arc length of the whole profile."""
        ...

    @property
    def junctions(self) -> NDArray[np.float64]:
        """Arc lengths where the profile's pieces meet (interior junctions only)."""
        ...

    def point(self, s: ArrayLike) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """Return the surface coordinates (x, y) at arc length s."""
        ...

    def tangent(self, s: ArrayLike) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """Return the unit tangent (tx, ty) at s, pointing towards increasing s."""
        ...

    def normal(self, s: ArrayLike) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """Return the unit normal (nx, ny) at s, pointing away from the body into the flow."""
        ...

    def curvature(self, s: ArrayLike) -> NDArray[np.float64]:
        """Return the surface curvature at s (positive where the surface is convex)."""
        ...


# --------------------------------------------------
# shared helpers for profile implementations
# --------------------------------------------------
def check_arc_length(s: ArrayLike, total_length: float) -> NDArray[np.float64]:
    """Convert s to a float array and check that it lies in [0, total_length].

    Values within a round-off tolerance outside the range are clipped onto it.

    Args:
        s: Arc length(s).
        total_length: Arc length of the whole profile.

    Returns:
        Float array of arc lengths, clipped onto [0, total_length].

    Raises:
        ValueError: If any s lies outside [0, total_length] by more than round-off.
    """

    # convert to float array
    s_arr = np.asarray(s, dtype=float)

    # check range with a small round-off tolerance
    total = total_length
    tol = _ARC_LENGTH_RTOL * total
    if np.any(s_arr < -tol) or np.any(s_arr > total + tol):
        raise ValueError(
            f"arc length must lie in [0, {total}], got values in [{s_arr.min()}, {s_arr.max()}]"
        )

    # clip round-off onto the valid range
    s_clipped = np.clip(s_arr, 0.0, total)

    return s_clipped
