"""Tests for the blunted wedge profile (blunted plate at zero half-angle)."""

# --------------------------------------------------
# load necessary modules
# --------------------------------------------------
from __future__ import annotations

import math

import numpy as np
import pytest

import canonical_geometries
from canonical_geometries import BluntedWedge

# --------------------------------------------------
# test cases: the flat-plate plan's geometry, and a 7 deg wedge / sphere-cone meridian
# --------------------------------------------------
NOSE_RADIUS = 100.0e-6
LENGTH = 0.5
HALF_ANGLE = 7.0

# small step either side of the junction for continuity checks
JUNCTION_STEP = 1.0e-12


@pytest.fixture
def plate() -> BluntedWedge:
    """Blunted plate: r_n = 100 um, L = 0.5 m, zero half-angle."""
    return BluntedWedge(nose_radius=NOSE_RADIUS, length=LENGTH)


@pytest.fixture
def wedge() -> BluntedWedge:
    """Blunted 7 deg wedge: r_n = 100 um, L = 0.5 m."""
    return BluntedWedge(nose_radius=NOSE_RADIUS, length=LENGTH, half_angle=HALF_ANGLE)


# --------------------------------------------------
# package
# --------------------------------------------------
def test_package_exposes_version() -> None:
    """Expose package version metadata from the top-level package."""

    # validate version attribute
    assert isinstance(canonical_geometries.__version__, str)
    assert canonical_geometries.__version__


# --------------------------------------------------
# blunted plate (half_angle = 0)
# --------------------------------------------------
def test_plate_total_length(plate: BluntedWedge) -> None:
    """Total arc length is the quarter circle plus the flat part."""

    # build expected value
    expected = 0.5 * math.pi * NOSE_RADIUS + (LENGTH - NOSE_RADIUS)

    # check
    assert plate.total_length == pytest.approx(expected, rel=1e-15)


def test_plate_junction_is_the_quarter_circle(plate: BluntedWedge) -> None:
    """The only junction (nose meets plate) is at s = pi r_n / 2, a quarter circle."""

    # check
    np.testing.assert_allclose(plate.junctions, [0.5 * math.pi * NOSE_RADIUS])


def test_plate_end_points(plate: BluntedWedge) -> None:
    """s = 0 is the stagnation point; s = total_length is (L, r_n)."""

    # evaluate both ends
    x_start, y_start = plate.point(0.0)
    x_end, y_end = plate.point(plate.total_length)

    # check
    assert x_start == pytest.approx(0.0, abs=1e-18)
    assert y_start == pytest.approx(0.0, abs=1e-18)
    assert x_end == pytest.approx(LENGTH, rel=1e-14)
    assert y_end == pytest.approx(NOSE_RADIUS, rel=1e-14)


def test_plate_normals_point_into_the_flow(plate: BluntedWedge) -> None:
    """Normal is upstream at the stagnation point and +y on the plate."""

    # stagnation point and plate
    nx_stag, ny_stag = plate.normal(0.0)
    nx_plate, ny_plate = plate.normal(0.5 * plate.total_length)

    # check
    np.testing.assert_allclose([nx_stag, ny_stag], [-1.0, 0.0], atol=1e-15)
    np.testing.assert_allclose([nx_plate, ny_plate], [0.0, 1.0], atol=1e-15)


# --------------------------------------------------
# blunted wedge (half_angle = 7 deg)
# --------------------------------------------------
def test_wedge_junction_is_the_tangency_point(wedge: BluntedWedge) -> None:
    """The nose arc ends at polar angle 90 - theta, at (r_n (1 - sin theta), r_n cos theta)."""

    # build expected values
    theta = math.radians(HALF_ANGLE)
    phi_junction = 0.5 * math.pi - theta
    x_expected = NOSE_RADIUS * (1.0 - math.sin(theta))
    y_expected = NOSE_RADIUS * math.cos(theta)

    # evaluate at the junction
    x_j, y_j = wedge.point(wedge.junction_arc_length)

    # check
    assert wedge.junction_angle == pytest.approx(phi_junction, rel=1e-15)
    assert wedge.junction_arc_length == pytest.approx(NOSE_RADIUS * phi_junction, rel=1e-15)
    assert x_j == pytest.approx(x_expected, rel=1e-14)
    assert y_j == pytest.approx(y_expected, rel=1e-14)


