"""Domain types for the racing module.

Purpose: Provide strongly-typed domain models for track generation
Scope: Point, TrackConfig, and other domain primitives
Overview: This module defines immutable domain types that replace primitive
    obsession (tuples, magic numbers) with explicit, type-safe constructs.
    Uses dataclasses for clarity and enforces immutability where appropriate.
Dependencies: Standard library dataclasses
Exports: Point, TrackConfig domain types
Interfaces: Immutable domain primitives with useful methods
Implementation: Frozen dataclasses for immutability and type safety
"""

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Point:
    """2D point with immutable coordinates.

    Replaces tuple-based point representation with a strongly-typed,
    immutable point class that provides useful geometric operations.
    """

    x: float
    y: float

    def distance_to(self, other: "Point") -> float:
        """Calculate Euclidean distance to another point.

        Args:
            other: Target point

        Returns:
            Distance between this point and other
        """
        dx = self.x - other.x
        dy = self.y - other.y
        return math.sqrt(dx * dx + dy * dy)

    def to_tuple(self) -> tuple[float, float]:
        """Convert to tuple representation.

        Returns:
            (x, y) tuple
        """
        return (self.x, self.y)

    @classmethod
    def from_tuple(cls, point: tuple[float, float]) -> "Point":
        """Create Point from tuple.

        Args:
            point: (x, y) tuple

        Returns:
            Point instance
        """
        return cls(x=point[0], y=point[1])


@dataclass(frozen=True)
class TrackConfig:
    """Configuration parameters for track generation.

    Centralizes all track generation parameters in a single,
    immutable configuration object. Replaces magic numbers
    scattered throughout the codebase.
    """

    # Canvas dimensions
    width: int = 800
    height: int = 600

    # Track geometry
    track_width: float = 80.0
    padding: int = 60

    # Control point configuration
    num_control_points: int = 16
    variation_amount: float = 0.22

    # Curve features
    hairpin_chance: float = 0.2
    hairpin_intensity: float = 2.5

    # Smoothing
    smoothing_passes: int = 2
    points_per_segment: int = 10

    # Validation ranges
    min_radius: float = 100.0
    min_spacing: float = 50.0

    def get_center(self) -> Point:
        """Get the center point of the track canvas.

        Returns:
            Center point (width/2, height/2)
        """
        return Point(x=self.width / 2, y=self.height / 2)

    def get_base_radius(self) -> tuple[float, float]:
        """Get the base radius for track generation.

        Returns:
            (radius_x, radius_y) tuple accounting for padding
        """
        radius_x = (self.width - 2 * self.padding) / 2
        radius_y = (self.height - 2 * self.padding) / 2
        return (radius_x, radius_y)


# Constants for track validation
MIN_TRACK_WIDTH = 400
MAX_TRACK_WIDTH = 1920
MIN_TRACK_HEIGHT = 300
MAX_TRACK_HEIGHT = 1080
DEFAULT_TRACK_WIDTH = 800
DEFAULT_TRACK_HEIGHT = 600
DEFAULT_TRACK_PADDING = 60

# Difficulty configurations
DIFFICULTY_PARAMS = {
    "easy": {"track_width": 120.0, "num_points": 12, "variation": 0.15},
    "medium": {"track_width": 100.0, "num_points": 16, "variation": 0.22},
    "hard": {"track_width": 80.0, "num_points": 20, "variation": 0.28},
}

# HTTP Status codes
HTTP_BAD_REQUEST = 400
HTTP_NOT_FOUND = 404
