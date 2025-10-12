"""Concave hull computation algorithm.

Purpose: Compute concave hull of point sets
Scope: k-nearest neighbors based hull algorithm
Overview: Implementation of concave hull algorithm using k-nearest neighbors
    approach. Used for creating closed track shapes from scattered points.
Dependencies: Standard library math
Exports: compute_concave_hull, find_k_nearest, select_best_candidate
Interfaces: Pure functions for hull computation
Implementation: k-NN based concave hull with angle-based point selection
"""

import math

from ..geometry.curves import normalize_angle


def find_k_nearest(current: tuple[float, float], points_set: set, k: int) -> list[tuple[float, float]]:
    """Find k nearest neighbors to current point.

    Args:
        current: Current point (x, y)
        points_set: Set of available points
        k: Number of neighbors to find

    Returns:
        List of k nearest points
    """
    distances = [(p, math.sqrt((p[0] - current[0]) ** 2 + (p[1] - current[1]) ** 2)) for p in points_set]
    distances.sort(key=lambda x: x[1])
    return [p for p, _ in distances[: min(k, len(distances))]]


def select_best_candidate(
    candidates: list[tuple[float, float]],
    current: tuple[float, float],
    prev: tuple[float, float] | None,
) -> tuple[float, float]:
    """Select best candidate based on angle from previous direction.

    Selects the candidate that maximizes the left-turn angle from the
    previous direction, which helps create a consistent hull boundary.

    Args:
        candidates: List of candidate points
        current: Current point
        prev: Previous point (None if at start)

    Returns:
        Best candidate point
    """
    if prev is None:
        return candidates[0]

    ref_angle = math.atan2(current[1] - prev[1], current[0] - prev[0])
    best_angle = -math.pi
    best_candidate = candidates[0]

    for candidate in candidates:
        angle = math.atan2(candidate[1] - current[1], candidate[0] - current[0])
        relative_angle = normalize_angle(angle - ref_angle)

        if relative_angle > best_angle:
            best_angle = relative_angle
            best_candidate = candidate

    return best_candidate


def compute_concave_hull(points: list[tuple[float, float]], k: int = 3) -> list[tuple[float, float]]:
    """Compute concave hull of points using k-nearest neighbors approach.

    Creates a concave hull that follows the shape of the point cloud
    more closely than a convex hull would. Uses k-nearest neighbors
    to find candidate points and angle-based selection to build the hull.

    Args:
        points: List of input points
        k: Number of nearest neighbors to consider

    Returns:
        Ordered list of points forming concave hull
    """
    if len(points) < 3:
        return points

    # Start with leftmost point
    start = min(points, key=lambda p: (p[0], p[1]))
    hull = [start]
    current = start
    points_set = set(points)
    points_set.remove(start)

    # Build hull by selecting best neighbor at each step
    while points_set:
        candidates = find_k_nearest(current, points_set, k)
        if not candidates:
            break

        prev = hull[-2] if len(hull) > 1 else None
        next_point = select_best_candidate(candidates, current, prev)

        # Check if we've completed the loop
        if next_point == start and len(hull) > 2:
            break

        hull.append(next_point)
        current = next_point
        points_set.discard(next_point)

        # Safety check to prevent infinite loops
        if len(hull) > len(points) * 2:
            break

    return hull
