"""Comprehensive security utilities and middleware for application-wide protection.

Purpose: Comprehensive security utilities and middleware for application-wide protection.
Scope: Input validation, sanitization, rate limiting, security headers, and threat mitigation
Overview: This module provides a complete security layer for the FastAPI application, implementing
    defense-in-depth practices to protect against common web vulnerabilities. It includes input
    sanitization to prevent XSS attacks, strict validation rules to ensure data integrity, rate
    limiting to prevent abuse and DDoS attacks, and security headers middleware to protect against
    various client-side attacks. The module implements OWASP security best practices, including
    Content Security Policy, HSTS, X-Frame-Options, and other critical security headers. All
    security functions are designed to be performant while maintaining strong protection levels.
Dependencies: FastAPI, pydantic for validation, slowapi for rate limiting, html for sanitization
Exports: SecurityMiddleware class, sanitize_input function, SecureModel base class, rate limiter
Interfaces: Middleware dispatch method, validation decorators, sanitization utilities
Implementation: Middleware pattern with configurable security policies and validation chains
"""

import html
import re
from typing import Any

from fastapi import Request, Response
from pydantic import BaseModel, Field, validator
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware

# Security constants
MAX_TEXT_LENGTH = 1000
MIN_TEXT_LENGTH = 1
MAX_FREQUENCY = 100.0
MIN_FREQUENCY = 0.1
MAX_AMPLITUDE = 10.0
MIN_AMPLITUDE = 0.1
MAX_OFFSET = 10.0
MIN_OFFSET = -10.0

# HTTP Status Codes
HTTP_TOO_MANY_REQUESTS = 429

# Input sanitization patterns
ALLOWED_TEXT_PATTERN = re.compile(r"^[a-zA-Z0-9\s\-_.,!?()]+$")
# Path validation pattern - using atomic grouping (?:...) to prevent ReDoS via backtracking
PATH_PATTERN = re.compile(r"^(?:/[a-zA-Z0-9_-]+)+$")
DANGEROUS_PATTERNS = [
    re.compile(r"<script.*?</script>", re.IGNORECASE | re.DOTALL),
    re.compile(r"javascript:", re.IGNORECASE),
    re.compile(r"on\w+\s*=", re.IGNORECASE),
    re.compile(r"<iframe.*?</iframe>", re.IGNORECASE | re.DOTALL),
]

# Rate limiting configuration
RATE_LIMITER = Limiter(key_func=get_remote_address, default_limits=["100 per minute", "1000 per hour"])

# Security headers configuration - Using built-in security headers
SECURITY_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "img-src 'self' data: https://fastapi.tiangolo.com"
    ),
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Cache-Control": "no-cache",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
}


def sanitize_text_input(text: str) -> str:
    """Sanitize text input to prevent XSS and injection attacks.

    Args:
        text: Raw text input to sanitize

    Returns:
        Sanitized text safe for processing

    Raises:
        ValueError: If text contains dangerous patterns
    """
    if not text:
        return text

    # Check for dangerous patterns
    for pattern in DANGEROUS_PATTERNS:
        if pattern.search(text):
            raise ValueError("Input contains potentially dangerous content")

    # Use built-in HTML escaping for XSS protection
    sanitized = html.escape(text, quote=True)

    # Additional validation for allowed characters
    if not ALLOWED_TEXT_PATTERN.match(sanitized):
        raise ValueError("Input contains invalid characters")

    return sanitized.strip()


def validate_numeric_range(value: float, min_val: float, max_val: float, field_name: str) -> float:
    """Validate numeric values are within safe ranges.

    Args:
        value: Numeric value to validate
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        field_name: Name of field for error messages

    Returns:
        Validated numeric value

    Raises:
        ValueError: If value is outside allowed range
    """
    if not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be a number")

    if value < min_val or value > max_val:
        raise ValueError(f"{field_name} must be between {min_val} and {max_val}")

    return float(value)


def validate_path(path: str) -> str:
    """Validate path string to prevent ReDoS and path traversal attacks.

    Uses atomic grouping in regex to prevent catastrophic backtracking
    that could lead to ReDoS (Regular Expression Denial of Service).

    Args:
        path: Path string to validate

    Returns:
        Validated path string

    Raises:
        ValueError: If path contains invalid characters or patterns
    """
    if not path:
        raise ValueError("Path cannot be empty")

    if ".." in path:
        raise ValueError("Path traversal not allowed")

    if not PATH_PATTERN.match(path):
        raise ValueError("Path contains invalid characters or format")

    return path


