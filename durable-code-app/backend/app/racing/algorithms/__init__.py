"""Algorithms package for racing module.

Purpose: Complex algorithms for track generation
Scope: Concave hull, random point generation, special track layouts
Overview: This package contains specialized algorithms used in track
    generation including computational geometry and layout algorithms.
"""

from .hull import compute_concave_hull, find_k_nearest, select_best_candidate
from .layouts import generate_figure8_track
from .random_points import generate_random_track_points

__all__ = [
    "compute_concave_hull",
    "find_k_nearest",
    "select_best_candidate",
    "generate_random_track_points",
    "generate_figure8_track",
]
