"""Curve interpolation and smoothing for track generation.

Purpose: Provide Catmull-Rom spline interpolation and curve smoothing
Scope: Centerline interpolation, curve smoothing algorithms
Overview: This module contains mathematical functions for interpolating smooth
    curves using Catmull-Rom splines and smoothing track centerlines. Extracted
    from the monolithic racing.py to improve modularity.
Dependencies: Standard library math
Exports: catmull_rom_point, smooth_track_centerline, interpolate_centerline
Interfaces: Pure functions for curve operations
Implementation: Catmull-Rom spline math and moving average smoothing
"""

import math


def catmull_rom_point(
    p0: tuple[float, float],
    p1: tuple[float, float],
    p2: tuple[float, float],
    p3: tuple[float, float],
    t: float,
) -> tuple[float, float]:
    """Calculate a point on a Catmull-Rom curve.

    Catmull-Rom splines create smooth curves through control points.
    This implementation uses the standard Catmull-Rom basis matrix.

    Args:
        p0: First control point (before curve segment)
        p1: Second control point (start of curve segment)
        p2: Third control point (end of curve segment)
        p3: Fourth control point (after curve segment)
        t: Interpolation parameter (0 to 1)

    Returns:
        Interpolated point (x, y) on the curve
    """
    t2 = t * t
    t3 = t2 * t

    # Catmull-Rom basis calculation for x coordinate
    x = 0.5 * (
        (2 * p1[0])
        + (-p0[0] + p2[0]) * t
        + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2
        + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3
    )

    # Catmull-Rom basis calculation for y coordinate
    y = 0.5 * (
        (2 * p1[1])
        + (-p0[1] + p2[1]) * t
        + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
        + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3
    )

    return (x, y)


def smooth_track_centerline(points: list[tuple[float, float]], smoothing_passes: int = 2) -> list[tuple[float, float]]:
    """Smooth track centerline using moving average filter.

    Applies a 3-point moving average filter multiple times to smooth
    the track centerline. Each pass averages each point with its neighbors.

    Args:
        points: Track centerline points
        smoothing_passes: Number of smoothing iterations

    Returns:
        Smoothed centerline points
    """
    if len(points) < 3:
        return points

    smoothed = points.copy()

    for _ in range(smoothing_passes):
        new_smoothed = []
        num_points = len(smoothed)

        for i in range(num_points):
            prev_pt = smoothed[(i - 1) % num_points]
            curr_pt = smoothed[i]
            next_pt = smoothed[(i + 1) % num_points]

            # 3-point moving average
            avg_x = (prev_pt[0] + curr_pt[0] + next_pt[0]) / 3
            avg_y = (prev_pt[1] + curr_pt[1] + next_pt[1]) / 3
            new_smoothed.append((avg_x, avg_y))

        smoothed = new_smoothed

    return smoothed


def interpolate_centerline(
    smoothed_points: list[tuple[float, float]], points_per_segment: int = 10
) -> list[tuple[float, float]]:
    """Interpolate centerline points using Catmull-Rom splines.

    Creates a smooth, interpolated centerline by applying Catmull-Rom
    splines between control points. This densifies the point set for
    smoother track boundaries.

    Args:
        smoothed_points: Smoothed control points
        points_per_segment: Number of interpolated points per segment

    Returns:
        Dense interpolated centerline
    """
    interpolated_centerline = []
    num_control = len(smoothed_points)

    for i in range(num_control):
        # Get four control points (wrap around for closed loop)
        p0 = smoothed_points[(i - 1) % num_control]
        p1 = smoothed_points[i]
        p2 = smoothed_points[(i + 1) % num_control]
        p3 = smoothed_points[(i + 2) % num_control]

        # Interpolate points along this segment
        for t in range(points_per_segment):
            t_norm = t / points_per_segment
            point = catmull_rom_point(p0, p1, p2, p3, t_norm)
            interpolated_centerline.append(point)

    return interpolated_centerline


def normalize_angle(angle: float) -> float:
    """Normalize angle to [-pi, pi] range.

    Args:
        angle: Angle in radians

    Returns:
        Normalized angle in [-pi, pi]
    """
    while angle > math.pi:
        angle -= 2 * math.pi
    while angle < -math.pi:
        angle += 2 * math.pi
    return angle
