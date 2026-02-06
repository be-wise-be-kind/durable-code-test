"""
Purpose: OpenTelemetry TracerProvider and MeterProvider configuration with OTLP gRPC export.

Scope: Backend application distributed tracing and metrics collection infrastructure

Overview: Configures OpenTelemetry TracerProvider, MeterProvider, and LoggerProvider with OTLP
    gRPC exporters for sending traces, metrics, and logs to the Grafana Alloy collector.
    Instruments the FastAPI application with automatic span creation for HTTP requests. The
    LoggerProvider attaches a LoggingHandler to the standard logging root logger, enabling
    Loguru messages bridged via logging_config.py to flow through OTLP to Alloy and then Loki.
    All instrumentation is gated behind the OTEL_ENABLED environment variable, ensuring zero
    overhead when disabled. Functions are decomposed to maintain low cyclomatic complexity.
    OTel imports are placed inside helper functions to avoid import errors in environments
    without the full dependency chain installed.

Dependencies: opentelemetry-api, opentelemetry-sdk, opentelemetry-exporter-otlp-proto-grpc,
    opentelemetry-instrumentation-fastapi, FastAPI

Exports: configure_telemetry, shutdown_telemetry, get_tracer

Interfaces: configure_telemetry(app: FastAPI) initializes tracing and metrics;
    shutdown_telemetry() flushes and shuts down providers;
    get_tracer(name) returns a Tracer instance (no-op when OTel disabled)

Implementation: Uses OTLP gRPC protocol for export, TraceIdRatioBased sampler for head-based
    sampling, and BatchSpanProcessor for efficient span batching. Resource attributes identify
    the service in the Grafana stack backends. A server_request_hook enriches auto-instrumented
    FastAPI spans with deployment.environment attribute.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from fastapi import FastAPI
    from opentelemetry.sdk._logs import LoggerProvider
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.trace import Tracer


class _TelemetryState:
    """Container for module-level provider references used during shutdown."""

    def __init__(self) -> None:
        """Initialize provider references as None until configured."""
        self.tracer_provider: TracerProvider | None = None
        self.meter_provider: MeterProvider | None = None
        self.logger_provider: LoggerProvider | None = None


_state = _TelemetryState()


def _is_telemetry_enabled() -> bool:
    """Check whether OpenTelemetry instrumentation is enabled via environment variable."""
    return os.getenv("OTEL_ENABLED", "false").lower() == "true"


def _build_resource() -> Resource:
    """Build an OpenTelemetry Resource with service identification attributes."""
    from opentelemetry.sdk.resources import Resource as OTelResource

    service_name = os.getenv("OTEL_SERVICE_NAME", "durable-code-backend")
    environment = os.getenv("ENVIRONMENT", "dev")

    return OTelResource.create(
        {
            "service.name": service_name,
            "service.namespace": "durable-code",
            "deployment.environment": environment,
        }
    )


def _configure_tracer_provider(resource: Resource) -> None:
    """Configure TracerProvider with BatchSpanProcessor and OTLP gRPC exporter."""
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.trace.sampling import TraceIdRatioBased
    from opentelemetry.trace import set_tracer_provider

    sampler_arg = float(os.getenv("OTEL_TRACES_SAMPLER_ARG", "1.0"))
    sampler = TraceIdRatioBased(sampler_arg)

    provider = TracerProvider(resource=resource, sampler=sampler)

    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(exporter))

    set_tracer_provider(provider)
    _state.tracer_provider = provider


def _configure_meter_provider(resource: Resource) -> None:
    """Configure MeterProvider with PeriodicExportingMetricReader and OTLP gRPC exporter."""
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    from opentelemetry.sdk.metrics.view import ExplicitBucketHistogramAggregation, View

    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    exporter = OTLPMetricExporter(endpoint=endpoint, insecure=True)
    reader = PeriodicExportingMetricReader(exporter, export_interval_millis=60000)

    duration_view = View(
        instrument_name="http_request_duration_seconds",
        aggregation=ExplicitBucketHistogramAggregation(
            boundaries=[
                0.005,
                0.01,
                0.025,
                0.05,
                0.075,
                0.1,
                0.25,
                0.5,
                0.75,
                1.0,
                2.5,
                5.0,
                7.5,
                10.0,
            ]
        ),
    )

    provider = MeterProvider(resource=resource, metric_readers=[reader], views=[duration_view])

    from opentelemetry.metrics import set_meter_provider

    set_meter_provider(provider)
    _state.meter_provider = provider


def _configure_logger_provider(resource: Resource) -> None:
    """Configure LoggerProvider with BatchLogRecordProcessor and OTLP gRPC exporter.

    Sets up the OTel logging pipeline and attaches a LoggingHandler to the
    standard logging root logger. Loguru messages bridged to standard logging
    (via logging_config.py) flow through this handler to Alloy and then Loki.
    """
    import logging

    from opentelemetry._logs import set_logger_provider
    from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
    from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
    from opentelemetry.sdk._logs.export import BatchLogRecordProcessor

    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    exporter = OTLPLogExporter(endpoint=endpoint, insecure=True)

    provider = LoggerProvider(resource=resource)
    provider.add_log_record_processor(BatchLogRecordProcessor(exporter))
    set_logger_provider(provider)

    handler = LoggingHandler(level=logging.INFO, logger_provider=provider)
    logging.getLogger().addHandler(handler)

    _state.logger_provider = provider


def _server_request_hook(span: object, scope: dict[str, object]) -> None:
    """Enrich auto-instrumented FastAPI spans with custom attributes.

    Adds deployment.environment to every incoming request span for filtering
    traces by environment in Grafana Tempo.

    Args:
        span: The OpenTelemetry Span object for the request.
        scope: The ASGI scope dictionary for the request.
    """
    from opentelemetry.trace import Span

    if isinstance(span, Span) and span.is_recording():
        environment = os.getenv("ENVIRONMENT", "dev")
        span.set_attribute("deployment.environment", environment)


def _instrument_fastapi(app: FastAPI) -> None:
    """Instrument the FastAPI application for automatic HTTP span creation."""
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

    FastAPIInstrumentor.instrument_app(app, server_request_hook=_server_request_hook)


def configure_telemetry(app: FastAPI) -> None:
    """Configure OpenTelemetry tracing and metrics for the application.

    No-ops when OTEL_ENABLED environment variable is not set to 'true'.
    Initializes TracerProvider, MeterProvider, and instruments FastAPI.

    Args:
        app: The FastAPI application instance to instrument.
    """
    if not _is_telemetry_enabled():
        logger.info("OpenTelemetry disabled (OTEL_ENABLED != 'true')")
        return

    resource = _build_resource()
    _configure_tracer_provider(resource)
    _configure_meter_provider(resource)
    _configure_logger_provider(resource)
    _instrument_fastapi(app)
    logger.info("OpenTelemetry configured with OTLP gRPC export (traces, metrics, logs)")


def shutdown_telemetry() -> None:
    """Flush and shut down OpenTelemetry providers for clean application exit."""
    if _state.tracer_provider is not None:
        _state.tracer_provider.shutdown()
    if _state.meter_provider is not None:
        _state.meter_provider.shutdown()
    if _state.logger_provider is not None:
        _state.logger_provider.shutdown()


def get_tracer(name: str) -> Tracer:
    """Return a Tracer instance for creating custom spans.

    Returns a no-op tracer when OpenTelemetry is disabled, so callers can
    unconditionally use trace.get_tracer() without checking enablement.

    Args:
        name: The instrumentation scope name for the tracer.

    Returns:
        An OpenTelemetry Tracer (real or no-op).
    """
    from opentelemetry import trace

    return trace.get_tracer(name)
