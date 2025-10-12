"""Tests for racing.domain.generator module."""

from app.racing.domain.generator import (
    generate_control_points_radial,
    generate_oval_track,
    generate_procedural_track,
)
from app.racing.types import TrackConfig


class TestGenerateOvalTrack:
    """Tests for oval track generation."""

    def test_oval_track_generation(self) -> None:
        """Test basic oval track generation."""
        track = generate_oval_track(800, 600)

        assert len(track.outer) > 0
        assert len(track.inner) > 0
        assert len(track.outer) == len(track.inner)

    def test_oval_track_with_padding(self) -> None:
        """Test oval track respects padding."""
        track = generate_oval_track(800, 600, padding=100)

        # Points should be within bounds minus padding
        for point in track.outer:
            assert 100 <= point.x <= 700
            assert 100 <= point.y <= 500


class TestGenerateControlPointsRadial:
    """Tests for radial control point generation."""

    def test_correct_number_of_points(self) -> None:
        """Test correct number of control points generated."""
        points = generate_control_points_radial(
            num_points=8,
            center=(400.0, 300.0),
            base_radius=(200.0, 150.0),
            variation_amount=0.2,
            hairpin_chance=0.1,
            hairpin_intensity=2.0,
            width=800,
            height=600,
            padding=60,
            track_width=80.0,
        )

        assert len(points) == 8

    def test_points_within_bounds(self) -> None:
        """Test control points respect canvas bounds."""
        width, height, padding = 800, 600, 60

        points = generate_control_points_radial(
            num_points=12,
            center=(400.0, 300.0),
            base_radius=(340.0, 240.0),
            variation_amount=0.2,
            hairpin_chance=0.1,
            hairpin_intensity=2.0,
            width=width,
            height=height,
            padding=padding,
            track_width=80.0,
        )

        # All points should be within canvas bounds
        for x, y in points:
            assert 0 <= x <= width
            assert 0 <= y <= height


class TestGenerateProceduralTrack:
    """Tests for procedural track generation."""

    def test_procedural_track_easy(self) -> None:
        """Test procedural track generation with easy difficulty."""
        config = TrackConfig(
            width=800,
            height=600,
            track_width=120.0,
            num_control_points=12,
            variation_amount=0.15,
        )

        track = generate_procedural_track(800, 600, "easy", config)

        assert len(track.outer) >= 3
        assert len(track.inner) >= 3

    def test_procedural_track_medium(self) -> None:
        """Test procedural track generation with medium difficulty."""
        config = TrackConfig(
            width=800,
            height=600,
            track_width=100.0,
            num_control_points=16,
            variation_amount=0.22,
        )

        track = generate_procedural_track(800, 600, "medium", config)

        assert len(track.outer) >= 3
        assert len(track.inner) >= 3

    def test_procedural_track_hard(self) -> None:
        """Test procedural track generation with hard difficulty."""
        config = TrackConfig(
            width=800,
            height=600,
            track_width=80.0,
            num_control_points=20,
            variation_amount=0.28,
        )

        track = generate_procedural_track(800, 600, "hard", config)

        assert len(track.outer) >= 3
        assert len(track.inner) >= 3
