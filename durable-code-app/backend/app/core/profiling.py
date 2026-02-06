"""
Purpose: Pyroscope push-based continuous profiling configuration for CPU and memory analysis.

Scope: Backend application continuous profiling with Pyroscope SDK integration

Overview: Configures the Pyroscope SDK for push-based continuous profiling, sending CPU and
    memory profile data to the Pyroscope server running in the Grafana observability stack.
    Profiling is gated behind the PYROSCOPE_ENABLED environment variable, separate from
    OTEL_ENABLED, because profiling has higher CPU overhead and may need independent control.
    Tags include environment and service name for filtering profiles in the Grafana UI.

Dependencies: pyroscope-io SDK

Exports: configure_profiling, profile_with_trace_context

Interfaces: configure_profiling() initializes Pyroscope push-mode profiling when enabled;
    profile_with_trace_context() context manager tags profiles with OTel trace_id/span_id

Implementation: Uses pyroscope.configure() with push mode to send profiles to the Pyroscope
    server. Server address is provided via PYROSCOPE_SERVER_ADDRESS environment variable,
    set by Terraform to the EC2 observability instance private IP on port 4040. The
    profile_with_trace_context() context manager uses pyroscope.tag_wrapper to inject
    trace_id and span_id from the active OTel span context into profile tags, enabling
    trace-to-profile correlation in Grafana.
"""

from __future__ import annotations

import contextlib
import os
from collections.abc import Generator

from loguru import logger


def configure_profiling() -> None:
    """Configure Pyroscope continuous profiling in push mode.

    No-ops when PYROSCOPE_ENABLED environment variable is not set to 'true'.
    Profiling has higher CPU overhead than tracing/metrics, so it uses a separate
    feature flag for independent control.
    """
    pyroscope_enabled = os.getenv("PYROSCOPE_ENABLED", "false").lower() == "true"
    if not pyroscope_enabled:
        logger.info("Pyroscope profiling disabled (PYROSCOPE_ENABLED != 'true')")
        return

    server_address = os.getenv("PYROSCOPE_SERVER_ADDRESS", "http://localhost:4040")
    service_name = os.getenv("OTEL_SERVICE_NAME", "durable-code-backend")
    environment = os.getenv("ENVIRONMENT", "dev")

    try:
        import pyroscope

        pyroscope.configure(
            application_name=service_name,
            server_address=server_address,
            tags={"environment": environment, "service": service_name},
        )
        logger.info("Pyroscope profiling configured (push mode)")
    except ImportError:
        logger.warning("pyroscope-io package not installed, profiling disabled")


class _ProfilingState:
    """Container for profiling enablement state used by trace context tagging."""

    def __init__(self) -> None:
        """Initialize profiling state flags."""
        self.pyroscope_enabled: bool = False
        self.otel_enabled: bool = False


_profiling_state = _ProfilingState()
_profiling_state.pyroscope_enabled = os.getenv("PYROSCOPE_ENABLED", "false").lower() == "true"
_profiling_state.otel_enabled = os.getenv("OTEL_ENABLED", "false").lower() == "true"


def _should_tag_profiles() -> bool:
    """Check whether profiles should be tagged with trace context.

    Returns True only when both Pyroscope and OpenTelemetry are enabled,
    since trace_id/span_id tagging requires both systems to be active.

    Returns:
        True if profile tagging is appropriate.
    """
    return _profiling_state.pyroscope_enabled and _profiling_state.otel_enabled


@contextlib.contextmanager
def profile_with_trace_context() -> Generator[None, None, None]:
    """Tag Pyroscope profiling with active OTel trace context for flame graph correlation.

    When both Pyroscope and OpenTelemetry are enabled, wraps the enclosed code block
    with pyroscope.tag_wrapper injecting trace_id and span_id from the active span
    context. This enables navigating from a Tempo trace to the corresponding Pyroscope
    flame graph in Grafana.

    When either system is disabled, yields without tagging (no-op).

    Yields:
        None
    """
    if not _should_tag_profiles():
        yield
        return

    try:
        from opentelemetry import trace

        span = trace.get_current_span()
        span_context = span.get_span_context()

        if span_context.trace_id == 0:
            yield
            return

        trace_id = format(span_context.trace_id, "032x")
        span_id = format(span_context.span_id, "016x")

        import pyroscope

        with pyroscope.tag_wrapper({"trace_id": trace_id, "span_id": span_id}):
            yield

    except (ImportError, AttributeError):
        yield
