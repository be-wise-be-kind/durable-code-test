"""Track boundary generation from centerline.

Purpose: Generate inner and outer track boundaries from centerline
Scope: Boundary calculation using perpendicular normals
Overview: This module calculates track boundaries by offsetting the centerline
    using perpendicular normal vectors. Extracted from racing.py for modularity.
Dependencies: Standard library math, Pydantic models from racing.models
Exports: generate_track_boundaries, calculate_normal_offset
Interfaces: Functions for boundary generation from centerline
Implementation: Normal vector calculation and boundary offset
"""

import math
from collections.abc import Callable

from ..models import Point2D, TrackBoundary


def calculate_normal_offset(
    current: tuple[float, float],
    next_point: tuple[float, float],
    track_width: float,
) -> tuple[float, float]:
    """Calculate inner boundary point using normal vector.

    Computes the perpendicular normal vector to the tangent and offsets
    the current point by the track width to create the inner boundary.

    Args:
        current: Current point (x, y)
        next_point: Next point for tangent calculation
        track_width: Width of track

    Returns:
        Inner boundary point (x, y)
    """
    # Calculate tangent vector
    tangent_x = next_point[0] - current[0]
    tangent_y = next_point[1] - current[1]
    length = math.sqrt(tangent_x**2 + tangent_y**2)

    if length > 0:
        # Perpendicular vector (rotated 90 degrees)
        normal_x = -tangent_y / length
        normal_y = tangent_x / length

        # Offset point along normal
        inner_x = current[0] + normal_x * track_width
        inner_y = current[1] + normal_y * track_width
    else:
        # Degenerate case - no tangent
        inner_x = current[0]
        inner_y = current[1]

    return (inner_x, inner_y)


def generate_track_boundaries(
    interpolated_centerline: list[tuple[float, float]],
    track_width: float,
) -> tuple[list[Point2D], list[Point2D]]:
    """Generate inner and outer track boundaries from centerline.

    Takes a densely interpolated centerline and creates parallel inner
    and outer boundaries by offsetting points perpendicular to the
    centerline direction.

    Args:
        interpolated_centerline: Dense centerline points
        track_width: Total track width

    Returns:
        Tuple of (outer_points, inner_points) as Point2D lists
    """
    all_outer_points = []
    all_inner_points = []
    half_width = track_width / 2
    num_points = len(interpolated_centerline)

    for i, current in enumerate(interpolated_centerline):
        next_pt = interpolated_centerline[(i + 1) % num_points]

        # Calculate tangent direction
        dx = next_pt[0] - current[0]
        dy = next_pt[1] - current[1]
        length = math.sqrt(dx * dx + dy * dy)

        if length > 0:
            # Normal vector (perpendicular to tangent)
            normal = (-dy / length, dx / length)

            # Offset current point in both directions
            all_outer_points.append(
                Point2D(
                    x=current[0] + normal[0] * half_width,
                    y=current[1] + normal[1] * half_width,
                )
            )
            all_inner_points.append(
                Point2D(
                    x=current[0] - normal[0] * half_width,
                    y=current[1] - normal[1] * half_width,
                )
            )
        else:
            # Degenerate case - offset horizontally
            all_outer_points.append(Point2D(x=current[0] + half_width, y=current[1]))
            all_inner_points.append(Point2D(x=current[0] - half_width, y=current[1]))

    return all_outer_points, all_inner_points


def generate_boundaries_from_centerline(
    control_points: list[tuple[float, float]],
    track_width: float,
    *,
    interpolate_fn: Callable[[list[tuple[float, float]]], list[tuple[float, float]]],
    smooth_fn: Callable[[list[tuple[float, float]]], list[tuple[float, float]]],
) -> TrackBoundary:
    """Generate track boundaries from centerline control points.

    High-level function that orchestrates smoothing, interpolation,
    and boundary generation.

    Args:
        control_points: Control points defining centerline
        track_width: Width of track
        interpolate_fn: Function to interpolate centerline
        smooth_fn: Function to smooth centerline

    Returns:
        TrackBoundary with inner and outer boundaries
    """
    # Smooth the control points
    smoothed = smooth_fn(control_points)

    # Interpolate to dense centerline
    centerline = interpolate_fn(smoothed)

    # Generate boundaries
    outer, inner = generate_track_boundaries(centerline, track_width)

    return TrackBoundary(outer=outer, inner=inner)
