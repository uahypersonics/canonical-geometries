"""End-to-end tests for the geometry CLI: `geometry <type> init` and `geometry <type> run`."""

# --------------------------------------------------
# load necessary modules
# --------------------------------------------------
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pytest
from typer.testing import CliRunner

from canonical_geometries.cli import app
from canonical_geometries.cli.cmd_geometry import GEOMETRY_HELP
from canonical_geometries.config import GEOMETRY_TEMPLATES

runner = CliRunner()

# a short 7 deg cone configuration
CONE_CONFIG = """\
[geometry]
type = "cone"
nose_radius = 100.0e-6
length = 0.01
half_angle = 7.0

[points]
n_nose = 84
n_body = 20

[output]
file = "cone.csv"
"""


# --------------------------------------------------
# command layout
# --------------------------------------------------
def test_help_lists_every_geometry() -> None:
    """`geometry --help` lists one subcommand per registered geometry type."""

    # run
    result = runner.invoke(app, ["--help"])

    # check
    assert result.exit_code == 0
    for geometry_type in GEOMETRY_HELP:
        assert geometry_type in result.output


def test_every_command_has_a_template() -> None:
    """The CLI's help registry and the config's template registry list the same geometry types."""

    # check
    assert set(GEOMETRY_HELP) == set(GEOMETRY_TEMPLATES)


def test_version_flag() -> None:
    """--version prints the package version."""

    # run
    result = runner.invoke(app, ["--version"])

    # check
    assert result.exit_code == 0
    assert result.output.startswith("canonical-geometries ")


# --------------------------------------------------
# init
# --------------------------------------------------
@pytest.mark.parametrize("geometry_type", list(GEOMETRY_HELP))
def test_init_writes_the_geometry_contract(geometry_type: str, tmp_path: Path) -> None:
    """Each init writes <type>.toml with that geometry's type, and it validates."""

    # run in a temporary folder so the default file name is used
    config_path = tmp_path / f"{geometry_type}.toml"
    result = runner.invoke(app, [geometry_type, "init", "--output", str(config_path)])

    # check
    assert result.exit_code == 0, result.output
    assert f'type = "{geometry_type}"' in config_path.read_text()
    assert f"geometry {geometry_type} run" in result.output


def test_plate_contract_has_no_half_angle(tmp_path: Path) -> None:
    """The plate template only asks for what a plate needs."""

    # run
    config_path = tmp_path / "plate.toml"
    runner.invoke(app, ["plate", "init", "--output", str(config_path)])

    # check
    assert "half_angle" not in config_path.read_text()


def test_init_refuses_to_overwrite(tmp_path: Path) -> None:
    """init leaves an existing file alone unless --force is given."""

    # existing user file
    config_path = tmp_path / "cone.toml"
    config_path.write_text("# mine\n")

    # run without and with --force
    result_keep = runner.invoke(app, ["cone", "init", "--output", str(config_path)])
    content_after_keep = config_path.read_text()
    result_force = runner.invoke(app, ["cone", "init", "--output", str(config_path), "--force"])

    # check
    assert result_keep.exit_code == 1
    assert content_after_keep == "# mine\n"
    assert result_force.exit_code == 0
    assert 'type = "cone"' in config_path.read_text()


# --------------------------------------------------
# run
# --------------------------------------------------
@pytest.mark.parametrize(
    ("geometry_type", "n_points"),
    [
        ("plate", 91 + 200 - 1),
        ("wedge", 84 + 200 - 1),
        ("cone", 84 + 200 - 1),
        ("tangent-ogive", 80 + 200 - 1),
    ],
)
def test_init_then_run_writes_csv(geometry_type: str, n_points: int, tmp_path: Path) -> None:
    """Each template runs as-is and writes <type>.csv next to the config."""

    # init, then run
    config_path = tmp_path / f"{geometry_type}.toml"
    runner.invoke(app, [geometry_type, "init", "--output", str(config_path)])
    result = runner.invoke(app, [geometry_type, "run", str(config_path)])

    # check
    assert result.exit_code == 0, result.output
    table = np.loadtxt(tmp_path / f"{geometry_type}.csv", delimiter=",", skiprows=1)
    assert table.shape == (n_points, 8)


def test_run_cone_ends_on_the_cone_surface(tmp_path: Path) -> None:
    """The cone moldline ends at x = L on the 7 deg cone surface."""

    # write config and run
    config_path = tmp_path / "cone.toml"
    config_path.write_text(CONE_CONFIG)
    result = runner.invoke(app, ["cone", "run", str(config_path)])

    # check: last point at x = L, on the line from the junction at 7 deg
    assert result.exit_code == 0, result.output
    table = np.loadtxt(tmp_path / "cone.csv", delimiter=",", skiprows=1)
    theta = math.radians(7.0)
    x_j = 100.0e-6 * (1.0 - math.sin(theta))
    y_j = 100.0e-6 * math.cos(theta)
    y_end_expected = y_j + (0.01 - x_j) * math.tan(theta)
    assert table.shape == (84 + 20 - 1, 8)
    assert table[-1, 0] == pytest.approx(0.01, rel=1e-14)
    assert table[-1, 1] == pytest.approx(y_end_expected, rel=1e-13)


