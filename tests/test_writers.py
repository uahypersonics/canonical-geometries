"""Tests for the moldline writers (CSV, Tecplot ASCII) and the extension dispatcher."""

# --------------------------------------------------
# load necessary modules
# --------------------------------------------------
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from canonical_geometries import BluntedWedge, Moldline, sample_moldline, write_moldline
from canonical_geometries.writers import COLUMN_NAMES, write_csv, write_tecplot_ascii

# --------------------------------------------------
# test case: 7 deg blunted wedge
# --------------------------------------------------
EXPECTED_COLUMNS = ("x [m]", "y [m]", "z [m]", "s [m]", "nx", "ny", "nz", "curvature [1/m]")


@pytest.fixture
def moldline() -> Moldline:
    """Moldline of a 7 deg wedge with r_n = 100 um, L = 10 mm."""
    wedge = BluntedWedge(nose_radius=100.0e-6, length=0.01, half_angle=7.0)
    return sample_moldline(wedge, [84, 20])


def check_table(table: np.ndarray, moldline: Moldline) -> None:
    """Check a read-back table holds the moldline in COLUMN_NAMES order."""

    # check shape
    assert table.shape == (moldline.s.size, len(EXPECTED_COLUMNS))

    # check values: x, y, z = 0, s, normals with nz = 0, curvature
    np.testing.assert_allclose(table[:, 0], moldline.x, rtol=1e-15)
    np.testing.assert_allclose(table[:, 1], moldline.y, rtol=1e-15)
    np.testing.assert_array_equal(table[:, 2], 0.0)
    np.testing.assert_allclose(table[:, 3], moldline.s, rtol=1e-15)
    np.testing.assert_allclose(table[:, 4], moldline.nx, rtol=1e-15)
    np.testing.assert_allclose(table[:, 5], moldline.ny, rtol=1e-15)
    np.testing.assert_array_equal(table[:, 6], 0.0)
    np.testing.assert_allclose(table[:, 7], moldline.curvature, rtol=1e-15)


# --------------------------------------------------
# column layout
# --------------------------------------------------
def test_coordinates_come_first() -> None:
    """x and y are columns 0 and 1, so positional readers and Tecplot's axes get them right."""

    # check
    assert COLUMN_NAMES == EXPECTED_COLUMNS


# --------------------------------------------------
# CSV
# --------------------------------------------------
def test_csv_round_trip(moldline: Moldline, tmp_path: Path) -> None:
    """The CSV has one header line with units and reads back to the same values."""

    # write
    csv_path = write_csv(moldline, tmp_path / "out" / "moldline.csv")

    # read back
    header = csv_path.read_text().splitlines()[0]
    table = np.loadtxt(csv_path, delimiter=",", skiprows=1)

    # check
    assert header == ",".join(EXPECTED_COLUMNS)
    check_table(table, moldline)


# --------------------------------------------------
# Tecplot ASCII
# --------------------------------------------------
def test_tecplot_header(moldline: Moldline, tmp_path: Path) -> None:
    """The .dat file has TITLE, quoted VARIABLES and a POINT zone sized to the moldline."""

    # write
    dat_path = write_tecplot_ascii(moldline, tmp_path / "moldline.dat")
    lines = dat_path.read_text().splitlines()

    # check the three header lines
    expected_variables = ", ".join(f'"{name}"' for name in EXPECTED_COLUMNS)
    assert lines[0] == 'TITLE = "moldline"'
    assert lines[1] == f"VARIABLES = {expected_variables}"
    assert lines[2] == f'ZONE T="moldline", I={moldline.s.size}, J=1, K=1, F=POINT'


def test_tecplot_round_trip(moldline: Moldline, tmp_path: Path) -> None:
    """The .dat data block reads back to the same values."""

    # write and read the data after the three header lines
    dat_path = write_tecplot_ascii(moldline, tmp_path / "moldline.dat")
    table = np.loadtxt(dat_path, skiprows=3)

    # check
    check_table(table, moldline)


# --------------------------------------------------
# dispatcher
# --------------------------------------------------
@pytest.mark.parametrize(
    ("file_name", "first_line"),
    [
        ("moldline.csv", "x [m],y [m]"),
        ("moldline.dat", 'TITLE = "moldline"'),
        ("MOLDLINE.DAT", 'TITLE = "moldline"'),
    ],
)
def test_extension_picks_the_format(
    moldline: Moldline, tmp_path: Path, file_name: str, first_line: str
) -> None:
    """write_moldline picks the writer from the extension, ignoring case."""

    # write through the dispatcher
    written = write_moldline(moldline, tmp_path / file_name)

    # check
    assert written.read_text().startswith(first_line)


def test_unknown_extension_rejected(moldline: Moldline, tmp_path: Path) -> None:
    """An extension without a writer raises and lists the supported ones."""

    with pytest.raises(ValueError, match=r"\.csv, \.dat"):
        write_moldline(moldline, tmp_path / "moldline.txt")
