"""Per-geometry command groups: `geometry <type> init` and `geometry <type> run`."""

# --------------------------------------------------
# load necessary modules
# --------------------------------------------------
from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Annotated

import typer

from canonical_geometries.cli.templates import GEOMETRY_COMMANDS
from canonical_geometries.config import load_config
from canonical_geometries.moldline import sample_moldline
from canonical_geometries.writers import write_moldline


# --------------------------------------------------
# command group factory
# --------------------------------------------------
def build_geometry_app(geometry_type: str) -> typer.Typer:
    """Build the `init` / `run` command group for one geometry type.

    Every geometry gets the same two commands; only the template that `init` writes
    and the type `run` accepts differ. The commands below close over geometry_type.

    Args:
        geometry_type: Key in GEOMETRY_COMMANDS, e.g. "cone".

    Returns:
        Typer app to register as `geometry <geometry_type>`.
    """

    # command group
    geometry_app = typer.Typer(
        name=geometry_type,
        help=GEOMETRY_COMMANDS[geometry_type].help,
        no_args_is_help=True,
    )
    default_config = Path(f"{geometry_type}.toml")

    # init: write the starter configuration for this geometry
    @geometry_app.command("init")
    def cmd_init(
        output: Annotated[
            Path,
            typer.Option("--output", "-o", help="Configuration file to create."),
        ] = default_config,
        force: Annotated[
            bool,
            typer.Option("--force", "-f", help="Overwrite an existing configuration."),
        ] = False,
    ) -> None:
        """Create a starter configuration."""

        # protect existing user configuration unless overwrite was requested
        if output.exists() and not force:
            typer.echo(f"Error: {output} already exists. Use --force to overwrite.", err=True)
            raise typer.Exit(code=1)

        # write and validate the starter configuration
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(GEOMETRY_COMMANDS[geometry_type].template, encoding="utf-8")
        load_config(output, expected_type=geometry_type)

        typer.echo(f"Created: {output}")
        typer.echo(f"Edit the file, then run: geometry {geometry_type} run {output}")

    # run: build the profile from a configuration and write its moldline
    @geometry_app.command("run")
    def cmd_run(
        config: Annotated[
            Path,
            typer.Argument(help="Configuration file."),
        ] = default_config,
    ) -> None:
        """Generate the moldline from a configuration."""

        try:
            # read and validate (pydantic's ValidationError is a ValueError)
            geometry_config = load_config(config, expected_type=geometry_type)

            # build the profile and sample it
            profile = geometry_config.geometry.build()
            points_per_piece = [
                geometry_config.points.n_nose,
                geometry_config.points.n_body,
            ]
            moldline = sample_moldline(profile, points_per_piece)

            # write
            output_path = write_moldline(moldline, geometry_config.output.file)
        except (OSError, ValueError, tomllib.TOMLDecodeError) as error:
            typer.echo(f"Error: {error}", err=True)
            raise typer.Exit(code=1) from None

        # report
        typer.echo(f"Generated {geometry_type} moldline: {moldline.s.size} points")
        typer.echo(f"Wrote: {output_path}")

    return geometry_app
