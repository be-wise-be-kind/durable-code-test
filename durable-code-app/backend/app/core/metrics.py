"""
Purpose: Four Golden Signals HTTP metrics collection via OpenTelemetry and FastAPI middleware.

Scope: Backend application request-level metrics for latency, traffic, errors, and saturation

Overview: Implements the Four Golden Signals metrics pattern using OpenTelemetry instruments
    and a FastAPI middleware. Captures request duration (latency), request count (traffic),
    error count (errors), and active connection gauge (saturation) for all HTTP requests.
    Metrics are exported to Grafana Mimir via the MeterProvider configured in telemetry.py.
    The middleware records timing and status for every request, with method and path labels
    for per-endpoint analysis. All instrumentation is gated behind the OTEL_ENABLED
    environment variable.

Dependencies: opentelemetry-api, opentelemetry-sdk, FastAPI, starlette

Exports: configure_metrics

Interfaces: configure_metrics(app: FastAPI) creates metric instruments and adds
    the MetricsMiddleware to the application

Implementation: Uses OpenTelemetry Histogram, Counter, and UpDownCounter instruments.
    MetricsMiddleware wraps each request to record duration, increment counters, and
    track active connections. Metric names follow OpenTelemetry semantic conventions.
"""

from __future__ import annotations

import os
import time
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from fastapi import FastAPI
    from opentelemetry.metrics import Counter, Histogram, UpDownCounter
    from starlette.requests import Request
    from starlette.responses import Response


class MetricsState:
    """Holds references to OpenTelemetry metric instruments."""

    def __init__(self) -> None:
        """Initialize metric instrument references as None until created."""
        self.request_duration: Histogram | None = None
        self.request_count: Counter | None = None
        self.error_count: Counter | None = None
        self.active_connections: UpDownCounter | None = None


_metrics_state = MetricsState()

HTTP_ERROR_STATUS_THRESHOLD = 400


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
    state.active_connections = meter.create_up_down_counter(
        name="http_active_connections",
        description="Number of active HTTP connections",
        unit="1",
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
    _metrics_state.active_connections = new_state.active_connections

    from starlette.middleware.base import BaseHTTPMiddleware

    class MetricsMiddleware(BaseHTTPMiddleware):
        """Middleware that records HTTP request metrics for the Four Golden Signals."""

        async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
            """Record timing, request count, errors, and active connections.

            Args:
                request: The incoming HTTP request.
                call_next: The next middleware or route handler.

            Returns:
                The HTTP response from the downstream handler.
            """
            if _metrics_state.active_connections is not None:
                _metrics_state.active_connections.add(1)
            start_time = time.monotonic()

            response = await call_next(request)

            duration = time.monotonic() - start_time
            _record_request_metrics(
                _metrics_state,
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration=duration,
            )
            if _metrics_state.active_connections is not None:
                _metrics_state.active_connections.add(-1)
            return response

    app.add_middleware(MetricsMiddleware)
    logger.info("Metrics middleware configured with Four Golden Signals instruments")
