"""Tests for the spherically blunted tangent ogive profile (with and without a cylinder)."""

# --------------------------------------------------
# load necessary modules
# --------------------------------------------------
from __future__ import annotations

import math

import numpy as np
import pytest

from canonical_geometries import BluntedTangentOgive

# --------------------------------------------------
# test cases: a fineness-5 ogive with a 100 micron nose, with and without a cylinder
# --------------------------------------------------
NOSE_RADIUS = 100.0e-6
LENGTH = 0.5
BASE_RADIUS = 0.05
CYLINDER_LENGTH = 0.1

# ogive arc radius rho = (R^2 + L^2) / (2 R)
OGIVE_RADIUS = (BASE_RADIUS**2 + LENGTH**2) / (2.0 * BASE_RADIUS)

# small step either side of a junction for continuity checks
JUNCTION_STEP = 1.0e-12


@pytest.fixture
def ogive() -> BluntedTangentOgive:
    """Blunted tangent ogive without a cylinder."""
    return BluntedTangentOgive(nose_radius=NOSE_RADIUS, length=LENGTH, base_radius=BASE_RADIUS)


@pytest.fixture
def ogive_cylinder() -> BluntedTangentOgive:
    """The same ogive followed by a 0.1 m cylinder."""
    return BluntedTangentOgive(
        nose_radius=NOSE_RADIUS,
        length=LENGTH,
        base_radius=BASE_RADIUS,
        cylinder_length=CYLINDER_LENGTH,
    )


# --------------------------------------------------
# geometry against the sharp-ogive definition
# --------------------------------------------------
def test_ogive_radius_and_tangency_angle(ogive: BluntedTangentOgive) -> None:
    """rho = (R^2 + L^2) / (2 R) and cos(theta_t) = (rho - R) / (rho - r_n)."""

    # expected tangency angle
    theta_t = math.acos((OGIVE_RADIUS - BASE_RADIUS) / (OGIVE_RADIUS - NOSE_RADIUS))

    # check
    assert ogive.ogive_radius == pytest.approx(OGIVE_RADIUS, rel=1e-15)
    assert ogive.tangency_angle == pytest.approx(theta_t, rel=1e-14)
    assert ogive.junction_angle == pytest.approx(0.5 * math.pi - theta_t, rel=1e-14)


def test_nose_centre_matches_the_sharp_ogive_frame(ogive: BluntedTangentOgive) -> None:
    """In the sharp-tip frame the nose centre lies at L - sqrt((rho - r_n)^2 - (rho - R)^2)."""

    # nose centre in the sharp-tip frame (tip at X = 0, base at X = L)
    x_centre_sharp = LENGTH - math.sqrt(
        (OGIVE_RADIUS - NOSE_RADIUS) ** 2 - (OGIVE_RADIUS - BASE_RADIUS) ** 2
    )

    # the profile's nose centre is (r_n, 0); the sharp tip sits at sharp_tip_x
    x_centre_profile = NOSE_RADIUS - ogive.sharp_tip_x

    # check
    assert x_centre_profile == pytest.approx(x_centre_sharp, rel=1e-12)


def test_ogive_points_follow_the_sharp_ogive_formula(ogive: BluntedTangentOgive) -> None:
    """Ogive points satisfy y = sqrt(rho^2 - (X - L)^2) - (rho - R) in the sharp-tip frame."""

    # sample the ogive piece
    s = np.linspace(ogive.junction_arc_length, ogive.base_arc_length, 101)
    x, y = ogive.point(s)

    # sharp-tip frame and the sharp-ogive arc
    x_sharp = x - ogive.sharp_tip_x
    y_expected = np.sqrt(OGIVE_RADIUS**2 - (x_sharp - LENGTH) ** 2) - (OGIVE_RADIUS - BASE_RADIUS)

    # check
    np.testing.assert_allclose(y, y_expected, rtol=0.0, atol=1e-14)


