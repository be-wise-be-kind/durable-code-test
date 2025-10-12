"""Special track layout generators.

Purpose: Generate specific track layouts (figure-8, etc.)
Scope: Parametric track layout generation
Overview: Specialized track generators for specific shapes and patterns,
    including figure-8 and other geometric layouts.
Dependencies: Standard library math, geometry functions
Exports: generate_figure8_track
Interfaces: Track layout generation functions
Implementation: Parametric equations for special shapes
"""

import math

from ..geometry.boundaries import TrackBoundary
from ..geometry.curves import interpolate_centerline, smooth_track_centerline


def generate_figure8_track(width: int, height: int, track_width: float) -> TrackBoundary:
    """Generate a figure-8 style track with crossover.

    Creates a track in the shape of a figure-8 using parametric equations
    for two overlapping loops.

    Args:
        width: Canvas width
        height: Canvas height
        track_width: Width of track surface

    Returns:
        TrackBoundary for figure-8 layout
    """
    center_x, center_y = width / 2, height / 2
    radius = min(width, height) / 4

    # Create figure-8 shape with two loops
    control_points = []
    num_points = 32

    for i in range(num_points):
        angle = (2 * math.pi * i) / num_points

        # Create figure-8 using parametric equations
        if i < num_points // 2:
            # Upper loop
            x = center_x + radius * 1.2 * math.cos(angle * 2)
            y = center_y - radius * 0.8 - radius * 0.8 * math.sin(angle * 2)
        else:
            # Lower loop
            angle_offset = angle - math.pi
            x = center_x + radius * 1.2 * math.cos(angle_offset * 2)
            y = center_y + radius * 0.8 + radius * 0.8 * math.sin(angle_offset * 2)

        control_points.append((x, y))

    # Generate smooth centerline and boundaries
    smoothed = smooth_track_centerline(control_points)
    centerline = interpolate_centerline(smoothed)

    # Use the boundaries generation function
    from ..geometry.boundaries import generate_track_boundaries

    outer, inner = generate_track_boundaries(centerline, track_width)
    return TrackBoundary(outer=outer, inner=inner)
