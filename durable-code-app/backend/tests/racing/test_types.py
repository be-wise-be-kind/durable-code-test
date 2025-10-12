"""Tests for racing.types module."""

import pytest

from app.racing.types import DIFFICULTY_PARAMS, Point, TrackConfig


class TestPoint:
    """Tests for Point domain type."""

    def test_point_creation(self) -> None:
        """Test Point can be created with coordinates."""
        point = Point(x=10.0, y=20.0)
        assert point.x == 10.0
        assert point.y == 20.0

    def test_point_immutability(self) -> None:
        """Test Point is immutable (frozen dataclass)."""
        point = Point(x=10.0, y=20.0)
        with pytest.raises(AttributeError):
            point.x = 30.0  # type: ignore

    def test_distance_to(self) -> None:
        """Test distance calculation between points."""
        p1 = Point(x=0.0, y=0.0)
        p2 = Point(x=3.0, y=4.0)
        distance = p1.distance_to(p2)
        assert distance == 5.0  # 3-4-5 triangle

    def test_to_tuple(self) -> None:
        """Test conversion to tuple."""
        point = Point(x=10.0, y=20.0)
        assert point.to_tuple() == (10.0, 20.0)

    def test_from_tuple(self) -> None:
        """Test creation from tuple."""
        point = Point.from_tuple((10.0, 20.0))
        assert point.x == 10.0
        assert point.y == 20.0


class TestTrackConfig:
    """Tests for TrackConfig domain type."""

    def test_default_config(self) -> None:
        """Test TrackConfig has sensible defaults."""
        config = TrackConfig()
        assert config.width == 800
        assert config.height == 600
        assert config.track_width == 80.0
        assert config.padding == 60

    def test_custom_config(self) -> None:
        """Test TrackConfig can be customized."""
        config = TrackConfig(width=1024, height=768, track_width=100.0)
        assert config.width == 1024
        assert config.height == 768
        assert config.track_width == 100.0

    def test_get_center(self) -> None:
        """Test center point calculation."""
        config = TrackConfig(width=800, height=600)
        center = config.get_center()
        assert center.x == 400.0
        assert center.y == 300.0

    def test_get_base_radius(self) -> None:
        """Test base radius calculation."""
        config = TrackConfig(width=800, height=600, padding=60)
        radius_x, radius_y = config.get_base_radius()
        assert radius_x == (800 - 2 * 60) / 2
        assert radius_y == (600 - 2 * 60) / 2

    def test_config_immutability(self) -> None:
        """Test TrackConfig is immutable."""
        config = TrackConfig()
        with pytest.raises(AttributeError):
            config.width = 1024  # type: ignore


class TestConstants:
    """Tests for module constants."""

    def test_difficulty_params_exist(self) -> None:
        """Test difficulty parameters are defined."""
        assert "easy" in DIFFICULTY_PARAMS
        assert "medium" in DIFFICULTY_PARAMS
        assert "hard" in DIFFICULTY_PARAMS

    def test_difficulty_params_structure(self) -> None:
        """Test difficulty parameters have correct structure."""
        for difficulty, params in DIFFICULTY_PARAMS.items():
            assert "track_width" in params
            assert "num_points" in params
            assert "variation" in params
            assert isinstance(params["track_width"], float)
            assert isinstance(params["num_points"], int)
            assert isinstance(params["variation"], float)

    def test_difficulty_progression(self) -> None:
        """Test difficulty parameters increase in difficulty."""
        easy = DIFFICULTY_PARAMS["easy"]
        medium = DIFFICULTY_PARAMS["medium"]
        hard = DIFFICULTY_PARAMS["hard"]

        # Easy should have wider track, fewer points, less variation
        assert easy["track_width"] > medium["track_width"]
        assert medium["track_width"] > hard["track_width"]
        assert easy["num_points"] < medium["num_points"]
        assert medium["num_points"] < hard["num_points"]
