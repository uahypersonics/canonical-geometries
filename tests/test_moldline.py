"""Tests for moldline sampling."""

# --------------------------------------------------
# load necessary modules
# --------------------------------------------------
from __future__ import annotations

import math

import numpy as np
import pytest

from canonical_geometries import BluntedWedge, sample_moldline

# --------------------------------------------------
# test case: 7 deg blunted wedge
# --------------------------------------------------
NOSE_RADIUS = 100.0e-6
LENGTH = 0.5
HALF_ANGLE = 7.0
N_NOSE = 84
N_BODY = 50


@pytest.fixture
def wedge() -> BluntedWedge:
    """Blunted 7 deg wedge: r_n = 100 um, L = 0.5 m."""
    return BluntedWedge(nose_radius=NOSE_RADIUS, length=LENGTH, half_angle=HALF_ANGLE)


# --------------------------------------------------
# sampling
# --------------------------------------------------
def test_point_count_shares_the_junction(wedge: BluntedWedge) -> None:
    """Nose and body share the junction point: n_nose + n_body - 1 points."""

    # sample
    moldline = sample_moldline(wedge, [N_NOSE, N_BODY])

    # check
    assert moldline.s.size == N_NOSE + N_BODY - 1
    assert moldline.s[0] == 0.0
    assert moldline.s[-1] == pytest.approx(wedge.total_length, rel=1e-15)


def test_junction_is_a_sample_point(wedge: BluntedWedge) -> None:
    """The tangency point is sampled exactly, as the last nose point."""

    # sample
    moldline = sample_moldline(wedge, [N_NOSE, N_BODY])

    # check
    junction_index = N_NOSE - 1
    x_j, y_j = wedge.junction_point
    assert moldline.s[junction_index] == pytest.approx(wedge.junction_arc_length, rel=1e-15)
    assert moldline.x[junction_index] == pytest.approx(x_j, rel=1e-14)
    assert moldline.y[junction_index] == pytest.approx(y_j, rel=1e-14)


def test_nose_points_equally_spaced_in_angle(wedge: BluntedWedge) -> None:
    """On the nose, polar angles step evenly from 0 to 90 - theta."""

    # sample and compute the polar angle of each nose point about (r_n, 0)
    moldline = sample_moldline(wedge, [N_NOSE, N_BODY])
    x_nose = moldline.x[:N_NOSE]
    y_nose = moldline.y[:N_NOSE]
    phi = np.arctan2(y_nose, NOSE_RADIUS - x_nose)

    # check
    phi_expected = np.linspace(0.0, 0.5 * math.pi - math.radians(HALF_ANGLE), N_NOSE)
    np.testing.assert_allclose(phi, phi_expected, atol=1e-12)


def test_wrong_number_of_counts_rejected(wedge: BluntedWedge) -> None:
    """One count per piece is required."""

    with pytest.raises(ValueError, match="pieces"):
        sample_moldline(wedge, [N_NOSE])


def test_count_below_two_rejected(wedge: BluntedWedge) -> None:
    """Each piece needs at least its two end points."""

    with pytest.raises(ValueError, match="at least 2"):
        sample_moldline(wedge, [N_NOSE, 1])