def test_run_tangent_ogive_with_cylinder(tmp_path: Path) -> None:
    """A cylinder adds a third piece: n_cylinder more points, ending at x_base + cylinder_length."""

    # init, then switch the cylinder on
    config_path = tmp_path / "tangent-ogive.toml"
    runner.invoke(app, ["tangent-ogive", "init", "--output", str(config_path)])
    config_text = config_path.read_text()
    config_text = config_text.replace("cylinder_length = 0.0", "cylinder_length = 0.1")
    config_text = config_text.replace("# n_cylinder = 50", "n_cylinder = 50")
    config_path.write_text(config_text)

    # run
    result = runner.invoke(app, ["tangent-ogive", "run", str(config_path)])

    # check: three pieces share two junction points; the last point is on the cylinder
    assert result.exit_code == 0, result.output
    table = np.loadtxt(tmp_path / "tangent-ogive.csv", delimiter=",", skiprows=1)
    assert table.shape == (80 + 200 + 50 - 2, 8)
    assert table[-1, 1] == pytest.approx(0.05, rel=1e-14)
    np.testing.assert_allclose(table[-50:, 1], 0.05, rtol=1e-14)


@pytest.mark.parametrize(
    ("old", "new", "expected_text"),
    [
        ("cylinder_length = 0.0", "cylinder_length = 0.1", "n_cylinder is needed"),
        ("# n_cylinder = 50", "n_cylinder = 50", "only for geometries with a cylinder"),
    ],
)
def test_run_tangent_ogive_checks_the_cylinder_points(
    tmp_path: Path, old: str, new: str, expected_text: str
) -> None:
    """n_cylinder is required with a cylinder and rejected without one."""

    # init, then break the cylinder/points pairing
    config_path = tmp_path / "tangent-ogive.toml"
    runner.invoke(app, ["tangent-ogive", "init", "--output", str(config_path)])
    config_path.write_text(config_path.read_text().replace(old, new))

    # run
    result = runner.invoke(app, ["tangent-ogive", "run", str(config_path)])

    # check
    assert result.exit_code == 1
    assert expected_text in result.output


def test_run_rejects_a_config_for_another_geometry(tmp_path: Path) -> None:
    """A cone config given to `geometry wedge run` fails and names the right command."""

    # write config and run with the wrong command
    config_path = tmp_path / "cone.toml"
    config_path.write_text(CONE_CONFIG)
    result = runner.invoke(app, ["wedge", "run", str(config_path)])

    # check
    assert result.exit_code == 1
    assert "geometry cone run" in result.output


@pytest.mark.parametrize(
    ("bad_line", "expected_text"),
    [
        ("half_angel = 7.0", "half_angel"),
        ("half_angle = 95.0", "half_angle"),
    ],
)
def test_run_rejects_bad_config(tmp_path: Path, bad_line: str, expected_text: str) -> None:
    """Misspelled keys and out-of-range values fail with a message naming the key."""

    # break the half_angle line
    config_text = CONE_CONFIG.replace("half_angle = 7.0", bad_line)
    config_path = tmp_path / "bad.toml"
    config_path.write_text(config_text)

    # run
    result = runner.invoke(app, ["cone", "run", str(config_path)])

    # check
    assert result.exit_code == 1
    assert expected_text in result.output


def test_plate_rejects_half_angle(tmp_path: Path) -> None:
    """The plate contract has no half_angle; giving one is an error."""

    # plate config with a stray half_angle
    config_text = CONE_CONFIG.replace('type = "cone"', 'type = "plate"')
    config_path = tmp_path / "plate.toml"
    config_path.write_text(config_text)

    # run
    result = runner.invoke(app, ["plate", "run", str(config_path)])

    # check
    assert result.exit_code == 1
    assert "half_angle" in result.output


def test_run_writes_tecplot_for_dat(tmp_path: Path) -> None:
    """file = "cone.dat" writes a Tecplot ASCII file instead of CSV."""

    # point the output at a .dat file and run
    config_text = CONE_CONFIG.replace('file = "cone.csv"', 'file = "cone.dat"')
    config_path = tmp_path / "cone.toml"
    config_path.write_text(config_text)
    result = runner.invoke(app, ["cone", "run", str(config_path)])

    # check
    assert result.exit_code == 0, result.output
    lines = (tmp_path / "cone.dat").read_text().splitlines()
    assert lines[0] == 'TITLE = "moldline"'
    assert "I=103" in lines[2]


def test_run_rejects_unsupported_extension(tmp_path: Path) -> None:
    """An output extension without a writer fails when the config is read."""

    # point the output at a .txt file and run
    config_text = CONE_CONFIG.replace('file = "cone.csv"', 'file = "cone.txt"')
    config_path = tmp_path / "cone.toml"
    config_path.write_text(config_text)
    result = runner.invoke(app, ["cone", "run", str(config_path)])

    # check: error names the extension, and nothing was written
    assert result.exit_code == 1
    assert ".txt" in result.output
    assert not (tmp_path / "cone.txt").exists()


def test_run_missing_config_fails_cleanly(tmp_path: Path) -> None:
    """A missing config file exits with an error message, not a traceback."""

    # run
    result = runner.invoke(app, ["cone", "run", str(tmp_path / "missing.toml")])

    # check
    assert result.exit_code == 1
    assert "Error" in result.output
