"""Root application for the geometry CLI."""

# --------------------------------------------------
# load necessary modules
# --------------------------------------------------
from typing import Annotated

import typer

from canonical_geometries.cli.callbacks import version_callback
from canonical_geometries.cli.cmd_geometry import GEOMETRY_HELP, build_geometry_app

# --------------------------------------------------
# root application
# --------------------------------------------------
app = typer.Typer(
    name="geometry",
    help="Generate moldlines of canonical test geometries.",
    no_args_is_help=True,
    add_completion=False,
)


# --------------------------------------------------
# register callbacks
# --------------------------------------------------
@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-V",
            callback=version_callback,
            is_eager=True,
            help="Show version and exit.",
        ),
    ] = False,
) -> None:
    """Generate moldlines of canonical test geometries."""

    del version


# --------------------------------------------------
# register one command group per geometry type: geometry <type> init / run
# --------------------------------------------------
for geometry_type in GEOMETRY_HELP:
    app.add_typer(build_geometry_app(geometry_type), name=geometry_type)
