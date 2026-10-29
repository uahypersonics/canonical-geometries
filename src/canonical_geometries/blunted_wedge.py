"""2D circular nose followed by a straight body at a half-angle (upper half only).

The same profile describes three test geometries:

- half_angle = 0: flat plate with a circular leading edge (blunted plate)
- half_angle > 0, planar: blunted wedge
- half_angle > 0, axisymmetric: meridian of a sphere-cone (e.g. 7 deg)

Planar vs axisymmetric is a choice for the grid and the solver, not the profile.

Coordinates
-----------
- origin at the stagnation point, x downstream, y up
- nose: circular arc with centre (r_n, 0). Its polar angle phi is measured from
  the stagnation point and runs from 0 to phi_j = 90 deg - half_angle
- junction (tangency point): (r_n (1 - sin theta), r_n cos theta), theta = half_angle
- body: straight line from the junction in direction (cos theta, sin theta),
  ending at x = L (L is measured from the nose tip along x)

At the junction the arc's tangent equals the body direction, so the profile is
continuous in position and slope. Curvature jumps from 1 / r_n to 0 there.

Arc length s runs from 0 at the stagnation point, around the nose, to the end of
the body:

- nose:  0 <= s <= s_j, with s_j = r_n phi_j and phi = s / r_n
- body: s_j < s <= s_j + (L - x_j) / cos theta

Equal steps in s on the nose are equal steps in angle, and the nose normals point
radially away from the nose centre, so a constant-height grid around the nose is a
polar grid. At s = s_j exactly, the curvature is reported as the nose value.
"""

# --------------------------------------------------
# load necessary modules
# --------------------------------------------------
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray

from canonical_geometries.profile import check_arc_length


