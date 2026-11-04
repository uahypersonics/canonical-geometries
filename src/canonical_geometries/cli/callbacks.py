"""Shared callbacks for the geometry CLI."""

# --------------------------------------------------
# load necessary modules
# --------------------------------------------------
import logging

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


# --------------------------------------------------
# verbose callback
# --------------------------------------------------
def verbose_callback(value: bool) -> None:
    """Configure console logging; --verbose adds debug output from this tool.

    By default only warnings are shown. With --verbose, this package logs at
    debug level, while other packages stay quiet.
    """

    # default console logging for every logger: warnings only
    logging.basicConfig(level=logging.WARNING, format="%(levelname)-8s %(message)s")

    # debug output from this tool only; the packages it calls keep their levels
    if value:
        logging.getLogger("canonical_geometries").setLevel(logging.DEBUG)
