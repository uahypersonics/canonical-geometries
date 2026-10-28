"""Shared callbacks for the geometry CLI."""

# --------------------------------------------------
# load necessary modules
# --------------------------------------------------
import typer

from canonical_geometries import __version__


# --------------------------------------------------
# callbacks
# --------------------------------------------------
def version_callback(value: bool) -> None:
    """Print the installed package version and exit."""

    if value:
        typer.echo(f"canonical-geometries {__version__}")
        raise typer.Exit()
