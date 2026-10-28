"""Common interface for 2D body profiles parametrized by arc length."""

# --------------------------------------------------
# load necessary modules
# --------------------------------------------------
from __future__ import annotations

from typing import Protocol

import numpy as np
from numpy.typing import ArrayLike, NDArray


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
