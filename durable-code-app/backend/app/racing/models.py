"""Pydantic models for racing API.

Purpose: Request/response models for racing API endpoints
Scope: API data validation and serialization
Overview: This module contains all Pydantic models used for request validation
    and response serialization in the racing API. Extracted from racing.py.
Dependencies: Pydantic for validation, types module for constants
Exports: Point2D, TrackBoundary, SimpleTrack, TrackGenerationParams
Interfaces: Pydantic BaseModel classes for API contracts
Implementation: Declarative Pydantic models with validation rules
"""

from pydantic import BaseModel, Field

from .types import (
    DEFAULT_TRACK_HEIGHT,
    DEFAULT_TRACK_WIDTH,
    MAX_TRACK_HEIGHT,
    MAX_TRACK_WIDTH,
    MIN_TRACK_HEIGHT,
    MIN_TRACK_WIDTH,
)


class Point2D(BaseModel):
    """2D point representation for API responses."""

    x: float = Field(..., description="X coordinate")
    y: float = Field(..., description="Y coordinate")


class TrackBoundary(BaseModel):
    """Track boundary definition with inner and outer points."""

    inner: list[Point2D] = Field(..., description="Inner track boundary points")
    outer: list[Point2D] = Field(..., description="Outer track boundary points")


class SimpleTrack(BaseModel):
    """Simple track data for physics testing and gameplay."""

    width: int = Field(
        default=DEFAULT_TRACK_WIDTH,
        ge=MIN_TRACK_WIDTH,
        le=MAX_TRACK_WIDTH,
        description="Track canvas width",
    )
    height: int = Field(
        default=DEFAULT_TRACK_HEIGHT,
        ge=MIN_TRACK_HEIGHT,
        le=MAX_TRACK_HEIGHT,
        description="Track canvas height",
    )
    boundaries: TrackBoundary = Field(..., description="Track boundary points")
    start_position: Point2D = Field(..., description="Starting position for the car")
    track_width: float = Field(default=80, ge=40, le=120, description="Width of the track surface")


class TrackGenerationParams(BaseModel):
    """Parameters for procedural track generation with validation."""

    difficulty: str = Field(
        default="medium",
        pattern="^(easy|medium|hard)$",
        description="Track difficulty level",
    )
    seed: int | None = Field(default=None, ge=0, le=999999, description="Seed for reproducible generation")
    width: int = Field(
        default=DEFAULT_TRACK_WIDTH,
        ge=MIN_TRACK_WIDTH,
        le=MAX_TRACK_WIDTH,
        description="Canvas width",
    )
    height: int = Field(
        default=DEFAULT_TRACK_HEIGHT,
        ge=MIN_TRACK_HEIGHT,
        le=MAX_TRACK_HEIGHT,
        description="Canvas height",
    )
    layout: str = Field(
        default="procedural",
        pattern="^(procedural|figure8|spa|monaco|laguna|suzuka)$",
        description="Track layout style",
    )

    # Advanced parameters for procedural generation
    num_points: int | None = Field(default=None, ge=6, le=24, description="Number of control points")
    variation_amount: float | None = Field(default=None, ge=0.05, le=0.50, description="Radius variation amount")
    hairpin_chance: float | None = Field(default=None, ge=0, le=0.60, description="Probability of hairpin turns")
    hairpin_intensity: float | None = Field(default=None, ge=1.0, le=5.0, description="Hairpin variation multiplier")
    smoothing_passes: int | None = Field(default=None, ge=0, le=5, description="Number of smoothing iterations")
    track_width_override: float | None = Field(default=None, ge=60, le=140, description="Override track width")
