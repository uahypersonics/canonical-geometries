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

# loggers that --verbose switches to debug: this tool and the uahypersonics
# packages it calls
DEBUG_LOGGERS = ("canonical_geometries",)


def verbose_callback(value: bool) -> None:
    """Configure console logging; --verbose adds debug output from our own packages.

    By default only warnings are shown. With --verbose, this package logs at
    debug level, while third-party libraries stay quiet.
    """

    # default console logging for every logger: warnings only
    logging.basicConfig(level=logging.WARNING, format="%(levelname)-8s %(message)s")

    # debug output from this tool and the uahypersonics packages it calls
    if value:
        for logger_name in DEBUG_LOGGERS:
            logging.getLogger(logger_name).setLevel(logging.DEBUG)