class SecureTextInput(BaseModel):
    """Secure text input model with comprehensive validation."""

    text: str = Field(
        ...,
        min_length=MIN_TEXT_LENGTH,
        max_length=MAX_TEXT_LENGTH,
        description="Text input with security validation",
    )

    @validator("text")
    def sanitize_text(cls, value: str) -> str:  # noqa: N805
        """Sanitize and validate text input."""
        return sanitize_text_input(value)


class SecureNumericInput(BaseModel):
    """Secure numeric input model with range validation."""

    frequency: float = Field(
        ...,
        ge=MIN_FREQUENCY,
        le=MAX_FREQUENCY,
        description="Frequency value with security validation",
    )
    amplitude: float = Field(
        ...,
        ge=MIN_AMPLITUDE,
        le=MAX_AMPLITUDE,
        description="Amplitude value with security validation",
    )
    offset: float = Field(
        ...,
        ge=MIN_OFFSET,
        le=MAX_OFFSET,
        description="Offset value with security validation",
    )

    @validator("frequency")
    def validate_frequency_range(cls, value: float) -> float:  # noqa: N805
        """Validate frequency is within safe operational range."""
        return validate_numeric_range(value, MIN_FREQUENCY, MAX_FREQUENCY, "frequency")

    @validator("amplitude")
    def validate_amplitude_range(cls, value: float) -> float:  # noqa: N805
        """Validate amplitude is within safe operational range."""
        return validate_numeric_range(value, MIN_AMPLITUDE, MAX_AMPLITUDE, "amplitude")

    @validator("offset")
    def validate_offset_range(cls, value: float) -> float:  # noqa: N805
        """Validate offset is within safe operational range."""
        return validate_numeric_range(value, MIN_OFFSET, MAX_OFFSET, "offset")


class SecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware for FastAPI applications."""

    async def dispatch(self, request: Request, call_next: Any) -> Any:
        """Process request with security middleware.

        Args:
            request: FastAPI request object
            call_next: Next middleware/route handler

        Returns:
            Response with security headers applied
        """
        # Process request
        response = await call_next(request)

        # Apply security headers
        for header_name, header_value in SECURITY_HEADERS.items():
            response.headers[header_name] = header_value

        # Add additional security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Robots-Tag"] = "noindex, nofollow"
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"

        return response


def get_rate_limiter() -> Limiter:
    """Get configured rate limiter instance.

    Returns:
        Configured Limiter instance for rate limiting
    """
    return RATE_LIMITER


def create_rate_limited_route(rate_limit: str) -> Any:
    """Create a rate-limited route decorator.

    Args:
        rate_limit: Rate limit string (e.g., "10 per minute")

    Returns:
        Decorator function for rate limiting routes
    """

    def decorator(func: Any) -> Any:
        return RATE_LIMITER.limit(rate_limit)(func)

    return decorator


# Security configuration for different endpoint types
SECURITY_CONFIG = {
    "health_check": {"rate_limit": "60 per minute"},
    "api_data": {"rate_limit": "30 per minute"},
    "websocket": {"rate_limit": "10 per minute"},
    "config": {"rate_limit": "20 per minute"},
}


def get_security_config(endpoint_type: str) -> dict[str, str]:
    """Get security configuration for specific endpoint type.

    Args:
        endpoint_type: Type of endpoint (health_check, api_data, etc.)

    Returns:
        Security configuration dictionary
    """
    return SECURITY_CONFIG.get(endpoint_type, {"rate_limit": "100 per minute"})


async def _rate_limit_exceeded_handler(request: Request, exc: Exception) -> Response:
    """Handle rate limit exceeded exceptions.

    Args:
        request: FastAPI request object
        exc: Rate limit exceeded exception

    Returns:
        JSON response with rate limit error
    """
    # Default retry after value
    retry_after = "60"

    # Try to get retry_after from exception if available
    if hasattr(exc, "retry_after"):
        retry_after = str(exc.retry_after)

    response = Response(
        content='{"error": "Rate limit exceeded", "message": "Too many requests"}',
        status_code=HTTP_TOO_MANY_REQUESTS,
        headers={"Content-Type": "application/json", "Retry-After": retry_after},
    )
    return response
