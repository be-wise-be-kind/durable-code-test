"""Track generation domain logic.

Purpose: Core track generation algorithms and control point generation
Scope: Procedural track generation, control points, track variations
Overview: This module contains the core domain logic for generating tracks
    including control point generation, variations, and track features.
Dependencies: Standard library math, random
Exports: Track generation functions
Interfaces: Pure functions for track generation
Implementation: Procedural generation with parametric control
"""

import math
import random

from ..geometry.boundaries import generate_track_boundaries
from ..geometry.curves import interpolate_centerline, smooth_track_centerline
from ..models import Point2D, TrackBoundary
from ..types import TrackConfig


def generate_control_points_radial(
    num_points: int,
    center: tuple[float, float],
    base_radius: tuple[float, float],
    variation_amount: float,
    hairpin_chance: float,
    hairpin_intensity: float,
    width: int,
    height: int,
    padding: int,
    track_width: float,
) -> list[tuple[float, float]]:
    """Generate control points with radial variation.

    Creates control points arranged radially around a center with
    random variation to create interesting track shapes.

    Args:
        num_points: Number of control points
        center: Center point (x, y)
        base_radius: Base radius (rx, ry)
        variation_amount: Amount of random variation (0-1)
        hairpin_chance: Probability of hairpin variation
        hairpin_intensity: Multiplier for hairpin variations
        width: Canvas width
        height: Canvas height
        padding: Edge padding
        track_width: Track width for bounds checking

    Returns:
        List of control points as (x, y) tuples
    """
    control_points = []
    min_radius = padding + track_width

    for i in range(num_points):
        angle = (2 * math.pi * i) / num_points

        # Generate random variation (not cryptographic use)
        variation = random.uniform(-variation_amount, variation_amount)  # noqa: S311  # nosec B311

        # Apply hairpin intensity randomly
        if random.random() < hairpin_chance:  # noqa: S311  # nosec B311
            variation *= hairpin_intensity

        # Calculate radius with variation
        r_x = base_radius[0] * (1 + variation)
        r_y = base_radius[1] * (1 + variation)

        # Clamp to canvas bounds
        r_x = max(min_radius, min(width / 2 - padding, r_x))
        r_y = max(min_radius, min(height / 2 - padding, r_y))

        # Calculate point position
        x = center[0] + r_x * math.cos(angle)
        y = center[1] + r_y * math.sin(angle)
        control_points.append((x, y))

    return control_points


def generate_control_points_with_bounds(
    num_points: int,
    center: tuple[float, float],
    base_radius: tuple[float, float],
    variation: float,
    bounds: tuple[int, int, float],
) -> list[tuple[float, float]]:
    """Generate random control points for track generation.

    Args:
        num_points: Number of control points
        center: Center point (x, y)
        base_radius: Base ellipse radius (rx, ry)
        variation: Variation amount for radius
        bounds: (width, height, padding) for bounds checking

    Returns:
        List of control points
    """
    width, height, padding = bounds
    control_points = []
    min_radius = padding + 50

    for i in range(num_points):
        angle = (2 * math.pi * i) / num_points

        # Add random variation and clamp to bounds (not cryptographic use)
        var = random.uniform(-variation, variation)  # noqa: S311  # nosec B311
        r_x = max(min_radius, min(width / 2 - padding, base_radius[0] * (1 + var)))
        r_y = max(min_radius, min(height / 2 - padding, base_radius[1] * (1 + var)))

        control_points.append((center[0] + r_x * math.cos(angle), center[1] + r_y * math.sin(angle)))

    return control_points