def test_blunted_body_is_shorter_than_the_sharp_ogive(ogive: BluntedTangentOgive) -> None:
    """The base lies at (L - (stagnation point offset), R): blunting removes a bit of length."""

    # check
    x_base, y_base = ogive.base_point
    assert y_base == BASE_RADIUS
    assert x_base < LENGTH
    assert x_base - ogive.sharp_tip_x == pytest.approx(LENGTH, rel=1e-15)


def test_small_nose_approaches_the_sharp_ogive() -> None:
    """With a tiny nose, the tip offset vanishes and the length approaches the sharp arc."""

    # build with a 1 nm nose
    profile = BluntedTangentOgive(nose_radius=1.0e-9, length=LENGTH, base_radius=BASE_RADIUS)

    # sharp ogive arc: from the tip (angle asin(L / rho) from the vertical) to the base
    sharp_arc = OGIVE_RADIUS * math.asin(LENGTH / OGIVE_RADIUS)

    # check
    assert abs(profile.sharp_tip_x) < 1.0e-8
    assert profile.total_length == pytest.approx(sharp_arc, rel=1e-7)


# --------------------------------------------------
# pieces and junctions
# --------------------------------------------------
def test_nose_points_lie_on_the_circle(ogive: BluntedTangentOgive) -> None:
    """Every nose point is r_n from (r_n, 0); the stagnation point is the origin."""

    # sample the nose
    s = np.linspace(0.0, ogive.junction_arc_length, 51)
    x, y = ogive.point(s)

    # check
    np.testing.assert_allclose(np.hypot(x - NOSE_RADIUS, y), NOSE_RADIUS, rtol=1e-13)
    assert (x[0], y[0]) == (0.0, 0.0)


@pytest.mark.parametrize("junction", ["junction_arc_length", "base_arc_length"])
def test_point_and_tangent_continuous_at_junctions(
    ogive_cylinder: BluntedTangentOgive, junction: str
) -> None:
    """Position and slope are continuous at nose/ogive and at ogive/cylinder."""

    # evaluate just either side of the junction
    s_junction = getattr(ogive_cylinder, junction)
    s = np.array([s_junction - JUNCTION_STEP, s_junction + JUNCTION_STEP])
    x, y = ogive_cylinder.point(s)
    tx, ty = ogive_cylinder.tangent(s)

    # check: the two points are 2 steps apart along the wall (no gap), same direction
    distance = math.hypot(x[1] - x[0], y[1] - y[0])
    assert abs(distance - 2.0 * JUNCTION_STEP) < 1e-15
    assert abs(tx[1] - tx[0]) < 1e-6
    assert abs(ty[1] - ty[0]) < 1e-6


def test_junction_point_and_slope(ogive: BluntedTangentOgive) -> None:
    """The nose/ogive junction is the reported tangency point, with slope theta_t."""

    # evaluate at the junction
    x, y = ogive.point(ogive.junction_arc_length)
    tx, ty = ogive.tangent(ogive.junction_arc_length)

    # check
    x_j, y_j = ogive.junction_point
    assert float(x) == pytest.approx(x_j, rel=1e-14)
    assert float(y) == pytest.approx(y_j, rel=1e-14)
    assert math.atan2(float(ty), float(tx)) == pytest.approx(ogive.tangency_angle, rel=1e-12)


def test_base_is_tangent_to_the_cylinder(ogive: BluntedTangentOgive) -> None:
    """At the base the ogive is horizontal, at y = R."""

    # evaluate at the base (the end of the profile without a cylinder)
    x, y = ogive.point(ogive.total_length)
    tx, ty = ogive.tangent(ogive.total_length)

    # check
    assert (float(x), float(y)) == pytest.approx(ogive.base_point, rel=1e-14)
    assert (float(tx), float(ty)) == pytest.approx((1.0, 0.0), abs=1e-15)


