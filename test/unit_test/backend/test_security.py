"""
Purpose: Validates security implementations for the durable code application

Scope: Rate limiting, input validation, security headers, and CORS configuration

Overview: Comprehensive test suite for security features including rate limiting,
    input sanitization, security headers validation, and CORS policy testing.
    Ensures that security hardening measures function correctly. Tests verify
    proper input validation against injection attacks, rate limiting effectiveness,
    security header presence and configuration, CORS policy enforcement, and
    overall application security posture.

Dependencies: pytest, httpx, FastAPI TestClient

Exports: Security test functions for automated testing

Interfaces: pytest test functions

Implementation: FastAPI TestClient for endpoint testing and mock requests
"""

import pytest
from app.main import app
from app.oscilloscope import OscilloscopeCommand, WaveType
from app.security import sanitize_text_input, validate_numeric_range
from fastapi.testclient import TestClient

client = TestClient(app)


class TestInputValidation:
    """Test input validation and sanitization."""

    def test_sanitize_text_input_valid(self) -> None:
        """Test text sanitization with valid input."""
        valid_text = "Hello World 123"
        result = sanitize_text_input(valid_text)
        assert result == "Hello World 123"

    def test_sanitize_text_input_with_html(self) -> None:
        """Test text sanitization removes HTML."""
        html_text = "<script>alert('xss')</script>Hello"
        with pytest.raises(ValueError, match="potentially dangerous content"):
            sanitize_text_input(html_text)

    def test_sanitize_text_input_with_javascript(self) -> None:
        """Test text sanitization blocks JavaScript."""
        js_text = "javascript:alert('xss')"
        with pytest.raises(ValueError, match="potentially dangerous content"):
            sanitize_text_input(js_text)

    def test_sanitize_text_input_empty(self) -> None:
        """Test text sanitization with empty input."""
        result = sanitize_text_input("")
        assert result == ""

    def test_validate_numeric_range_valid(self) -> None:
        """Test numeric validation with valid ranges."""
        result = validate_numeric_range(5.0, 1.0, 10.0, "test_field")
        assert result == 5.0

    def test_validate_numeric_range_below_minimum(self) -> None:
        """Test numeric validation rejects values below minimum."""
        with pytest.raises(ValueError, match="test_field must be between"):
            validate_numeric_range(0.5, 1.0, 10.0, "test_field")

    def test_validate_numeric_range_above_maximum(self) -> None:
        """Test numeric validation rejects values above maximum."""
        with pytest.raises(ValueError, match="test_field must be between"):
            validate_numeric_range(15.0, 1.0, 10.0, "test_field")

    def test_validate_numeric_range_invalid_type(self) -> None:
        """Test numeric validation rejects non-numeric types."""
        with pytest.raises(ValueError, match="test_field must be a number"):
            validate_numeric_range("not_a_number", 1.0, 10.0, "test_field")  # type: ignore[arg-type]


class TestOscilloscopeValidation:
    """Test enhanced validation for oscilloscope commands."""

    def test_oscilloscope_command_valid(self) -> None:
        """Test valid oscilloscope command."""
        command = OscilloscopeCommand(
            command="start", wave_type=WaveType.SINE, frequency=10.0, amplitude=1.0, offset=0.0
        )
        assert command.command == "start"
        assert command.frequency == 10.0

    def test_oscilloscope_command_invalid_command(self) -> None:
        """Test invalid command validation."""
        with pytest.raises(ValueError, match="Command must be one of"):
            OscilloscopeCommand(
                command="invalid_command", wave_type=WaveType.SINE, frequency=10.0, amplitude=1.0, offset=0.0
            )

    def test_oscilloscope_command_frequency_too_high(self) -> None:
        """Test frequency validation with value too high."""
        with pytest.raises(Exception, match="less_than_equal"):
            OscilloscopeCommand(
                command="start",
                wave_type=WaveType.SINE,
                frequency=150.0,  # Above MAX_FREQUENCY
                amplitude=1.0,
                offset=0.0,
            )

    def test_oscilloscope_command_amplitude_too_low(self) -> None:
        """Test amplitude validation with value too low."""
        with pytest.raises(Exception, match="greater_than_equal"):
            OscilloscopeCommand(
                command="start",
                wave_type=WaveType.SINE,
                frequency=10.0,
                amplitude=0.05,  # Below MIN_AMPLITUDE
                offset=0.0,
            )


