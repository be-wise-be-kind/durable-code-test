"""
Purpose: Four Golden Signals HTTP metrics collection via OpenTelemetry and FastAPI middleware.

Scope: Backend application request-level metrics for latency, traffic, errors, and saturation

Overview: Implements the Four Golden Signals metrics pattern using OpenTelemetry instruments
    and a pure ASGI middleware. Captures request duration (latency), request count (traffic),
    error count (errors), and active connection gauge (saturation) for all HTTP requests.
    Metrics are exported to Grafana Mimir via the MeterProvider configured in telemetry.py.
    The middleware records timing and status for every request, with method and path labels
    for per-endpoint analysis. Uses a pure ASGI middleware (not BaseHTTPMiddleware) to ensure
    the active connection counter spans the full request-response lifecycle including body
    streaming. All instrumentation is gated behind the OTEL_ENABLED environment variable.

Dependencies: opentelemetry-api, opentelemetry-sdk, FastAPI, starlette

Exports: configure_metrics

Interfaces: configure_metrics(app: FastAPI) creates metric instruments and adds
    the MetricsMiddleware to the application

Implementation: Uses OpenTelemetry Histogram, Counter, and ObservableGauge instruments.
    Pure ASGI middleware wraps the full ASGI call (including response body streaming) to
    accurately track active connections. The active connections metric uses an ObservableGauge
    with a callback that reports the peak concurrent connection count observed since the last
    collection interval. This avoids the point-in-time sampling problem where fast requests
    (sub-millisecond) complete between 60-second collection cycles, always reading zero.
    Metric names follow OpenTelemetry semantic conventions.
"""

from __future__ import annotations

import os
import time
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from collections.abc import Iterable

    from fastapi import FastAPI
    from opentelemetry.metrics import CallbackOptions, Counter, Histogram, Observation
    from starlette.types import ASGIApp, Message, Receive, Scope, Send


class MetricsState:
    """Holds references to OpenTelemetry metric instruments."""

    def __init__(self) -> None:
        """Initialize metric instrument references as None until created."""
        self.request_duration: Histogram | None = None
        self.request_count: Counter | None = None
        self.error_count: Counter | None = None
        self.active_connection_count: int = 0
        self.peak_active_connections: int = 0


_metrics_state = MetricsState()

HTTP_ERROR_STATUS_THRESHOLD = 400


def _active_connections_callback(
    options: CallbackOptions,
) -> Iterable[Observation]:
    """Report peak concurrent connections observed since the last collection.

    Returns the high-water mark of simultaneous in-flight requests and resets
    it for the next interval. This avoids the point-in-time sampling problem
    where fast requests always read zero at the 60-second collection boundary.

    Args:
        options: Callback options provided by the OTel SDK.

    Yields:
        An Observation with the peak active connection count since last collection.
    """
    from opentelemetry.metrics import Observation

    peak = _metrics_state.peak_active_connections
    _metrics_state.peak_active_connections = _metrics_state.active_connection_count
    yield Observation(peak)


def _create_instruments() -> MetricsState:
    """Create OpenTelemetry metric instruments from the global MeterProvider."""
    from opentelemetry.metrics import get_meter

    meter = get_meter("durable-code-backend", "1.0.0")

    state = MetricsState()
    state.request_duration = meter.create_histogram(
        name="http_request_duration_seconds",
        description="HTTP request duration in seconds",
        unit="s",
    )
    state.request_count = meter.create_counter(
        name="http_requests_total",
        description="Total number of HTTP requests",
        unit="1",
    )
    state.error_count = meter.create_counter(
        name="http_errors_total",
        description="Total number of HTTP error responses",
        unit="1",
    )
    meter.create_observable_gauge(
        name="http_active_connections",
        callbacks=[_active_connections_callback],
        description="Number of active HTTP connections",
    )
    return state


def _record_request_metrics(
    state: MetricsState,
    method: str,
    path: str,
    status_code: int,
    duration: float,
) -> None:
    """Record request-level metrics for a completed HTTP request.

    Args:
        state: MetricsState holding instrument references.
        method: HTTP method (GET, POST, etc.).
        path: Request path.
        status_code: HTTP response status code.
        duration: Request duration in seconds.
    """
    labels = {"method": method, "path": path, "status_code": str(status_code)}

    if state.request_duration is not None:
        state.request_duration.record(duration, attributes=labels)
    if state.request_count is not None:
        state.request_count.add(1, attributes=labels)

    if status_code >= HTTP_ERROR_STATUS_THRESHOLD and state.error_count is not None:
        state.error_count.add(1, attributes=labels)


def _increment_active_connections() -> None:
    """Increment active connection count and update peak if new high-water mark."""
    _metrics_state.active_connection_count += 1
    current = _metrics_state.active_connection_count
    _metrics_state.peak_active_connections = max(_metrics_state.peak_active_connections, current)


def _decrement_and_record(start_time: float, scope: Scope, status_code: int) -> None:
    """Decrement active connection count and record request metrics.

    Args:
        start_time: Monotonic timestamp when the request started.
        scope: The ASGI scope containing method and path.
        status_code: The HTTP response status code.
    """
    _metrics_state.active_connection_count -= 1
    duration = time.monotonic() - start_time
    _record_request_metrics(
        _metrics_state,
        method=scope.get("method", "UNKNOWN"),
        path=scope.get("path", "/"),
        status_code=status_code,
        duration=duration,
    )


class _MetricsASGIMiddleware:
    """Pure ASGI middleware that tracks active connections across the full request lifecycle.

    Unlike BaseHTTPMiddleware where call_next returns after headers, this wraps
    the entire ASGI call including response body streaming, ensuring the active
    connection counter accurately reflects in-flight requests.
    """

    def __init__(self, app: ASGIApp) -> None:
        """Initialize the middleware with the wrapped ASGI application.

        Args:
            app: The next ASGI application in the middleware chain.
        """
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Handle ASGI requests, tracking metrics for HTTP connections.

        Args:
            scope: The ASGI connection scope.
            receive: The ASGI receive callable.
            send: The ASGI send callable.
        """
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        _increment_active_connections()
        start_time = time.monotonic()
        status_code = 200

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 200)
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            _decrement_and_record(start_time, scope, status_code)


def configure_metrics(app: FastAPI) -> None:
    """Create metric instruments and add metrics middleware to the application.

    No-ops when OTEL_ENABLED environment variable is not set to 'true'.

    Args:
        app: The FastAPI application instance.
    """
    otel_enabled = os.getenv("OTEL_ENABLED", "false").lower() == "true"
    if not otel_enabled:
        return

    new_state = _create_instruments()
    _metrics_state.request_duration = new_state.request_duration
    _metrics_state.request_count = new_state.request_count
    _metrics_state.error_count = new_state.error_count

    app.add_middleware(_MetricsASGIMiddleware)
    logger.info("Metrics middleware configured with Four Golden Signals instruments")
