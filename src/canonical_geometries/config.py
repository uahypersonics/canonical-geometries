"""Geometry configuration contract: parse and validate the TOML, build the profile.

Used by the geometry CLI and meant to be reused by tools that read the same
[geometry] table (e.g. grid-generator). CLI-only text (help, starter templates)
lives in canonical_geometries.cli.templates.
"""

# --------------------------------------------------
# load necessary modules
# --------------------------------------------------
from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from canonical_geometries.blunted_wedge import BluntedWedge
from canonical_geometries.writers import WRITERS


# --------------------------------------------------
# [geometry]: one model per geometry type
# --------------------------------------------------
class PlateConfig(BaseModel):
    """Flat plate with a circular leading edge (upper half)."""

    # reject misspelled keys
    model_config = ConfigDict(extra="forbid")

    type: Literal["plate"]
    nose_radius: float = Field(gt=0.0, description="Nose radius r_n [m]")
    length: float = Field(gt=0.0, description="Axial length from the nose tip [m]")

    def build(self) -> BluntedWedge:
        """Build the profile (circular nose plus a body at zero half-angle)."""
        profile = BluntedWedge(nose_radius=self.nose_radius, length=self.length)
        return profile


class WedgeConfig(BaseModel):
    """Planar blunted wedge: circular nose plus straight body at a half-angle."""

    # reject misspelled keys
    model_config = ConfigDict(extra="forbid")

    type: Literal["wedge"]
    nose_radius: float = Field(gt=0.0, description="Nose radius r_n [m]")
    length: float = Field(gt=0.0, description="Axial length from the nose tip [m]")
    half_angle: float = Field(ge=0.0, lt=90.0, description="Body half-angle [deg]")

    def build(self) -> BluntedWedge:
        """Build the profile."""
        profile = BluntedWedge(
            nose_radius=self.nose_radius,
            length=self.length,
            half_angle=self.half_angle,
        )
        return profile


class ConeConfig(BaseModel):
    """Sphere-cone (axisymmetric): the profile is its meridian, the same shape as a wedge."""

    # reject misspelled keys
    model_config = ConfigDict(extra="forbid")

    type: Literal["cone"]
    nose_radius: float = Field(gt=0.0, description="Nose radius r_n [m]")
    length: float = Field(gt=0.0, description="Axial length from the nose tip [m]")
    half_angle: float = Field(ge=0.0, lt=90.0, description="Cone half-angle [deg]")

    def build(self) -> BluntedWedge:
        """Build the meridian profile."""
        profile = BluntedWedge(
            nose_radius=self.nose_radius,
            length=self.length,
            half_angle=self.half_angle,
        )
        return profile


# the "type" key picks the model; add new geometry models to this union
GeometryConfig = Annotated[
    PlateConfig | WedgeConfig | ConeConfig,
    Field(discriminator="type"),
]


# --------------------------------------------------
# [points] and [output]
# --------------------------------------------------
class PointsConfig(BaseModel):
    """Points per profile piece, each count including both ends of its piece."""

    # reject misspelled keys
    model_config = ConfigDict(extra="forbid")

    n_nose: int = Field(default=91, ge=2, description="Points on the nose arc")
    n_body: int = Field(default=200, ge=2, description="Points on the body")


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