# --------------------------------------------------
# blunted wedge profile
# --------------------------------------------------
@dataclass(frozen=True, slots=True)
class BluntedWedge:
    """Circular nose plus straight body, upper half, parametrized by arc length.

    With the default half_angle = 0 this is the blunted flat plate.

    Attributes:
        nose_radius: Nose radius r_n [m].
        length: Axial length L [m], measured from the nose tip (stagnation point).
        half_angle: Body half-angle theta [deg], 0 <= theta < 90.
    """

    nose_radius: float
    length: float
    half_angle: float = 0.0

    def __post_init__(self) -> None:
        # validate inputs
        if self.nose_radius <= 0.0:
            raise ValueError(f"nose_radius must be positive, got {self.nose_radius}")
        if not 0.0 <= self.half_angle < 90.0:
            raise ValueError(f"half_angle must lie in [0, 90) deg, got {self.half_angle}")

        # the body must extend past the junction
        x_junction = self.nose_radius * (1.0 - math.sin(math.radians(self.half_angle)))
        if self.length <= x_junction:
            raise ValueError(
                f"length must be greater than the junction x position ({x_junction}), "
                f"got {self.length}"
            )

    # --------------------------------------------------
    # derived geometry
    # --------------------------------------------------
    @property
    def junction_angle(self) -> float:
        """Polar angle phi_j = 90 deg - half_angle [rad] where the nose meets the body."""
        phi_junction = 0.5 * math.pi - math.radians(self.half_angle)
        return phi_junction

    @property
    def junction_point(self) -> tuple[float, float]:
        """Coordinates (x_j, y_j) of the tangency point between nose and body."""
        theta = math.radians(self.half_angle)
        x_junction = self.nose_radius * (1.0 - math.sin(theta))
        y_junction = self.nose_radius * math.cos(theta)
        return x_junction, y_junction

    @property
    def junction_arc_length(self) -> float:
        """Arc length s_j = r_n phi_j where the nose meets the body."""
        s_junction = self.nose_radius * self.junction_angle
        return s_junction

    @property
    def total_length(self) -> float:
        """Arc length of the whole profile, s_j + (L - x_j) / cos(theta)."""
        theta = math.radians(self.half_angle)
        x_junction, _ = self.junction_point
        body_length = (self.length - x_junction) / math.cos(theta)
        total = self.junction_arc_length + body_length
        return total

    @property
    def junctions(self) -> NDArray[np.float64]:
        """Arc lengths where the pieces meet: the nose-body junction."""
        junctions = np.array([self.junction_arc_length])
        return junctions

    # --------------------------------------------------
    # public evaluation methods
    # --------------------------------------------------
    def point(self, s: ArrayLike) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """Return the surface coordinates at arc length s.

        Args:
            s: Arc length(s) in [0, total_length].

        Returns:
            Tuple (x, y) of arrays with the shape of s.

        Raises:
            ValueError: If any s lies outside [0, total_length].
        """

        # validate inputs
        s_arr = check_arc_length(s, self.total_length)
        r_n = self.nose_radius
        s_j = self.junction_arc_length
        theta = math.radians(self.half_angle)
        x_j, y_j = self.junction_point

        # nose: circular arc around (r_n, 0)
        # clip to the nose range so body points don't produce angles past phi_j
        phi = np.minimum(s_arr, s_j) / r_n
        x_nose = r_n - r_n * np.cos(phi)
        y_nose = r_n * np.sin(phi)

        # body: straight line from the junction at the half-angle
        distance_on_body = s_arr - s_j
        x_body = x_j + distance_on_body * math.cos(theta)
        y_body = y_j + distance_on_body * math.sin(theta)

        # pick the piece each s belongs to
        on_nose = s_arr <= s_j
        x = np.where(on_nose, x_nose, x_body)
        y = np.where(on_nose, y_nose, y_body)

        return x, y

    def tangent(self, s: ArrayLike) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """Return the unit tangent at arc length s, pointing towards increasing s.

        Args:
            s: Arc length(s) in [0, total_length].

        Returns:
            Tuple (tx, ty) of arrays with the shape of s.

        Raises:
            ValueError: If any s lies outside [0, total_length].
        """

        # validate inputs
        s_arr = check_arc_length(s, self.total_length)
        s_j = self.junction_arc_length
        theta = math.radians(self.half_angle)

        # nose: derivative of (r_n - r_n cos(phi), r_n sin(phi)) w.r.t. s
        phi = np.minimum(s_arr, s_j) / self.nose_radius
        tx_nose = np.sin(phi)
        ty_nose = np.cos(phi)

        # body: constant direction (cos theta, sin theta)
        tx_body = np.full_like(s_arr, math.cos(theta))
        ty_body = np.full_like(s_arr, math.sin(theta))

        # pick the piece each s belongs to
        on_nose = s_arr <= s_j
        tx = np.where(on_nose, tx_nose, tx_body)
        ty = np.where(on_nose, ty_nose, ty_body)

        return tx, ty

    def normal(self, s: ArrayLike) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """Return the unit normal at arc length s, pointing away from the body into the flow.

        The normal is the tangent rotated by +90 degrees, (nx, ny) = (-ty, tx). With
        s running along the wall and the normal into the flow, (s, n) is a
        right-handed (counter-clockwise) pair.

        Args:
            s: Arc length(s) in [0, total_length].

        Returns:
            Tuple (nx, ny) of arrays with the shape of s.

        Raises:
            ValueError: If any s lies outside [0, total_length].
        """

        # build from the tangent (validates s)
        tx, ty = self.tangent(s)

        # rotate by +90 degrees
        nx = -ty
        ny = tx

        return nx, ny

    def curvature(self, s: ArrayLike) -> NDArray[np.float64]:
        """Return the surface curvature at arc length s.

        Curvature is 1 / r_n on the nose (convex, positive) and 0 on the body. It
        jumps at the junction; s = s_j itself returns the nose value.

        Args:
            s: Arc length(s) in [0, total_length].

        Returns:
            Array of curvatures [1/m] with the shape of s.

        Raises:
            ValueError: If any s lies outside [0, total_length].
        """

        # validate inputs
        s_arr = check_arc_length(s, self.total_length)

        # constant on each piece
        on_nose = s_arr <= self.junction_arc_length
        kappa = np.where(on_nose, 1.0 / self.nose_radius, 0.0)

        return kappa
