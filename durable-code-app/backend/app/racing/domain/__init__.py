"""Domain logic package for racing module.

Purpose: Core business logic for track generation
Scope: Track generation algorithms and domain operations
Overview: This package contains the core domain logic including track
    generation, control point manipulation, and track feature algorithms.
"""

from .generator import (
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

__all__ = [
    "generate_procedural_track",
    "generate_oval_track",
    "generate_control_points_radial",
    "generate_control_points_with_bounds",
    "add_track_variation",
    "add_hairpin_turns",
    "add_s_curves",
    "add_chicanes",
    "apply_curve_offset",
]
