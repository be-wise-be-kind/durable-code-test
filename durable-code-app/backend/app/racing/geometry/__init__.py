"""Geometry package for track generation.

Purpose: Geometric operations for track generation
Scope: Curves, boundaries, and spatial calculations
Overview: This package contains all geometric operations needed for track
    generation including curve interpolation and boundary calculations.
"""

from .boundaries import (
    TrackBoundary,
    calculate_normal_offset,
    generate_boundaries_from_centerline,
    generate_track_boundaries,
)
from .curves import (
    catmull_rom_point,
    interpolate_centerline,
    normalize_angle,
    smooth_track_centerline,
)

__all__ = [
    # Curves
    "catmull_rom_point",
    "smooth_track_centerline",
    "interpolate_centerline",
    "normalize_angle",
    # Boundaries
    "TrackBoundary",
    "calculate_normal_offset",
    "generate_track_boundaries",
    "generate_boundaries_from_centerline",
]
