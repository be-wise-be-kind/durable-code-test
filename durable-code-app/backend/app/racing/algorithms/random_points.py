"""Random point generation for track creation.

Purpose: Generate well-spaced random points for track layouts
Scope: Random point generation with spacing constraints
Overview: Generates random points with minimum spacing requirements,
    used for creating organic track shapes.
Dependencies: Standard library math, random
Exports: generate_random_track_points
Interfaces: Pure function for random point generation
Implementation: Trial-and-error approach with spacing validation
"""

import math
import random


def generate_random_track_points(
    num_points: int,
    center: tuple[float, float],
    max_radius: tuple[float, float],
    min_spacing: float,
) -> list[tuple[float, float]]:
    """Generate random points that will form the basis of a track with good spacing.

    Generates points within an elliptical region, ensuring each point
    maintains minimum spacing from all previously generated points.

    Args:
        num_points: Number of points to generate
        center: Center point (x, y)
        max_radius: Maximum radius (rx, ry) for elliptical region
        min_spacing: Minimum distance between points

    Returns:
        List of well-spaced random points
    """
    points: list[tuple[float, float]] = []

    for _ in range(num_points):
        # Try up to 1000 times to find a valid point
        for _ in range(1000):
            # Generate random point in elliptical region (not cryptographic use)
            angle = random.uniform(0, 2 * math.pi)  # noqa: S311  # nosec B311
            r = random.uniform(0.3, 1.0)  # noqa: S311  # nosec B311

            pt = (
                center[0] + max_radius[0] * r * math.cos(angle),
                center[1] + max_radius[1] * r * math.sin(angle),
            )

            # Check spacing constraint
            if all(math.sqrt((pt[0] - e[0]) ** 2 + (pt[1] - e[1]) ** 2) >= min_spacing for e in points):
                points.append(pt)
                break

    return points