def apply_curve_offset(
    control_points: list[tuple[float, float]],
    index: int,
    offset_dist: float,
    direction: int,
) -> None:
    """Apply perpendicular offset to a control point to create curves.

    Modifies control points in place to create curves by offsetting
    points perpendicular to the track direction.

    Args:
        control_points: Control points to modify
        index: Index of point to offset
        offset_dist: Distance to offset
        direction: Direction multiplier (+1 or -1)
    """
    num_points = len(control_points)
    prev_pt = control_points[index - 1]
    next_pt = control_points[(index + 1) % num_points]

    dx = next_pt[0] - prev_pt[0]
    dy = next_pt[1] - prev_pt[1]
    length = math.sqrt(dx * dx + dy * dy)

    if length > 0:
        normal_x = -dy / length * offset_dist * direction
        normal_y = dx / length * offset_dist * direction
        current = control_points[index]
        control_points[index] = (current[0] + normal_x, current[1] + normal_y)


def add_s_curves(control_points: list[tuple[float, float]]) -> None:
    """Add S-curves at multiple locations along the track.

    Modifies control points in place to create flowing S-curve sections.

    Args:
        control_points: Control points to modify
    """
    num_points = len(control_points)
    s_curve_positions = [
        num_points // 6,
        num_points // 3,
        (2 * num_points) // 3,
        (5 * num_points) // 6,
    ]

    for idx, i in enumerate(s_curve_positions):
        if 0 < i < num_points:
            offset_dist = 50 if idx % 2 == 0 else 35
            direction = (-1) ** idx
            apply_curve_offset(control_points, i, offset_dist, direction)


