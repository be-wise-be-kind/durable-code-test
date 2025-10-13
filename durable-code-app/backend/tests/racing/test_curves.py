"""Tests for racing.geometry.curves module."""

import math

from app.racing.geometry.curves import (
    catmull_rom_point,
    interpolate_centerline,
    normalize_angle,
    smooth_track_centerline,
)


class TestCatmullRomPoint:
    """Tests for Catmull-Rom spline interpolation."""

    def test_catmull_rom_at_t_zero(self) -> None:
        """Test that t=0 returns p1."""
        p0 = (0.0, 0.0)
        p1 = (10.0, 10.0)
        p2 = (20.0, 10.0)
        p3 = (30.0, 0.0)

        result = catmull_rom_point(p0, p1, p2, p3, 0.0)
        assert result[0] == p1[0]
        assert result[1] == p1[1]

    def test_catmull_rom_at_t_one(self) -> None:
        """Test that t=1 returns p2."""
        p0 = (0.0, 0.0)
        p1 = (10.0, 10.0)
        p2 = (20.0, 10.0)
        p3 = (30.0, 0.0)

        result = catmull_rom_point(p0, p1, p2, p3, 1.0)
        assert result[0] == p2[0]
        assert result[1] == p2[1]

    def test_catmull_rom_midpoint(self) -> None:
        """Test interpolation at t=0.5."""
        p0 = (0.0, 0.0)
        p1 = (0.0, 10.0)
        p2 = (10.0, 10.0)
        p3 = (10.0, 0.0)

        result = catmull_rom_point(p0, p1, p2, p3, 0.5)
        # Should be somewhere between p1 and p2
        assert 0.0 < result[0] < 10.0
        assert result[1] >= 9.0  # Should stay close to y=10


class TestSmoothTrackCenterline:
    """Tests for track centerline smoothing."""

    def test_smooth_preserves_count(self) -> None:
        """Test smoothing preserves point count."""
        points = [(0.0, 0.0), (10.0, 5.0), (20.0, 0.0), (10.0, -5.0)]
        smoothed = smooth_track_centerline(points, smoothing_passes=2)
        assert len(smoothed) == len(points)

    def test_smooth_with_few_points(self) -> None:
        """Test smoothing with less than 3 points returns original."""
        points = [(0.0, 0.0), (10.0, 10.0)]
        smoothed = smooth_track_centerline(points, smoothing_passes=2)
        assert smoothed == points

    def test_smooth_reduces_variation(self) -> None:
        """Test smoothing reduces variation in coordinates."""
        # Create points with one outlier
        points = [(0.0, 0.0), (1.0, 0.0), (2.0, 5.0), (3.0, 0.0), (4.0, 0.0)]
        smoothed = smooth_track_centerline(points, smoothing_passes=3)

        # Middle point should be smoothed (less extreme)
        original_y = points[2][1]
        smoothed_y = smoothed[2][1]
        assert abs(smoothed_y) < abs(original_y)

    def test_smooth_zero_passes(self) -> None:
        """Test that zero smoothing passes returns copy."""
        points = [(0.0, 0.0), (10.0, 5.0), (20.0, 0.0)]
        smoothed = smooth_track_centerline(points, smoothing_passes=0)
        assert len(smoothed) == len(points)


class TestInterpolateCenterline:
    """Tests for centerline interpolation."""

    def test_interpolation_increases_points(self) -> None:
        """Test interpolation creates more points."""
        points = [(0.0, 0.0), (100.0, 0.0), (100.0, 100.0), (0.0, 100.0)]
        interpolated = interpolate_centerline(points, points_per_segment=10)
        # Should have 4 control points * 10 points per segment
        assert len(interpolated) == len(points) * 10

    def test_interpolation_with_single_point(self) -> None:
        """Test interpolation with minimal points."""
        points = [(0.0, 0.0)]
        interpolated = interpolate_centerline(points, points_per_segment=10)
        assert len(interpolated) == 10


class TestNormalizeAngle:
    """Tests for angle normalization."""

    def test_normalize_positive_angle(self) -> None:
        """Test normalizing positive angles."""
        angle = 4 * math.pi  # 720 degrees
        normalized = normalize_angle(angle)
        assert -math.pi <= normalized <= math.pi

    def test_normalize_negative_angle(self) -> None:
        """Test normalizing negative angles."""
        angle = -4 * math.pi  # -720 degrees
        normalized = normalize_angle(angle)
        assert -math.pi <= normalized <= math.pi

    def test_normalize_already_normalized(self) -> None:
        """Test that already normalized angles stay the same."""
        angle = math.pi / 4
        normalized = normalize_angle(angle)
        assert abs(normalized - angle) < 0.0001

    def test_normalize_pi(self) -> None:
        """Test normalizing angle at pi boundary."""
        angle = math.pi
        normalized = normalize_angle(angle)
        assert abs(abs(normalized) - math.pi) < 0.0001
