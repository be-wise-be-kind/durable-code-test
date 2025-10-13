"""Security tests for ReDoS protection, WebSocket rate limiting, and error sanitization."""

import time

import pytest

from app.security import PATH_PATTERN, validate_path


def test_redos_protection_malicious_input() -> None:
    """Test ReDoS protection with malicious input that would cause backtracking.

    The original vulnerable pattern `^(/[a-zA-Z0-9_-]+)+$` would cause
    catastrophic backtracking on input like "///...aaa...!" because each
    failed match would trigger backtracking through all possible groupings.

    The fixed pattern `^(?:/[a-zA-Z0-9_-]+)+$` uses atomic grouping (?:...)
    which prevents backtracking, making it safe from ReDoS attacks.
    """
    # Malicious input that would cause catastrophic backtracking in vulnerable regex
    evil_input = "/" + "a" * 10000 + "!"

    start = time.time()
    result = PATH_PATTERN.match(evil_input)
    duration = time.time() - start

    # Should complete quickly (< 100ms) even with malicious input
    assert duration < 0.1, f"ReDoS detected: took {duration:.3f}s to process malicious input"

    # Should not match (invalid due to "!" at end)
    assert result is None


def test_redos_protection_valid_paths() -> None:
    """Test that ReDoS-protected pattern still matches valid paths."""
    valid_paths = [
        "/api/v1",
        "/users/123",
        "/api/v1/users/profile",
        "/a",
        "/a/b/c/d/e/f",
    ]

    for path in valid_paths:
        result = PATH_PATTERN.match(path)
        assert result is not None, f"Valid path {path} should match"


def test_redos_protection_invalid_paths() -> None:
    """Test that ReDoS-protected pattern rejects invalid paths."""
    invalid_paths = [
        "no-leading-slash",
        "/path with spaces",
        "/path/../traversal",
        "/path/./current",
        "/path//double-slash",
        "/path$special",
        "",
        "/",
        "/path!invalid",
    ]

    for path in invalid_paths:
        result = PATH_PATTERN.match(path)
        assert result is None, f"Invalid path {path} should not match"


def test_validate_path_accepts_valid_paths() -> None:
    """Test validate_path function with valid paths."""
    valid_paths = [
        "/api/v1",
        "/users/123",
        "/api/v1/users/profile",
    ]

    for path in valid_paths:
        result = validate_path(path)
        assert result == path


def test_validate_path_rejects_path_traversal() -> None:
    """Test validate_path rejects path traversal attempts."""
    with pytest.raises(ValueError) as exc_info:
        validate_path("/api/../etc/passwd")

    assert "path traversal" in str(exc_info.value).lower()


def test_validate_path_rejects_invalid_characters() -> None:
    """Test validate_path rejects invalid characters."""
    with pytest.raises(ValueError) as exc_info:
        validate_path("/api/user$123")

    assert "invalid" in str(exc_info.value).lower()


def test_validate_path_rejects_empty_path() -> None:
    """Test validate_path rejects empty path."""
    with pytest.raises(ValueError) as exc_info:
        validate_path("")

    assert "empty" in str(exc_info.value).lower()


def test_websocket_rate_limiter_allows_within_limits() -> None:
    """Test WebSocket rate limiter allows connections within limits."""
    from app.oscilloscope import WebSocketRateLimiter

    limiter = WebSocketRateLimiter(max_connections_per_ip=5, window_seconds=60.0)

    # Should allow up to 5 connections from same IP
    for i in range(5):
        result = limiter.check_rate_limit("192.168.1.100")
        assert result is True, f"Connection {i+1} should be allowed"


def test_websocket_rate_limiter_blocks_exceeding_limits() -> None:
    """Test WebSocket rate limiter blocks connections exceeding limits."""
    from app.oscilloscope import WebSocketRateLimiter

    limiter = WebSocketRateLimiter(max_connections_per_ip=5, window_seconds=60.0)

    # Allow 5 connections
    for _ in range(5):
        limiter.check_rate_limit("192.168.1.100")

    # 6th connection should be blocked
    result = limiter.check_rate_limit("192.168.1.100")
    assert result is False, "6th connection should be blocked"


