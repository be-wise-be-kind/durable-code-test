"""Famous racing circuit generators inspired by real-world tracks.

Purpose: Generate track layouts inspired by iconic racing circuits
Scope: Track generation for Spa, Monaco, Laguna Seca, and Suzuka
Overview: Provides track generators that mimic the characteristics of famous circuits
Dependencies: Pydantic for data models
Exports: Track generation functions for famous circuits
Implementation: Pure functions that return track boundaries
"""

from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.racing.models import TrackBoundary


def generate_spa_inspired_track(
    width: int,
    height: int,
    track_width: float,
    generate_boundaries_fn: Callable[[list[tuple[float, float]], float], "TrackBoundary"],
) -> "TrackBoundary":
    """Generate Spa-Francorchamps inspired track with fast curves and elevation changes.

    Args:
        width: Canvas width
        height: Canvas height
        track_width: Width of track surface
        generate_boundaries_fn: Function to generate boundaries from centerline

    Returns:
        TrackBoundary for Spa-inspired layout
    """
    # Create iconic Spa sections: Eau Rouge, Blanchimont, Bus Stop
    control_points = [
        (width * 0.5, height * 0.9),  # Start/finish
        (width * 0.3, height * 0.8),  # Turn 1 (La Source)
        (width * 0.2, height * 0.65),  # Eau Rouge entry
        (width * 0.25, height * 0.5),  # Eau Rouge climb
        (width * 0.35, height * 0.35),  # Raidillon
        (width * 0.5, height * 0.25),  # Kemmel Straight entry
        (width * 0.7, height * 0.2),  # Les Combes
        (width * 0.8, height * 0.3),  # Malmedy
        (width * 0.85, height * 0.45),  # Rivage
        (width * 0.8, height * 0.6),  # Pouhon
        (width * 0.7, height * 0.7),  # Fagnes
        (width * 0.6, height * 0.75),  # Campus
        (width * 0.55, height * 0.82),  # La Source approach
    ]

    return generate_boundaries_fn(control_points, track_width)


def generate_monaco_style_track(
    width: int,
    height: int,
    track_width: float,
    generate_boundaries_fn: Callable[[list[tuple[float, float]], float], "TrackBoundary"],
) -> "TrackBoundary":
    """Generate Monaco street circuit inspired track with tight corners.

    Args:
        width: Canvas width
        height: Canvas height
        track_width: Width of track surface
        generate_boundaries_fn: Function to generate boundaries from centerline

    Returns:
        TrackBoundary for Monaco-style layout
    """
    # Tight, technical street circuit with hairpins and chicanes
    control_points = [
        (width * 0.5, height * 0.85),  # Start/finish
        (width * 0.4, height * 0.75),  # Sainte Devote
        (width * 0.3, height * 0.6),  # Beau Rivage climb
        (width * 0.25, height * 0.45),  # Massenet
        (width * 0.2, height * 0.3),  # Casino Square
        (width * 0.25, height * 0.2),  # Mirabeau
        (width * 0.4, height * 0.15),  # Hairpin (Loews)
        (width * 0.55, height * 0.18),  # Portier
        (width * 0.7, height * 0.25),  # Tunnel entry
        (width * 0.8, height * 0.35),  # Tunnel exit
        (width * 0.82, height * 0.5),  # Chicane entry
        (width * 0.78, height * 0.58),  # Chicane exit
        (width * 0.7, height * 0.68),  # Tabac
        (width * 0.6, height * 0.78),  # Piscine
        (width * 0.55, height * 0.82),  # La Rascasse
    ]

    return generate_boundaries_fn(control_points, track_width)


def generate_laguna_seca_track(
    width: int,
    height: int,
    track_width: float,
    generate_boundaries_fn: Callable[[list[tuple[float, float]], float], "TrackBoundary"],
) -> "TrackBoundary":
    """Generate Laguna Seca inspired track with famous corkscrew section.

    Args:
        width: Canvas width
        height: Canvas height
        track_width: Width of track surface
        generate_boundaries_fn: Function to generate boundaries from centerline

    Returns:
        TrackBoundary for Laguna Seca layout
    """
    control_points = [
        (width * 0.5, height * 0.85),  # Start/finish
        (width * 0.3, height * 0.75),  # Turn 1
        (width * 0.2, height * 0.6),  # Turn 2
        (width * 0.25, height * 0.4),  # Turn 3 (Andretti Hairpin)
        (width * 0.4, height * 0.3),  # Turn 4
        (width * 0.6, height * 0.25),  # Turn 5
        (width * 0.75, height * 0.3),  # Turn 6 (Corkscrew entry)
        (width * 0.78, height * 0.42),  # Turn 7 (Corkscrew)
        (width * 0.75, height * 0.55),  # Turn 8 (Corkscrew exit)
        (width * 0.65, height * 0.65),  # Turn 9
        (width * 0.55, height * 0.75),  # Turn 10
        (width * 0.52, height * 0.82),  # Turn 11
    ]

    return generate_boundaries_fn(control_points, track_width)


def generate_suzuka_style_track(
    width: int,
    height: int,
    track_width: float,
    generate_boundaries_fn: Callable[[list[tuple[float, float]], float], "TrackBoundary"],
) -> "TrackBoundary":
    """Generate Suzuka figure-8 inspired track with iconic esses and hairpin.

    Args:
        width: Canvas width
        height: Canvas height
        track_width: Width of track surface
        generate_boundaries_fn: Function to generate boundaries from centerline

    Returns:
        TrackBoundary for Suzuka-style layout
    """
    control_points = [
        (width * 0.5, height * 0.88),  # Start/finish
        (width * 0.3, height * 0.8),  # Turn 1
        (width * 0.2, height * 0.68),  # Turn 2 (S-curves entry)
        (width * 0.22, height * 0.54),  # Turn 3 (S-curves)
        (width * 0.28, height * 0.42),  # Turn 4
        (width * 0.25, height * 0.28),  # Turn 5 (Degner)
        (width * 0.35, height * 0.2),  # Turn 6
        (width * 0.5, height * 0.15),  # Turn 7 (Hairpin)
        (width * 0.65, height * 0.18),  # Turn 8
        (width * 0.75, height * 0.28),  # Turn 9 (Spoon entry)
        (width * 0.78, height * 0.42),  # Turn 10 (Spoon)
        (width * 0.72, height * 0.55),  # Turn 11
        (width * 0.68, height * 0.65),  # Turn 12 (130R entry)
        (width * 0.6, height * 0.75),  # Turn 13 (130R)
        (width * 0.55, height * 0.82),  # Turn 14 (Chicane)
    ]

    return generate_boundaries_fn(control_points, track_width)