def add_chicanes(control_points: list[tuple[float, float]]) -> None:
    """Add chicane-style quick direction changes.

    Modifies control points to create tight chicane sections with
    quick left-right or right-left transitions.

    Args:
        control_points: Control points to modify
    """
    num_points = len(control_points)
    chicane_positions = [num_points // 4, (3 * num_points) // 4]

    for idx, i in enumerate(chicane_positions):
        if 1 < i < num_points - 1:
            direction = (-1) ** idx
            apply_curve_offset(control_points, i, 30, direction)

            # Adjust adjacent point for chicane effect
            if i + 1 < num_points:
                prev_pt = control_points[i - 1]
                next_pt = control_points[(i + 1) % num_points]
                dx = next_pt[0] - prev_pt[0]
                dy = next_pt[1] - prev_pt[1]
                length = math.sqrt(dx * dx + dy * dy)

                if length > 0:
                    normal_x = -dy / length * 30 * direction
                    normal_y = dx / length * 30 * direction
                    next_current = control_points[i + 1]
                    control_points[i + 1] = (
                        next_current[0] - normal_x * 0.6,
                        next_current[1] - normal_y * 0.6,
                    )


def add_hairpin_turns(
    control_points: list[tuple[float, float]],
    center: tuple[float, float],
) -> list[tuple[float, float]]:
    """Add dramatic 180-degree hairpin turns to the track.

    Creates sharp hairpin turns by offsetting control points and their
    neighbors perpendicular to the track direction.

    Args:
        control_points: Base control points
        center: Track center for reference

    Returns:
        Modified control points with hairpins
    """
    num_points = len(control_points)
    hairpin_indices = [num_points // 4, num_points // 2, (3 * num_points) // 4]

    for hairpin_idx, base_idx in enumerate(hairpin_indices):
        if 1 < base_idx < num_points - 1:
            base_point = control_points[base_idx]
            prev_point = control_points[base_idx - 1]
            next_point = control_points[(base_idx + 1) % num_points]

            dx = next_point[0] - prev_point[0]
            dy = next_point[1] - prev_point[1]
            length = math.sqrt(dx * dx + dy * dy)

            if length > 0:
                normal = (-dy / length, dx / length)
                hairpin_distance = 80 + (hairpin_idx * 15)

                # Offset main point
                control_points[base_idx] = (
                    base_point[0] + normal[0] * hairpin_distance,
                    base_point[1] + normal[1] * hairpin_distance,
                )

                # Offset entry point
                if base_idx - 1 >= 0:
                    entry = control_points[base_idx - 1]
                    control_points[base_idx - 1] = (
                        entry[0] + normal[0] * hairpin_distance * 0.5,
                        entry[1] + normal[1] * hairpin_distance * 0.5,
                    )

                # Offset exit point
                if base_idx + 1 < num_points:
                    exit_pt = control_points[base_idx + 1]
                    control_points[base_idx + 1] = (
                        exit_pt[0] + normal[0] * hairpin_distance * 0.5,
                        exit_pt[1] + normal[1] * hairpin_distance * 0.5,
                    )

    return control_points


def add_track_variation(
    control_points: list[tuple[float, float]],
    variation_type: str,
    center: tuple[float, float] | None = None,
) -> list[tuple[float, float]]:
    """Add specific track features for more interesting layouts.

    Applies various track features like S-curves, chicanes, and hairpins
    based on the variation type.

    Args:
        control_points: Base control points
        variation_type: Type of variation ("complex", etc.)
        center: Track center point for hairpin calculations

    Returns:
        Modified control points with added features
    """
    if variation_type == "complex":
        add_s_curves(control_points)
        add_chicanes(control_points)
        if center:
            control_points = add_hairpin_turns(control_points, center)

    return control_points


def generate_procedural_track(
    width: int,
    height: int,
    difficulty: str,
    config: TrackConfig,
) -> TrackBoundary:
    """Generate a windy procedural track using radial variation.

    Creates a continuous closed-loop track with configurable difficulty
    and track features.

    Args:
        width: Canvas width
        height: Canvas height
        difficulty: Difficulty level ("easy", "medium", "hard")
        config: Track configuration parameters

    Returns:
        TrackBoundary with inner and outer boundaries

    Raises:
        ValueError: If track generation produces insufficient points
    """
    # Generate control points with variation
    control_points = generate_control_points_radial(
        num_points=config.num_control_points,
        center=(width / 2, height / 2),
        base_radius=((width - 2 * config.padding) / 2, (height - 2 * config.padding) / 2),
        variation_amount=config.variation_amount,
        hairpin_chance=config.hairpin_chance,
        hairpin_intensity=config.hairpin_intensity,
        width=width,
        height=height,
        padding=config.padding,
        track_width=config.track_width,
    )

    # Smooth the control points
    smoothed = smooth_track_centerline(control_points, config.smoothing_passes)

    # Interpolate to dense centerline
    centerline = interpolate_centerline(smoothed, config.points_per_segment)

    # Generate boundaries
    outer, inner = generate_track_boundaries(centerline, config.track_width)

    # Validate sufficient points
    if len(outer) < 3 or len(inner) < 3:
        raise ValueError(f"Track generation failed: insufficient points (outer={len(outer)}, inner={len(inner)})")

    return TrackBoundary(outer=outer, inner=inner)


def generate_oval_track(
    width: int,
    height: int,
    padding: int = 60,
) -> TrackBoundary:
    """Generate a simple oval track for testing.

    Args:
        width: Canvas width
        height: Canvas height
        padding: Padding from canvas edges

    Returns:
        TrackBoundary with inner and outer boundaries
    """
    center = (width / 2, height / 2)
    outer_radius = ((width - 2 * padding) / 2, (height - 2 * padding) / 2)
    track_width = 100  # Wider track for better gameplay
    inner_radius = (outer_radius[0] - track_width, outer_radius[1] - track_width)

    # Generate points around the oval
    num_points = 32
    outer_points = []
    inner_points = []

    for i in range(num_points):
        angle = (2 * math.pi * i) / num_points
        cos_angle = math.cos(angle)
        sin_angle = math.sin(angle)

        # Outer and inner boundaries
        outer_points.append(
            Point2D(
                x=center[0] + outer_radius[0] * cos_angle,
                y=center[1] + outer_radius[1] * sin_angle,
            )
        )
        inner_points.append(
            Point2D(
                x=center[0] + inner_radius[0] * cos_angle,
                y=center[1] + inner_radius[1] * sin_angle,
            )
        )

    return TrackBoundary(outer=outer_points, inner=inner_points)