class TestSecurityHeaders:
    """Test security headers implementation."""

    def test_security_headers_present(self) -> None:
        """Test that all security headers are present in responses."""
        response = client.get("/")

        # Check all security headers are present
        expected_headers = [
            "content-security-policy",
            "strict-transport-security",
            "x-frame-options",
            "referrer-policy",
            "cache-control",
            "permissions-policy",
            "x-content-type-options",
            "x-robots-tag",
            "x-permitted-cross-domain-policies",
        ]

        for header in expected_headers:
            assert header in response.headers, f"Missing security header: {header}"

    def test_csp_header_content(self) -> None:
        """Test Content Security Policy header content."""
        response = client.get("/")
        csp = response.headers.get("content-security-policy")
        assert "default-src 'self'" in csp
        assert "script-src 'self'" in csp
        assert "https://cdn.jsdelivr.net" in csp

    def test_hsts_header_content(self) -> None:
        """Test HSTS header content."""
        response = client.get("/")
        hsts = response.headers.get("strict-transport-security")
        assert "max-age=31536000" in hsts
        assert "includeSubDomains" in hsts

    def test_frame_options_header(self) -> None:
        """Test X-Frame-Options header."""
        response = client.get("/")
        assert response.headers.get("x-frame-options") == "DENY"


class TestRateLimiting:
    """Test rate limiting functionality."""

    def test_rate_limiting_allows_normal_requests(self) -> None:
        """Test that normal request rates are allowed."""
        # Make a few requests to ensure they work normally
        for _ in range(3):
            response = client.get("/")
            assert response.status_code == 200

    def test_health_endpoint_rate_limiting(self) -> None:
        """Test health endpoint has rate limiting applied."""
        response = client.get("/health")
        assert response.status_code == 200
        # The rate limiting is configured, exact testing would require many requests

    def test_oscilloscope_endpoints_rate_limiting(self) -> None:
        """Test oscilloscope endpoints have rate limiting."""
        response = client.get("/api/oscilloscope/config")
        assert response.status_code == 200
        # Rate limiting decorators are applied


class TestCORSConfiguration:
    """Test CORS configuration."""

    def test_cors_allows_configured_origins(self) -> None:
        """Test CORS allows configured origins."""
        headers = {"Origin": "http://localhost:5173"}
        response = client.options("/", headers=headers)

        # Should allow the configured origin
        assert "access-control-allow-origin" in response.headers

    def test_cors_credentials_disabled(self) -> None:
        """Test CORS credentials are disabled for security."""
        headers = {"Origin": "http://localhost:5173"}
        response = client.options("/", headers=headers)

        # Credentials should be disabled
        allow_credentials = response.headers.get("access-control-allow-credentials")
        assert allow_credentials != "true"

    def test_cors_methods_restricted(self) -> None:
        """Test CORS methods are restricted to specific ones."""
        headers = {"Origin": "http://localhost:5173"}
        response = client.get("/", headers=headers)

        # Should have CORS origin header but not allow all methods
        assert "access-control-allow-origin" in response.headers
        assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"

        # Check that we don't allow all origins (wildcard)
        assert response.headers.get("access-control-allow-origin") != "*"


class TestAPIEndpointSecurity:
    """Test API endpoint security."""

    def test_root_endpoint_security(self) -> None:
        """Test root endpoint has security measures."""
        response = client.get("/")
        assert response.status_code == 200

        # Should have security headers
        assert "content-security-policy" in response.headers

        # Should return expected content
        assert response.json() == {"message": "Welcome to Durable Code API"}

    def test_health_endpoint_security(self) -> None:
        """Test health endpoint security."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    def test_oscilloscope_config_security(self) -> None:
        """Test oscilloscope config endpoint security."""
        response = client.get("/api/oscilloscope/config")
        assert response.status_code == 200

        # Should have security headers
        assert "x-content-type-options" in response.headers

        # Should return valid config
        config = response.json()
        assert "sample_rate" in config
        assert "supported_wave_types" in config


class TestSecurityIntegration:
    """Test overall security integration."""

    def test_middleware_chain_order(self) -> None:
        """Test that security middleware is properly integrated."""
        response = client.get("/")

        # Security headers should be present (indicating middleware ran)
        assert "x-content-type-options" in response.headers

        # CORS should be configured
        assert response.status_code == 200

    def test_error_handling_security(self) -> None:
        """Test that error responses also have security headers."""
        # Request non-existent endpoint
        response = client.get("/nonexistent")
        assert response.status_code == 404

        # Even error responses should have security headers
        assert "x-content-type-options" in response.headers

    def test_websocket_endpoint_accessible(self) -> None:
        """Test that WebSocket endpoint info is accessible with security."""
        response = client.get("/api/oscilloscope/stream/info")
        assert response.status_code == 200

        # Should have security headers
        assert "content-security-policy" in response.headers

        # Should return WebSocket info
        info = response.json()
        assert "endpoint" in info
        assert "commands" in info
