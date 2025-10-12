"""Racing module - backward compatibility layer.

Purpose: Maintain backward compatibility with original racing.py module
Scope: Re-export all public APIs from refactored package structure
Overview: This module provides a compatibility layer that re-exports all
    functions and classes from the refactored racing package, ensuring that
    existing code using `from app.racing import X` continues to work.
Dependencies: All sub-modules in racing package
Exports: All public APIs from original racing.py
Interfaces: Same as original racing.py module
Implementation: Re-exports from refactored modules
"""

# Re-export models for backward compatibility
# Import router for backward compatibility - will be created in Sub-PR 3.2
# For now, we'll import from the old racing_old module temporarily
# This will be replaced once we create api/routes.py
from ..racing_old import router

# Re-export algorithms
from .algorithms.hull import (
    compute_concave_hull,
    find_k_nearest,
    select_best_candidate,
)
from .algorithms.layouts import generate_figure8_track
from .algorithms.random_points import generate_random_track_points

# Re-export domain/generation functions
from .domain.generator import (
    add_chicanes,
    add_hairpin_turns,
    add_s_curves,
    add_track_variation,
    apply_curve_offset,
    generate_control_points_radial,
    generate_control_points_with_bounds,
    generate_oval_track,
    generate_procedural_track,
)

# Re-export geometry functions
from .geometry.boundaries import (
    calculate_normal_offset,
    generate_boundaries_from_centerline,
    generate_track_boundaries,
)
from .geometry.curves import (
    catmull_rom_point,
    interpolate_centerline,
    normalize_angle,
    smooth_track_centerline,
)
from .models import Point2D, SimpleTrack, TrackBoundary, TrackGenerationParams

# Re-export types and constants
from .types import (
    DEFAULT_TRACK_HEIGHT,
    DEFAULT_TRACK_PADDING,
    DEFAULT_TRACK_WIDTH,
    DIFFICULTY_PARAMS,
    HTTP_BAD_REQUEST,
    HTTP_NOT_FOUND,
    MAX_TRACK_HEIGHT,
    MAX_TRACK_WIDTH,
    MIN_TRACK_HEIGHT,
    MIN_TRACK_WIDTH,
    Point,
    TrackConfig,
)

__all__ = [
    # Models
    "Point2D",
    "TrackBoundary",
    "SimpleTrack",
    "TrackGenerationParams",
    # Types
    "Point",
    "TrackConfig",
    "DEFAULT_TRACK_WIDTH",
    "DEFAULT_TRACK_HEIGHT",
    "MIN_TRACK_WIDTH",
    "MAX_TRACK_WIDTH",
    "MIN_TRACK_HEIGHT",
    "MAX_TRACK_HEIGHT",
    "DEFAULT_TRACK_PADDING",
    "DIFFICULTY_PARAMS",
    "HTTP_BAD_REQUEST",
    "HTTP_NOT_FOUND",
    # Geometry - Curves
    "catmull_rom_point",
    "smooth_track_centerline",
    "interpolate_centerline",
    "normalize_angle",
    # Geometry - Boundaries
    "calculate_normal_offset",
    "generate_track_boundaries",
    "generate_boundaries_from_centerline",
    # Domain - Generator
    "generate_oval_track",
    "generate_procedural_track",
    "generate_control_points_radial",
    "generate_control_points_with_bounds",
    "add_track_variation",
    "add_hairpin_turns",
    "add_s_curves",
    "add_chicanes",
    "apply_curve_offset",
    # Algorithms - Hull
    "compute_concave_hull",
    "find_k_nearest",
    "select_best_candidate",
    # Algorithms - Layouts
    "generate_figure8_track",
    # Algorithms - Random Points
    "generate_random_track_points",
    # Router
    "router",
]
