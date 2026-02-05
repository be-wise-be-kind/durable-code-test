"""
Purpose: Structured JSON logging with OpenTelemetry trace context injection for loguru.

Scope: Backend application logging configuration for observability correlation

Overview: Provides a structured JSON loguru sink that embeds OpenTelemetry trace_id and
    span_id into every log line, enabling log-to-trace correlation in Grafana Loki. Extracts
    span context from the active OpenTelemetry span and formats log records as JSON with
    all extra fields preserved. Only replaces the default loguru handler when OTEL_ENABLED
    is set to 'true', preserving the developer-friendly default format in local development.

Dependencies: loguru, opentelemetry-api (optional, used when OTEL_ENABLED)

Exports: configure_logging

Interfaces: configure_logging() replaces default loguru handler with JSON sink when
    telemetry is enabled

Implementation: Uses loguru's custom sink mechanism with a JSON formatter that extracts
    OTel span context via trace.get_current_span(). Trace and span IDs are formatted as
    zero-padded hex strings matching the W3C Trace Context specification.
"""

from __future__ import annotations

import json
import os
import sys
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from loguru import Message


def _get_trace_context() -> dict[str, str]:
    """Extract trace_id and span_id from the active OpenTelemetry span context.

    Returns zero-valued IDs when no active span exists or when OTel is unavailable.
    """
    try:
        from opentelemetry import trace

        span = trace.get_current_span()
        ctx = span.get_span_context()
        if ctx and ctx.trace_id != 0:
            return {
                "trace_id": f"{ctx.trace_id:032x}",
                "span_id": f"{ctx.span_id:016x}",
            }
    except ImportError:
        pass

    return {"trace_id": "0" * 32, "span_id": "0" * 16}


def _json_sink(message: Message) -> None:
    """Write a structured JSON log line to stdout with trace context and extra fields.

    Args:
        message: The loguru Message object containing the log record.
    """
    record = message.record
    trace_ctx = _get_trace_context()

    log_entry: dict[str, object] = {
        "timestamp": record["time"].isoformat(),
        "level": record["level"].name,
        "message": record["message"],
        "logger": record["name"],
        "module": record["module"],
        "function": record["function"],
        "line": record["line"],
        "trace_id": trace_ctx["trace_id"],
        "span_id": trace_ctx["span_id"],
    }

    extra = record.get("extra", {})
    if extra:
        log_entry["extra"] = {k: str(v) for k, v in extra.items()}

    sys.stdout.write(json.dumps(log_entry) + "\n")
    sys.stdout.flush()


def configure_logging() -> None:
    """Configure structured JSON logging when OpenTelemetry is enabled.

    Replaces the default loguru handler with a JSON sink that includes trace context.
    No-ops when OTEL_ENABLED is not 'true', preserving default loguru formatting.
    """
    otel_enabled = os.getenv("OTEL_ENABLED", "false").lower() == "true"
    if not otel_enabled:
        logger.info("Structured JSON logging disabled (OTEL_ENABLED != 'true')")
        return

    logger.remove()
    logger.add(_json_sink, level="INFO")
    logger.info("Structured JSON logging configured with trace context injection")