def test_wedge_tangent_matches_the_body_at_junction(wedge: BluntedWedge) -> None:
    """Either side of the junction the tangent is (cos theta, sin theta): slope-continuous."""

    # evaluate just before and just after the junction
    s_j = wedge.junction_arc_length
    s_pair = np.array([s_j - JUNCTION_STEP, s_j + JUNCTION_STEP])
    tx, ty = wedge.tangent(s_pair)

    # check against the body direction
    theta = math.radians(HALF_ANGLE)
    np.testing.assert_allclose(tx, math.cos(theta), atol=1e-6)
    np.testing.assert_allclose(ty, math.sin(theta), atol=1e-6)


def test_wedge_end_point_and_length(wedge: BluntedWedge) -> None:
    """The body ends at x = L, and the total length is the arc plus the slanted body."""

    # build expected values
    theta = math.radians(HALF_ANGLE)
    x_j = NOSE_RADIUS * (1.0 - math.sin(theta))
    y_j = NOSE_RADIUS * math.cos(theta)
    body_length = (LENGTH - x_j) / math.cos(theta)
    expected_total = NOSE_RADIUS * (0.5 * math.pi - theta) + body_length
    expected_y_end = y_j + body_length * math.sin(theta)

    # evaluate the end point
    x_end, y_end = wedge.point(wedge.total_length)

    # check
    assert wedge.total_length == pytest.approx(expected_total, rel=1e-14)
    assert x_end == pytest.approx(LENGTH, rel=1e-14)
    assert y_end == pytest.approx(expected_y_end, rel=1e-14)


def test_wedge_body_points_lie_on_the_body_line(wedge: BluntedWedge) -> None:
    """Body points lie on the line through the junction at the half-angle."""

    # sample the body
    s_body = np.linspace(wedge.junction_arc_length, wedge.total_length, 50)
    x, y = wedge.point(s_body)

    # check: perpendicular distance to the body line is zero
    theta = math.radians(HALF_ANGLE)
    x_j, y_j = wedge.junction_point
    distance = -(x - x_j) * math.sin(theta) + (y - y_j) * math.cos(theta)
    np.testing.assert_allclose(distance, 0.0, atol=1e-15)


# --------------------------------------------------
# both geometries
# --------------------------------------------------
@pytest.mark.parametrize("half_angle", [0.0, HALF_ANGLE])
def test_nose_points_lie_on_the_circle(half_angle: float) -> None:
    """Every nose point is r_n away from the nose centre (r_n, 0)."""

    # sample the nose
    profile = BluntedWedge(nose_radius=NOSE_RADIUS, length=LENGTH, half_angle=half_angle)
    s_nose = np.linspace(0.0, profile.junction_arc_length, 50)
    x, y = profile.point(s_nose)

    # check distance to the centre
    radius = np.hypot(x - NOSE_RADIUS, y)
    np.testing.assert_allclose(radius, NOSE_RADIUS, rtol=1e-12)


@pytest.mark.parametrize("half_angle", [0.0, HALF_ANGLE])
def test_point_continuous_at_junction(half_angle: float) -> None:
    """Points on both sides of the junction meet."""

    # evaluate just before and just after the junction
    profile = BluntedWedge(nose_radius=NOSE_RADIUS, length=LENGTH, half_angle=half_angle)
    s_j = profile.junction_arc_length
    s_pair = np.array([s_j - JUNCTION_STEP, s_j + JUNCTION_STEP])
    x, y = profile.point(s_pair)

    # check (gap no larger than the step)
    assert math.hypot(x[1] - x[0], y[1] - y[0]) <= 3.0 * JUNCTION_STEP


