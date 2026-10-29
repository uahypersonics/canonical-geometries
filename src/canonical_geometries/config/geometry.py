"""[geometry] table: one pydantic model per geometry type, each building its profile.

This is the shared geometry contract: the geometry CLI uses it, and so can other
tools that read the same [geometry] table (e.g. grid-generator).
"""

# --------------------------------------------------
# load necessary modules
# --------------------------------------------------
from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from canonical_geometries.blunted_tangent_ogive import BluntedTangentOgive
from canonical_geometries.blunted_wedge import BluntedWedge


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


class TangentOgiveConfig(BaseModel):
    """Spherically blunted tangent ogive (axisymmetric), optionally followed by a cylinder."""

    # reject misspelled keys
    model_config = ConfigDict(extra="forbid")

    type: Literal["tangent-ogive"]
    nose_radius: float = Field(gt=0.0, description="Nose radius r_n [m]")
    length: float = Field(
        gt=0.0,
        description="Length of the sharp ogive, tip to base [m]; the blunted body is shorter",
    )
    base_radius: float = Field(gt=0.0, description="Base radius R [m]")
    cylinder_length: float = Field(
        default=0.0, ge=0.0, description="Length of the cylinder after the base [m]; 0 for none"
    )

    def build(self) -> BluntedTangentOgive:
        """Build the meridian profile."""
        profile = BluntedTangentOgive(
            nose_radius=self.nose_radius,
            length=self.length,
            base_radius=self.base_radius,
            cylinder_length=self.cylinder_length,
        )
        return profile


# the "type" key picks the model; add new geometry models to this union
GeometryConfig = Annotated[
    PlateConfig | WedgeConfig | ConeConfig | TangentOgiveConfig,
    Field(discriminator="type"),
]