def test_cylinder_end_and_total_length(ogive_cylinder: BluntedTangentOgive) -> None:
    """The cylinder runs at y = R for cylinder_length past the base."""

    # evaluate at the end
    x, y = ogive_cylinder.point(ogive_cylinder.total_length)

    # check
    x_base, _ = ogive_cylinder.base_point
    assert float(x) == pytest.approx(x_base + CYLINDER_LENGTH, rel=1e-14)
    assert float(y) == BASE_RADIUS
    assert ogive_cylinder.total_length == pytest.approx(
        ogive_cylinder.base_arc_length + CYLINDER_LENGTH, rel=1e-15
    )


def test_junctions_count_the_pieces(
    ogive: BluntedTangentOgive, ogive_cylinder: BluntedTangentOgive
) -> None:
    """One junction without a cylinder, two with one."""

    # check
    np.testing.assert_array_equal(ogive.junctions, [ogive.junction_arc_length])
    np.testing.assert_array_equal(
        ogive_cylinder.junctions,
        [ogive_cylinder.junction_arc_length, ogive_cylinder.base_arc_length],
    )


def test_curvature_per_piece(ogive_cylinder: BluntedTangentOgive) -> None:
    """Curvature is 1 / r_n on the nose, 1 / rho on the ogive and 0 on the cylinder."""

    # one point inside each piece
    s_j = ogive_cylinder.junction_arc_length
    s_b = ogive_cylinder.base_arc_length
    s = np.array([0.5 * s_j, 0.5 * (s_j + s_b), s_b + 0.5 * CYLINDER_LENGTH])

    # check
    kappa = ogive_cylinder.curvature(s)
    np.testing.assert_allclose(kappa, [1.0 / NOSE_RADIUS, 1.0 / OGIVE_RADIUS, 0.0], rtol=1e-15)


def test_normals_are_unit_perpendicular_and_outward(ogive_cylinder: BluntedTangentOgive) -> None:
    """Normals have unit length, are perpendicular to the tangent, and point into the flow."""

    # sample the whole profile
    s = np.linspace(0.0, ogive_cylinder.total_length, 401)
    tx, ty = ogive_cylinder.tangent(s)
    nx, ny = ogive_cylinder.normal(s)

    # check
    np.testing.assert_allclose(np.hypot(nx, ny), 1.0, rtol=1e-14)
    np.testing.assert_allclose(tx * nx + ty * ny, 0.0, atol=1e-15)
    assert np.all(ny[1:] > 0.0)


def test_methods_keep_the_shape_of_s(ogive_cylinder: BluntedTangentOgive) -> None:
    """Array input in, same-shape arrays out."""

    # 2 x 3 arc lengths across all three pieces
    s = np.linspace(0.0, ogive_cylinder.total_length, 6).reshape(2, 3)

    # check
    x, y = ogive_cylinder.point(s)
    nx, _ = ogive_cylinder.normal(s)
    assert x.shape == y.shape == nx.shape == ogive_cylinder.curvature(s).shape == (2, 3)


# --------------------------------------------------
# validation
# --------------------------------------------------
@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"nose_radius": 0.0}, "nose_radius must be positive"),
        ({"base_radius": -0.05}, "base_radius must be positive"),
        ({"cylinder_length": -0.1}, "cylinder_length must not be negative"),
        ({"length": 0.04}, "greater than base_radius"),
        ({"nose_radius": 0.05}, "smaller than base_radius"),
    ],
)
def test_invalid_inputs_rejected(kwargs: dict, message: str) -> None:
    """Each validation rule raises with a message naming the problem."""

    # defaults, with one value broken
    arguments = {"nose_radius": NOSE_RADIUS, "length": LENGTH, "base_radius": BASE_RADIUS}
    arguments.update(kwargs)

    with pytest.raises(ValueError, match=message):
        BluntedTangentOgive(**arguments)


def test_arc_length_outside_range_rejected(ogive: BluntedTangentOgive) -> None:
    """Arc lengths past the end are rejected."""

    with pytest.raises(ValueError, match="arc length must lie"):
        ogive.point(ogive.total_length * 1.001)
