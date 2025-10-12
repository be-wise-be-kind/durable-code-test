"""Tests for racing API route handlers.

Purpose: Test all racing API endpoints
Scope: Unit tests for route handlers, error handling, validation
Overview: Comprehensive test suite for racing API routes including
    simple track generation, procedural track generation, health checks,
    error handling, and edge cases.
Dependencies: pytest, FastAPI TestClient
Exports: Test functions for pytest
Interfaces: pytest test suite
Implementation: Unit tests with mocking and fixtures
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.racing.models import SimpleTrack, TrackBoundary
from app.racing.types import (
    DEFAULT_TRACK_HEIGHT,
    DEFAULT_TRACK_WIDTH,
    MAX_TRACK_HEIGHT,
    MAX_TRACK_WIDTH,
    MIN_TRACK_HEIGHT,
    MIN_TRACK_WIDTH,
)

# Create test client
client = TestClient(app)


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    def test_health_check_returns_healthy_status(self) -> None:
        """Test that health check returns healthy status."""
        response = client.get("/api/racing/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "racing-api"


class TestSimpleTrackEndpoint:
    """Tests for the simple track generation endpoint."""

    def test_get_simple_track_with_defaults(self) -> None:
        """Test simple track generation with default parameters."""
        response = client.get("/api/racing/track/simple")
        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "width" in data
        assert "height" in data
        assert "boundaries" in data
        assert "start_position" in data
        assert "track_width" in data

        # Verify default values
        assert data["width"] == DEFAULT_TRACK_WIDTH
        assert data["height"] == DEFAULT_TRACK_HEIGHT
        assert data["track_width"] == 100

    def test_get_simple_track_with_custom_dimensions(self) -> None:
        """Test simple track generation with custom width and height."""
        custom_width = 1000
        custom_height = 800

        response = client.get(f"/api/racing/track/simple?width={custom_width}&height={custom_height}")
        assert response.status_code == 200
        data = response.json()

        assert data["width"] == custom_width
        assert data["height"] == custom_height

    def test_get_simple_track_validates_min_width(self) -> None:
        """Test that width below minimum is rejected."""
        invalid_width = MIN_TRACK_WIDTH - 1

        response = client.get(f"/api/racing/track/simple?width={invalid_width}")
        assert response.status_code == 422  # Validation error

    def test_get_simple_track_validates_max_width(self) -> None:
        """Test that width above maximum is rejected."""
        invalid_width = MAX_TRACK_WIDTH + 1

        response = client.get(f"/api/racing/track/simple?width={invalid_width}")
        assert response.status_code == 422  # Validation error

    def test_get_simple_track_validates_min_height(self) -> None:
        """Test that height below minimum is rejected."""
        invalid_height = MIN_TRACK_HEIGHT - 1

        response = client.get(f"/api/racing/track/simple?height={invalid_height}")
        assert response.status_code == 422  # Validation error

    def test_get_simple_track_validates_max_height(self) -> None:
        """Test that height above maximum is rejected."""
        invalid_height = MAX_TRACK_HEIGHT + 1

        response = client.get(f"/api/racing/track/simple?height={invalid_height}")
        assert response.status_code == 422  # Validation error

    def test_get_simple_track_has_valid_boundaries(self) -> None:
        """Test that generated track has valid boundary points."""
        response = client.get("/api/racing/track/simple")
        assert response.status_code == 200
        data = response.json()

        boundaries = data["boundaries"]
        assert "inner" in boundaries
        assert "outer" in boundaries
        assert len(boundaries["inner"]) > 0
        assert len(boundaries["outer"]) > 0

        # Verify boundary points have x, y coordinates
        for point in boundaries["inner"]:
            assert "x" in point
            assert "y" in point
            assert isinstance(point["x"], (int, float))
            assert isinstance(point["y"], (int, float))

    def test_get_simple_track_has_valid_start_position(self) -> None:
        """Test that generated track has valid start position."""
        response = client.get("/api/racing/track/simple")
        assert response.status_code == 200
        data = response.json()

        start_position = data["start_position"]
        assert "x" in start_position
        assert "y" in start_position
        assert isinstance(start_position["x"], (int, float))
        assert isinstance(start_position["y"], (int, float))


class TestGenerateTrackEndpoint:
    """Tests for the procedural track generation endpoint."""

    def test_generate_track_with_default_params(self) -> None:
        """Test track generation with default parameters."""
        response = client.post("/api/racing/track/generate", json={})
        assert response.status_code == 200
        data = response.json()

        assert "width" in data
        assert "height" in data
        assert "boundaries" in data
        assert "start_position" in data
        assert "track_width" in data

    def test_generate_track_with_easy_difficulty(self) -> None:
        """Test track generation with easy difficulty."""
        response = client.post("/api/racing/track/generate", json={"difficulty": "easy"})
        assert response.status_code == 200
        data = response.json()

        # Easy difficulty should have wider track
        assert data["track_width"] == 120.0

    def test_generate_track_with_medium_difficulty(self) -> None:
        """Test track generation with medium difficulty."""
        response = client.post("/api/racing/track/generate", json={"difficulty": "medium"})
        assert response.status_code == 200
        data = response.json()

        assert data["track_width"] == 100.0

    def test_generate_track_with_hard_difficulty(self) -> None:
        """Test track generation with hard difficulty."""
        response = client.post("/api/racing/track/generate", json={"difficulty": "hard"})
        assert response.status_code == 200
        data = response.json()

        # Hard difficulty should have narrower track
        assert data["track_width"] == 80.0

    def test_generate_track_validates_difficulty(self) -> None:
        """Test that invalid difficulty is rejected."""
        response = client.post("/api/racing/track/generate", json={"difficulty": "invalid"})
        assert response.status_code == 422  # Validation error

    def test_generate_track_with_seed(self) -> None:
        """Test track generation with seed parameter."""
        seed = 42
        response = client.post("/api/racing/track/generate", json={"seed": seed})
        assert response.status_code == 200

    def test_generate_track_validates_seed_range(self) -> None:
        """Test that seed outside valid range is rejected."""
        invalid_seed = 1000000  # Above max of 999999
        response = client.post("/api/racing/track/generate", json={"seed": invalid_seed})
        assert response.status_code == 422  # Validation error

    def test_generate_track_with_custom_dimensions(self) -> None:
        """Test track generation with custom width and height."""
        custom_width = 1200
        custom_height = 900

        response = client.post(
            "/api/racing/track/generate", json={"width": custom_width, "height": custom_height}
        )
        assert response.status_code == 200
        data = response.json()

        assert data["width"] == custom_width
        assert data["height"] == custom_height

    def test_generate_track_with_figure8_layout(self) -> None:
        """Test track generation with figure-8 layout."""
        response = client.post("/api/racing/track/generate", json={"layout": "figure8"})
        assert response.status_code == 200
        data = response.json()

        assert "boundaries" in data
        assert len(data["boundaries"]["inner"]) > 0
        assert len(data["boundaries"]["outer"]) > 0

    def test_generate_track_with_spa_layout(self) -> None:
        """Test track generation with Spa-inspired layout."""
        response = client.post("/api/racing/track/generate", json={"layout": "spa"})
        assert response.status_code == 200

    def test_generate_track_with_monaco_layout(self) -> None:
        """Test track generation with Monaco-style layout."""
        response = client.post("/api/racing/track/generate", json={"layout": "monaco"})
        assert response.status_code == 200

    def test_generate_track_with_laguna_layout(self) -> None:
        """Test track generation with Laguna Seca layout."""
        response = client.post("/api/racing/track/generate", json={"layout": "laguna"})
        assert response.status_code == 200

    def test_generate_track_with_suzuka_layout(self) -> None:
        """Test track generation with Suzuka-style layout."""
        response = client.post("/api/racing/track/generate", json={"layout": "suzuka"})
        assert response.status_code == 200

    def test_generate_track_validates_layout(self) -> None:
        """Test that invalid layout is rejected."""
        response = client.post("/api/racing/track/generate", json={"layout": "invalid"})
        assert response.status_code == 422  # Validation error

    def test_generate_track_with_custom_num_points(self) -> None:
        """Test track generation with custom number of control points."""
        response = client.post("/api/racing/track/generate", json={"num_points": 12})
        assert response.status_code == 200

    def test_generate_track_validates_num_points_min(self) -> None:
        """Test that num_points below minimum is rejected."""
        response = client.post("/api/racing/track/generate", json={"num_points": 5})
        assert response.status_code == 422  # Validation error

    def test_generate_track_validates_num_points_max(self) -> None:
        """Test that num_points above maximum is rejected."""
        response = client.post("/api/racing/track/generate", json={"num_points": 25})
        assert response.status_code == 422  # Validation error

    def test_generate_track_with_custom_variation(self) -> None:
        """Test track generation with custom variation amount."""
        response = client.post("/api/racing/track/generate", json={"variation_amount": 0.3})
        assert response.status_code == 200

    def test_generate_track_validates_variation_min(self) -> None:
        """Test that variation_amount below minimum is rejected."""
        response = client.post("/api/racing/track/generate", json={"variation_amount": 0.01})
        assert response.status_code == 422  # Validation error

    def test_generate_track_validates_variation_max(self) -> None:
        """Test that variation_amount above maximum is rejected."""
        response = client.post("/api/racing/track/generate", json={"variation_amount": 0.6})
        assert response.status_code == 422  # Validation error

    def test_generate_track_with_hairpin_params(self) -> None:
        """Test track generation with hairpin parameters."""
        response = client.post(
            "/api/racing/track/generate", json={"hairpin_chance": 0.5, "hairpin_intensity": 3.0}
        )
        assert response.status_code == 200

    def test_generate_track_with_smoothing_passes(self) -> None:
        """Test track generation with custom smoothing passes."""
        response = client.post("/api/racing/track/generate", json={"smoothing_passes": 3})
        assert response.status_code == 200

    def test_generate_track_validates_smoothing_max(self) -> None:
        """Test that smoothing_passes above maximum is rejected."""
        response = client.post("/api/racing/track/generate", json={"smoothing_passes": 6})
        assert response.status_code == 422  # Validation error

    def test_generate_track_with_track_width_override(self) -> None:
        """Test track generation with custom track width."""
        response = client.post("/api/racing/track/generate", json={"track_width_override": 90.0})
        assert response.status_code == 200
        data = response.json()

        assert data["track_width"] == 90.0

    def test_generate_track_validates_track_width_min(self) -> None:
        """Test that track_width_override below minimum is rejected."""
        response = client.post("/api/racing/track/generate", json={"track_width_override": 50.0})
        assert response.status_code == 422  # Validation error

    def test_generate_track_validates_track_width_max(self) -> None:
        """Test that track_width_override above maximum is rejected."""
        response = client.post("/api/racing/track/generate", json={"track_width_override": 150.0})
        assert response.status_code == 422  # Validation error


class TestErrorHandling:
    """Tests for error handling in API routes."""

    def test_simple_track_handles_extreme_dimensions(self) -> None:
        """Test that extreme but valid dimensions are handled gracefully."""
        response = client.get(f"/api/racing/track/simple?width={MIN_TRACK_WIDTH}&height={MIN_TRACK_HEIGHT}")
        assert response.status_code == 200

    def test_generate_track_handles_all_parameters_at_once(self) -> None:
        """Test track generation with all optional parameters specified."""
        params = {
            "difficulty": "hard",
            "seed": 12345,
            "width": 1600,
            "height": 1000,
            "layout": "procedural",
            "num_points": 18,
            "variation_amount": 0.25,
            "hairpin_chance": 0.3,
            "hairpin_intensity": 2.0,
            "smoothing_passes": 3,
            "track_width_override": 90.0,
        }
        response = client.post("/api/racing/track/generate", json=params)
        assert response.status_code == 200


class TestResponseStructure:
    """Tests for response structure and data integrity."""

    def test_simple_track_response_matches_schema(self) -> None:
        """Test that simple track response matches SimpleTrack schema."""
        response = client.get("/api/racing/track/simple")
        assert response.status_code == 200
        data = response.json()

        # Validate response can be deserialized to SimpleTrack
        track = SimpleTrack(**data)
        assert track is not None
        assert isinstance(track.boundaries, TrackBoundary)

    def test_generated_track_response_matches_schema(self) -> None:
        """Test that generated track response matches SimpleTrack schema."""
        response = client.post("/api/racing/track/generate", json={"difficulty": "medium"})
        assert response.status_code == 200
        data = response.json()

        # Validate response can be deserialized to SimpleTrack
        track = SimpleTrack(**data)
        assert track is not None
        assert isinstance(track.boundaries, TrackBoundary)

    def test_track_boundaries_form_closed_loop(self) -> None:
        """Test that track boundaries have sufficient points to form a closed loop."""
        response = client.post("/api/racing/track/generate", json={})
        assert response.status_code == 200
        data = response.json()

        # Should have at least 3 points to form a closed shape
        assert len(data["boundaries"]["inner"]) >= 3
        assert len(data["boundaries"]["outer"]) >= 3

    def test_start_position_within_track_bounds(self) -> None:
        """Test that start position is within the track canvas bounds."""
        width = 800
        height = 600
        response = client.get(f"/api/racing/track/simple?width={width}&height={height}")
        assert response.status_code == 200
        data = response.json()

        start = data["start_position"]
        assert 0 <= start["x"] <= width
        assert 0 <= start["y"] <= height
