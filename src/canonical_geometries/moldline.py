"""Sample a profile into a moldline (writing it to files lives in canonical_geometries.writers)."""

# --------------------------------------------------
# load necessary modules
# --------------------------------------------------
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from canonical_geometries.profile import Profile2D


# --------------------------------------------------
# moldline data
# --------------------------------------------------
@dataclass(frozen=True, slots=True)
class Moldline:
    """Sampled profile: arc length, coordinates, unit normals and curvature per point.

    Attributes:
        s: Arc length [m].
        x: x coordinate [m].
        y: y coordinate [m].
        nx: x component of the unit normal (into the flow).
        ny: y component of the unit normal (into the flow).
        curvature: Surface curvature [1/m].
    """

    s: NDArray[np.float64]
    x: NDArray[np.float64]
    y: NDArray[np.float64]
    nx: NDArray[np.float64]
    ny: NDArray[np.float64]
    curvature: NDArray[np.float64]


# --------------------------------------------------
# sampling
# --------------------------------------------------
def sample_moldline(profile: Profile2D, points_per_piece: Sequence[int]) -> Moldline:
    """Sample a profile with equally spaced points on each of its pieces.

    Each piece (e.g. nose, then body) gets its own count, including both of its
    end points. Neighbouring pieces share the junction point, so the junctions are
    always sampled exactly and the total point count is sum(points_per_piece) minus
    the number of junctions. On a circular nose, equal steps in arc length are
    equal steps in angle.

    Args:
        profile: Profile to sample.
        points_per_piece: Number of points on each piece, in order along s.

    Returns:
        Sampled moldline.

    Raises:
        ValueError: If the counts don't match the number of pieces, or a count is below 2.
    """

    # piece boundaries in arc length
    junctions = np.asarray(profile.junctions, dtype=float)
    piece_bounds = [0.0, *junctions.tolist(), profile.total_length]
    n_pieces = len(piece_bounds) - 1

    # validate inputs
    if len(points_per_piece) != n_pieces:
        raise ValueError(f"profile has {n_pieces} pieces, got {len(points_per_piece)} point counts")
    for n_points in points_per_piece:
        if n_points < 2:
            raise ValueError(f"each piece needs at least 2 points, got {n_points}")

    # arc lengths, one piece at a time
    s_parts = []
    for index, n_points in enumerate(points_per_piece):
        s_start = piece_bounds[index]
        s_end = piece_bounds[index + 1]
        s_piece = np.linspace(s_start, s_end, n_points)

        # drop the shared junction point that the previous piece already holds
        if index > 0:
            s_piece = s_piece[1:]

        s_parts.append(s_piece)
    s = np.concatenate(s_parts)

    # evaluate the profile
    x, y = profile.point(s)
    nx, ny = profile.normal(s)
    curvature = profile.curvature(s)

    moldline = Moldline(
        s=s,
        x=x,
        y=y,
        nx=nx,
        ny=ny,
        curvature=curvature,
    )
    return moldline