@pytest.mark.parametrize("half_angle", [0.0, HALF_ANGLE])
def test_normals_are_unit_perpendicular_and_radial_on_nose(half_angle: float) -> None:
    """Normals are unit, perpendicular to tangents, and radial on the nose."""

    # sample both pieces
    profile = BluntedWedge(nose_radius=NOSE_RADIUS, length=LENGTH, half_angle=half_angle)
    s_all = np.linspace(0.0, profile.total_length, 2001)
    tx, ty = profile.tangent(s_all)
    nx, ny = profile.normal(s_all)

    # check unit length and orthogonality
    np.testing.assert_allclose(np.hypot(tx, ty), 1.0, rtol=1e-14)
    np.testing.assert_allclose(np.hypot(nx, ny), 1.0, rtol=1e-14)
    np.testing.assert_allclose(tx * nx + ty * ny, 0.0, atol=1e-14)

    # nose: normal points radially outward from the nose centre
    s_nose = np.linspace(0.0, profile.junction_arc_length, 20)
    x, y = profile.point(s_nose)
    nx_nose, ny_nose = profile.normal(s_nose)
    np.testing.assert_allclose(nx_nose, (x - NOSE_RADIUS) / NOSE_RADIUS, atol=1e-12)
    np.testing.assert_allclose(ny_nose, y / NOSE_RADIUS, atol=1e-12)


@pytest.mark.parametrize("half_angle", [0.0, HALF_ANGLE])
def test_curvature_jumps_at_junction(half_angle: float) -> None:
    """Curvature is 1/r_n on the nose (including the junction) and 0 on the body."""

    # evaluate on the nose, at the junction and on the body
    profile = BluntedWedge(nose_radius=NOSE_RADIUS, length=LENGTH, half_angle=half_angle)
    s_j = profile.junction_arc_length
    s_check = np.array([0.0, 0.5 * s_j, s_j, s_j + 1.0e-9, profile.total_length])
    kappa = profile.curvature(s_check)

    # check
    expected = [1.0 / NOSE_RADIUS, 1.0 / NOSE_RADIUS, 1.0 / NOSE_RADIUS, 0.0, 0.0]
    np.testing.assert_allclose(kappa, expected)


def test_methods_keep_the_shape_of_s(wedge: BluntedWedge) -> None:
    """Vectorized methods return arrays with the shape of the input."""

    # 2D array input
    s_grid = np.linspace(0.0, wedge.total_length, 12).reshape(3, 4)
    x, y = wedge.point(s_grid)
    nx, ny = wedge.normal(s_grid)
    kappa = wedge.curvature(s_grid)

    # check shapes
    assert x.shape == y.shape == nx.shape == ny.shape == kappa.shape == (3, 4)


# --------------------------------------------------
# input validation
# --------------------------------------------------
@pytest.mark.parametrize("nose_radius", [0.0, -1.0e-6])
def test_non_positive_nose_radius_rejected(nose_radius: float) -> None:
    """Nose radius must be positive."""

    with pytest.raises(ValueError, match="nose_radius"):
        BluntedWedge(nose_radius=nose_radius, length=LENGTH)


@pytest.mark.parametrize("half_angle", [-1.0, 90.0, 120.0])
def test_half_angle_outside_range_rejected(half_angle: float) -> None:
    """Half-angle must lie in [0, 90) deg."""

    with pytest.raises(ValueError, match="half_angle"):
        BluntedWedge(nose_radius=NOSE_RADIUS, length=LENGTH, half_angle=half_angle)


@pytest.mark.parametrize(
    ("half_angle", "length"),
    [(0.0, NOSE_RADIUS), (0.0, 0.5 * NOSE_RADIUS), (HALF_ANGLE, 0.5 * NOSE_RADIUS)],
)
def test_length_not_beyond_junction_rejected(half_angle: float, length: float) -> None:
    """The axial length must extend past the junction."""

    with pytest.raises(ValueError, match="length"):
        BluntedWedge(nose_radius=NOSE_RADIUS, length=length, half_angle=half_angle)


@pytest.mark.parametrize("s_offset", [-1.0e-6, 1.0e-6])
def test_arc_length_outside_range_rejected(plate: BluntedWedge, s_offset: float) -> None:
    """Arc lengths outside [0, total_length] raise."""

    # build an s just outside either end
    if s_offset < 0.0:
        s_bad = s_offset
    else:
        s_bad = plate.total_length + s_offset

    with pytest.raises(ValueError, match="arc length"):
        plate.point(s_bad)


def test_round_off_at_the_ends_accepted(plate: BluntedWedge) -> None:
    """Round-off just past the ends (as from np.linspace) is clipped, not rejected."""

    # tiny overshoot at both ends
    s_edge = np.array([-1.0e-18, plate.total_length * (1.0 + 1.0e-14)])
    x, _ = plate.point(s_edge)

    # check clipped onto the end points
    np.testing.assert_allclose(x, [0.0, LENGTH], atol=1e-18, rtol=1e-14)
