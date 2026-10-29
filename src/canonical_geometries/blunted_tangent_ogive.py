"""2D spherically blunted tangent ogive, optionally followed by a cylinder (upper half only).

The profile is the meridian of an axisymmetric body: a spherical nose, a tangent
ogive, and an optional cylinder of the base radius.

Sharp ogive (the definition the length refers to)
-------------------------------------------------
A tangent ogive of length L and base radius R is a circular arc of radius

    rho = (R^2 + L^2) / (2 R)

from the sharp tip to the base, where it is tangent to the cylinder (slope 0).
Blunting replaces the tip with a sphere of radius r_n, centred on the axis and
tangent to the arc from inside. The blunted body is therefore shorter than L.

Coordinates
-----------
- origin at the stagnation point, x downstream, y up (y is the radius)
- nose: circular arc with centre (r_n, 0). Its polar angle phi is measured from
  the stagnation point and runs from 0 to phi_j = 90 deg - theta_t
- theta_t: slope angle where nose and ogive meet, cos(theta_t) = (rho - R) / (rho - r_n)
- ogive: circular arc with centre (x_b, R - rho), where x_b = r_n + (rho - r_n) sin(theta_t)
  is the base position. Its angle alpha from the vertical runs from theta_t at the
  junction down to 0 at the base point (x_b, R)
- cylinder (optional): straight line y = R from x_b to x_b + cylinder_length

The sharp ogive's tip would lie at x = x_b - L, upstream of the stagnation point.

At both junctions position and slope are continuous. Curvature jumps from 1 / r_n
to 1 / rho at the nose/ogive junction, and from 1 / rho to 0 at the base.

Arc length s runs from 0 at the stagnation point, around the nose, along the
ogive, and along the cylinder:

- nose:     0 <= s <= s_j, with s_j = r_n phi_j and phi = s / r_n
- ogive:    s_j < s <= s_b, with s_b = s_j + rho theta_t and alpha = theta_t - (s - s_j) / rho
- cylinder: s_b < s <= s_b + cylinder_length

At a junction itself, the curvature is reported as the upstream piece's value.
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
# blunted tangent ogive profile
# --------------------------------------------------
@dataclass(frozen=True, slots=True)
class BluntedTangentOgive:
    """Spherical nose, tangent ogive, optional cylinder; upper half, parametrized by arc length.

    Attributes:
        nose_radius: Nose radius r_n [m], smaller than the base radius.
        length: Length L of the sharp ogive, tip to base [m]; the blunted body is shorter.
        base_radius: Base radius R [m], smaller than L.
        cylinder_length: Length of the cylinder after the base [m]; 0 for none.
    """

    nose_radius: float
    length: float
    base_radius: float
    cylinder_length: float = 0.0

    def __post_init__(self) -> None:
        # validate inputs
        if self.nose_radius <= 0.0:
            raise ValueError(f"nose_radius must be positive, got {self.nose_radius}")
        if self.base_radius <= 0.0:
            raise ValueError(f"base_radius must be positive, got {self.base_radius}")
        if self.cylinder_length < 0.0:
            raise ValueError(f"cylinder_length must not be negative, got {self.cylinder_length}")

        # a tangent ogive needs L > R (otherwise the arc bulges forward past the tip)
        if self.length <= self.base_radius:
            raise ValueError(
                f"length ({self.length}) must be greater than base_radius ({self.base_radius})"
            )

        # the nose sphere must fit inside the ogive (r_n = R would be a sphere-cylinder)
        if self.nose_radius >= self.base_radius:
            raise ValueError(
                f"nose_radius ({self.nose_radius}) must be smaller than base_radius "
                f"({self.base_radius})"
            )

    # --------------------------------------------------
    # derived geometry
    # --------------------------------------------------
    @property
    def ogive_radius(self) -> float:
        """Radius rho = (R^2 + L^2) / (2 R) of the ogive arc."""
        rho = (self.base_radius**2 + self.length**2) / (2.0 * self.base_radius)
        return rho

    @property
    def tangency_angle(self) -> float:
        """Slope angle theta_t [rad] where the nose meets the ogive."""
        rho = self.ogive_radius
        theta_t = math.acos((rho - self.base_radius) / (rho - self.nose_radius))
        return theta_t

    @property
    def junction_angle(self) -> float:
        """Polar angle phi_j = 90 deg - theta_t [rad] where the nose meets the ogive."""
        phi_junction = 0.5 * math.pi - self.tangency_angle
        return phi_junction

    @property
    def junction_point(self) -> tuple[float, float]:
        """Coordinates (x_j, y_j) of the tangency point between nose and ogive."""
        theta_t = self.tangency_angle
        x_junction = self.nose_radius * (1.0 - math.sin(theta_t))
        y_junction = self.nose_radius * math.cos(theta_t)
        return x_junction, y_junction

    @property
    def junction_arc_length(self) -> float:
        """Arc length s_j = r_n phi_j where the nose meets the ogive."""
        s_junction = self.nose_radius * self.junction_angle
        return s_junction

    @property
    def base_point(self) -> tuple[float, float]:
        """Coordinates (x_b, R) of the ogive base, where the cylinder starts."""
        rho = self.ogive_radius
        x_base = self.nose_radius + (rho - self.nose_radius) * math.sin(self.tangency_angle)
        return x_base, self.base_radius

    @property
    def base_arc_length(self) -> float:
        """Arc length s_b = s_j + rho theta_t at the ogive base."""
        s_base = self.junction_arc_length + self.ogive_radius * self.tangency_angle
        return s_base

    @property
    def sharp_tip_x(self) -> float:
        """x position of the sharp ogive's tip, x_b - L (upstream of the stagnation point)."""
        x_base, _ = self.base_point
        x_tip = x_base - self.length
        return x_tip

    @property
    def total_length(self) -> float:
        """Arc length of the whole profile, s_b + cylinder_length."""
        total = self.base_arc_length + self.cylinder_length
        return total

    @property
    def junctions(self) -> NDArray[np.float64]:
        """Arc lengths where the pieces meet: nose/ogive, and ogive/cylinder if there is one."""
        if self.cylinder_length > 0.0:
            junctions = np.array([self.junction_arc_length, self.base_arc_length])
        else:
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
        rho = self.ogive_radius
        x_base, y_base = self.base_point

        # nose: circular arc around (r_n, 0)
        phi = self._nose_angle(s_arr)
        x_nose = r_n - r_n * np.cos(phi)
        y_nose = r_n * np.sin(phi)

        # ogive: circular arc around (x_b, R - rho), angle alpha from the vertical
        alpha = self._ogive_angle(s_arr)
        x_ogive = x_base - rho * np.sin(alpha)
        y_ogive = (y_base - rho) + rho * np.cos(alpha)

        # cylinder: straight line at the base radius
        x_cylinder = x_base + (s_arr - self.base_arc_length)
        y_cylinder = np.full_like(s_arr, y_base)

        # pick the piece each s belongs to
        pieces = self._pieces(s_arr)
        x = np.select(pieces, [x_nose, x_ogive, x_cylinder])
        y = np.select(pieces, [y_nose, y_ogive, y_cylinder])

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

        # nose: derivative of (r_n - r_n cos(phi), r_n sin(phi)) w.r.t. s
        phi = self._nose_angle(s_arr)
        tx_nose = np.sin(phi)
        ty_nose = np.cos(phi)

        # ogive: derivative of (x_b - rho sin(alpha), ... + rho cos(alpha)), d(alpha)/ds = -1/rho
        alpha = self._ogive_angle(s_arr)
        tx_ogive = np.cos(alpha)
        ty_ogive = np.sin(alpha)

        # cylinder: along x
        tx_cylinder = np.ones_like(s_arr)
        ty_cylinder = np.zeros_like(s_arr)

        # pick the piece each s belongs to
        pieces = self._pieces(s_arr)
        tx = np.select(pieces, [tx_nose, tx_ogive, tx_cylinder])
        ty = np.select(pieces, [ty_nose, ty_ogive, ty_cylinder])

        return tx, ty

    def normal(self, s: ArrayLike) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """Return the unit normal at arc length s, pointing away from the body into the flow.

        The normal is the tangent rotated by +90 degrees, (nx, ny) = (-ty, tx).

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

        Curvature is 1 / r_n on the nose, 1 / rho on the ogive (both convex, positive)
        and 0 on the cylinder. At a junction the upstream piece's value is returned.

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
        pieces = self._pieces(s_arr)
        kappa = np.select(pieces, [1.0 / self.nose_radius, 1.0 / self.ogive_radius, 0.0])

        return kappa

    # --------------------------------------------------
    # private helpers
    # --------------------------------------------------
    def _pieces(self, s_arr: NDArray[np.float64]) -> list[NDArray[np.bool_]]:
        """Masks for the nose, ogive and cylinder pieces (in that order)."""

        # build: each junction belongs to the upstream piece
        on_nose = s_arr <= self.junction_arc_length
        on_ogive = ~on_nose & (s_arr <= self.base_arc_length)
        on_cylinder = s_arr > self.base_arc_length
        pieces = [on_nose, on_ogive, on_cylinder]

        return pieces

    def _nose_angle(self, s_arr: NDArray[np.float64]) -> NDArray[np.float64]:
        """Nose polar angle phi, clipped to the nose so other pieces don't overshoot it."""

        # convert arc length to angle
        phi = np.minimum(s_arr, self.junction_arc_length) / self.nose_radius
        return phi

    def _ogive_angle(self, s_arr: NDArray[np.float64]) -> NDArray[np.float64]:
        """Ogive angle alpha from the vertical, clipped to [0, theta_t]."""

        # distance along the ogive, clipped to the ogive piece
        ogive_arc = self.ogive_radius * self.tangency_angle
        distance_on_ogive = np.clip(s_arr - self.junction_arc_length, 0.0, ogive_arc)

        # convert to angle: theta_t at the junction, 0 at the base
        alpha = self.tangency_angle - distance_on_ogive / self.ogive_radius
        return alpha
