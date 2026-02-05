"""
Purpose: OpenTelemetry TracerProvider and MeterProvider configuration with OTLP gRPC export.

Scope: Backend application distributed tracing and metrics collection infrastructure

Overview: Configures OpenTelemetry TracerProvider and MeterProvider with OTLP gRPC exporters
    for sending traces and metrics to the Grafana Alloy collector. Instruments the FastAPI
    application with automatic span creation for HTTP requests. All instrumentation is gated
    behind the OTEL_ENABLED environment variable, ensuring zero overhead when disabled.
    Functions are decomposed to maintain low cyclomatic complexity. OTel imports are placed
    inside helper functions to avoid import errors in environments without the full dependency
    chain installed.

Dependencies: opentelemetry-api, opentelemetry-sdk, opentelemetry-exporter-otlp-proto-grpc,
    opentelemetry-instrumentation-fastapi, FastAPI

Exports: configure_telemetry, shutdown_telemetry

Interfaces: configure_telemetry(app: FastAPI) initializes tracing and metrics;
    shutdown_telemetry() flushes and shuts down providers

Implementation: Uses OTLP gRPC protocol for export, TraceIdRatioBased sampler for head-based
    sampling, and BatchSpanProcessor for efficient span batching. Resource attributes identify
    the service in the Grafana stack backends.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from fastapi import FastAPI
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider


class _TelemetryState:
    """Container for module-level provider references used during shutdown."""

    def __init__(self) -> None:
        """Initialize provider references as None until configured."""
        self.tracer_provider: TracerProvider | None = None
        self.meter_provider: MeterProvider | None = None


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

    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    exporter = OTLPMetricExporter(endpoint=endpoint, insecure=True)
    reader = PeriodicExportingMetricReader(exporter, export_interval_millis=60000)

    provider = MeterProvider(resource=resource, metric_readers=[reader])

    from opentelemetry.metrics import set_meter_provider

    set_meter_provider(provider)
    _state.meter_provider = provider


def _instrument_fastapi(app: FastAPI) -> None:
    """Instrument the FastAPI application for automatic HTTP span creation."""
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

    FastAPIInstrumentor.instrument_app(app)


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
    _instrument_fastapi(app)
    logger.info("OpenTelemetry configured with OTLP gRPC export")


def shutdown_telemetry() -> None:
    """Flush and shut down OpenTelemetry providers for clean application exit."""
    if _state.tracer_provider is not None:
        _state.tracer_provider.shutdown()
    if _state.meter_provider is not None:
        _state.meter_provider.shutdown()
