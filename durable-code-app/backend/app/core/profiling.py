"""
Purpose: Pyroscope push-based continuous profiling configuration for CPU and memory analysis.

Scope: Backend application continuous profiling with Pyroscope SDK integration

Overview: Configures the Pyroscope SDK for push-based continuous profiling, sending CPU and
    memory profile data to the Pyroscope server running in the Grafana observability stack.
    Profiling is gated behind the PYROSCOPE_ENABLED environment variable, separate from
    OTEL_ENABLED, because profiling has higher CPU overhead and may need independent control.
    Tags include environment and service name for filtering profiles in the Grafana UI.

Dependencies: pyroscope-io SDK

Exports: configure_profiling

Interfaces: configure_profiling() initializes Pyroscope push-mode profiling when enabled

Implementation: Uses pyroscope.configure() with push mode to send profiles to the Pyroscope
    server. Server address is provided via PYROSCOPE_SERVER_ADDRESS environment variable,
    set by Terraform to the EC2 observability instance private IP on port 4040.
"""

from __future__ import annotations

import os

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
