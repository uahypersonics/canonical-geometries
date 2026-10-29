"""Moldline configuration file: parse and validate the TOML, build the profile.

The file holds a [geometry] table (the shared contract in config.geometry), the
[points] per profile piece, and the [output] file.
"""

# --------------------------------------------------
# load necessary modules
# --------------------------------------------------
from __future__ import annotations

import tomllib
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from canonical_geometries.config.geometry import GeometryConfig
from canonical_geometries.writers import WRITERS


# --------------------------------------------------
# [points] and [output]
# --------------------------------------------------
class PointsConfig(BaseModel):
    """Points per profile piece, each count including both ends of its piece."""

    # reject misspelled keys
    model_config = ConfigDict(extra="forbid")

    n_nose: int = Field(default=91, ge=2, description="Points on the nose arc")
    n_body: int = Field(default=200, ge=2, description="Points on the body")
    n_cylinder: int | None = Field(
        default=None, ge=2, description="Points on the cylinder (geometries with a cylinder only)"
    )


class OutputConfig(BaseModel):
    """Output file; a relative path is resolved against the config file's folder."""

    # reject misspelled keys
    model_config = ConfigDict(extra="forbid")

    file: Path = Field(
        default=Path("moldline.csv"),
        description="Moldline file; the extension picks the format (.csv, .dat)",
    )

    @field_validator("file")
    @classmethod
    def _check_extension(cls, file: Path) -> Path:
        """Reject extensions without a writer, so the error comes before any work."""

        # check against the writer registry
        extension = file.suffix.lower()
        if extension not in WRITERS:
            supported = ", ".join(WRITERS)
            raise ValueError(f"no moldline writer for '{file.suffix}'; supported: {supported}")

        return file


# --------------------------------------------------
# whole file
# --------------------------------------------------
class GeometryFileConfig(BaseModel):
    """Contents of a geometry TOML file."""

    # reject unknown sections
    model_config = ConfigDict(extra="forbid")

    geometry: GeometryConfig
    points: PointsConfig = Field(default_factory=PointsConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)

    @model_validator(mode="after")
    def _check_points_match_the_pieces(self) -> GeometryFileConfig:
        """Check there is one point count per profile piece (n_cylinder only with a cylinder)."""

        # count the pieces (building the profile also runs its own checks)
        profile = self.geometry.build()
        n_pieces = len(profile.junctions) + 1
        has_cylinder = n_pieces == 3

        # check: n_cylinder exactly when there is a cylinder
        if has_cylinder and self.points.n_cylinder is None:
            raise ValueError("[points] n_cylinder is needed: the geometry has a cylinder")
        if not has_cylinder and self.points.n_cylinder is not None:
            raise ValueError("[points] n_cylinder is only for geometries with a cylinder")

        return self

    def points_per_piece(self) -> list[int]:
        """Point counts in order along the profile: nose, body, then cylinder if any."""

        # build
        counts = [self.points.n_nose, self.points.n_body]
        if self.points.n_cylinder is not None:
            counts.append(self.points.n_cylinder)

        return counts


# --------------------------------------------------
# public API
# --------------------------------------------------
def load_config(path: str | Path, expected_type: str | None = None) -> GeometryFileConfig:
    """Read and validate a geometry TOML file.

    A relative output path is resolved against the folder holding the config file.

    Args:
        path: Configuration file.
        expected_type: If given, the [geometry] type the file must describe
            (e.g. "cone" when called from `geometry cone run`).

    Returns:
        Validated configuration.

    Raises:
        OSError: If the file can't be read.
        tomllib.TOMLDecodeError: If the file isn't valid TOML.
        pydantic.ValidationError: If a value is missing, misspelled or out of range.
        ValueError: If the file describes a different geometry type than expected.
    """

    # convert to Path object
    path = Path(path)

    # read
    with path.open("rb") as stream:
        raw_dict = tomllib.load(stream)

    # validate
    config = GeometryFileConfig.model_validate(raw_dict)

    # check the file matches the command it was given to
    geometry_type = config.geometry.type
    if expected_type is not None and geometry_type != expected_type:
        raise ValueError(
            f"{path} describes a '{geometry_type}' geometry, not '{expected_type}'; "
            f"run it with: geometry {geometry_type} run {path}"
        )

    # resolve the output path relative to the config file
    output_file = path.parent / config.output.file
    resolved_output = OutputConfig(file=output_file)
    resolved_config = config.model_copy(update={"output": resolved_output})

    return resolved_config