def test_websocket_rate_limiter_per_ip_isolation() -> None:
    """Test WebSocket rate limiter isolates different IPs."""
    from app.oscilloscope import WebSocketRateLimiter

    limiter = WebSocketRateLimiter(max_connections_per_ip=5, window_seconds=60.0)

    # Max out connections for first IP
    for _ in range(5):
        limiter.check_rate_limit("192.168.1.100")

    # Second IP should still be able to connect
    result = limiter.check_rate_limit("192.168.1.101")
    assert result is True, "Different IP should not be affected"


def test_websocket_rate_limiter_window_expiration() -> None:
    """Test WebSocket rate limiter window expiration."""
    from app.oscilloscope import WebSocketRateLimiter

    # Use short window for testing
    limiter = WebSocketRateLimiter(max_connections_per_ip=2, window_seconds=0.1)

    # Use up connections
    limiter.check_rate_limit("192.168.1.100")
    limiter.check_rate_limit("192.168.1.100")

    # Should be blocked
    assert limiter.check_rate_limit("192.168.1.100") is False

    # Wait for window to expire
    time.sleep(0.15)

    # Should be allowed again
    result = limiter.check_rate_limit("192.168.1.100")
    assert result is True, "Should allow connections after window expiration"


def test_websocket_rate_limiter_release_connection() -> None:
    """Test WebSocket rate limiter connection release."""
    from app.oscilloscope import WebSocketRateLimiter

    limiter = WebSocketRateLimiter(max_connections_per_ip=2, window_seconds=60.0)

    # Use up connections
    limiter.check_rate_limit("192.168.1.100")
    limiter.check_rate_limit("192.168.1.100")

    # Should be blocked
    assert limiter.check_rate_limit("192.168.1.100") is False

    # Release one connection
    limiter.release_connection("192.168.1.100")

    # Should be able to connect again
    result = limiter.check_rate_limit("192.168.1.100")
    assert result is True, "Should allow connection after release"


@pytest.mark.asyncio
async def test_error_sanitization_production() -> None:
    """Test that error messages are sanitized in production environment."""
    import os
    from unittest.mock import AsyncMock, patch

    from fastapi import Request

    from app.main import handle_general_exception

    # Mock request
    mock_request = AsyncMock(spec=Request)
    mock_request.url.path = "/test"
    mock_request.method = "GET"

    # Simulate production environment
    with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
        test_exception = Exception("Sensitive internal error with database credentials")
        response = await handle_general_exception(mock_request, test_exception)

        # Check response content
        assert response.status_code == 500
        # Handle both bytes and memoryview types from response body
        body = response.body
        content = body.decode() if isinstance(body, bytes) else bytes(body).decode()

        # Should NOT contain sensitive information
        assert "database credentials" not in content.lower()
        assert "sensitive internal error" not in content.lower()

        # Should contain generic message
        assert "internal error occurred" in content.lower()


@pytest.mark.asyncio
async def test_error_details_in_development() -> None:
    """Test that error details are available in development environment."""
    import os
    from unittest.mock import AsyncMock, patch

    from fastapi import Request

    from app.main import handle_general_exception

    # Mock request
    mock_request = AsyncMock(spec=Request)
    mock_request.url.path = "/test"
    mock_request.method = "GET"

    # Simulate development environment
    with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
        test_exception = ValueError("Detailed error for debugging")
        response = await handle_general_exception(mock_request, test_exception)

        # Check response content
        assert response.status_code == 500
        # Handle both bytes and memoryview types from response body
        body = response.body
        content = body.decode() if isinstance(body, bytes) else bytes(body).decode()

        # Should contain detailed error information
        assert "Detailed error for debugging" in content
        assert "ValueError" in content
