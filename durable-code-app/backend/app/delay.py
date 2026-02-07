"""
Purpose: Configurable delay endpoints for distributed tracing validation.

Scope: REST API endpoints producing multi-hop traces with controllable latency

Overview: Provides three delay endpoints (slow, med, fast) that sleep for randomized durations
    within defined ranges. A ?call= query parameter chains sequential HTTP calls to other delay
    endpoints, producing parent-child spans visible in Grafana Tempo. Chained calls omit the
    ?call= parameter to prevent infinite recursion. Each endpoint is rate-limited and traced
    with custom OpenTelemetry spans carrying delay.type, delay.chain_length, and delay.duration_ms
    attributes. The module supports the load-testing roadmap by generating continuous, varied
    distributed trace data across the observability pipeline.

Dependencies: FastAPI, httpx for chained HTTP calls, asyncio for async sleep, pydantic for
    response models, opentelemetry for custom tracing, slowapi for rate limiting

Exports: router (APIRouter with /api/delay prefix)

Interfaces: GET /api/delay/slow, GET /api/delay/med, GET /api/delay/fast, GET /api/delay/health

Implementation: Sequential chaining design where each chained call applies its own delay without
    forwarding the ?call= parameter. Uses httpx.AsyncClient with OpenTelemetry auto-instrumentation
    for trace context propagation. Max chain depth of 5 prevents abuse.
"""

import asyncio
import random
import time

import httpx
from fastapi import APIRouter, HTTPException, Request
from loguru import logger
from pydantic import BaseModel

from .core.telemetry import get_tracer
from .security import get_rate_limiter, get_security_config

# Cryptographically secure RNG for delay durations (avoids Bandit S311)
_secure_random = random.SystemRandom()

_tracer = get_tracer("durable-code.delay")

# Delay ranges in seconds for each endpoint type
DELAY_RANGES: dict[str, tuple[float, float]] = {
    "slow": (2.0, 3.0),
    "med": (0.5, 1.0),
    "fast": (0.05, 0.1),
}
VALID_DELAY_TYPES = frozenset(DELAY_RANGES.keys())
MAX_CHAIN_DEPTH = 5

# HTTP status codes
HTTP_BAD_REQUEST = 400

router = APIRouter(
    prefix="/api/delay",
    tags=["delay"],
)


class CallResult(BaseModel):
    """Result from a single chained delay call."""

    endpoint: str
    delay_ms: int


class DelayResponse(BaseModel):
    """Response from a delay endpoint including chained call results."""

    endpoint: str
    delay_ms: int
    calls: list[CallResult]
    total_ms: int


def _parse_call_chain(call_param: str | None) -> list[str]:
    """Parse the ?call= query parameter into a list of delay type names.

    Args:
        call_param: Comma-separated delay types (e.g. "fast,med") or None.

    Returns:
        List of delay type strings, empty if call_param is None or empty.
    """
    if not call_param:
        return []
    return [name.strip() for name in call_param.split(",") if name.strip()]


def _validate_chain(chain: list[str]) -> None:
    """Validate that all chain entries are valid delay types and within depth limit.

    Args:
        chain: List of delay type names to validate.

    Raises:
        HTTPException: If chain exceeds MAX_CHAIN_DEPTH or contains invalid types.
    """
    if len(chain) > MAX_CHAIN_DEPTH:
        raise HTTPException(
            status_code=HTTP_BAD_REQUEST,
            detail=f"Chain depth {len(chain)} exceeds maximum of {MAX_CHAIN_DEPTH}",
        )
    invalid = [name for name in chain if name not in VALID_DELAY_TYPES]
    if invalid:
        raise HTTPException(
            status_code=HTTP_BAD_REQUEST,
            detail=f"Invalid delay types: {', '.join(invalid)}. Valid: {', '.join(sorted(VALID_DELAY_TYPES))}",
        )


async def _apply_delay(delay_type: str) -> int:
    """Sleep for a random duration within the range for delay_type.

    Args:
        delay_type: One of 'slow', 'med', 'fast'.

    Returns:
        The actual delay applied in milliseconds.
    """
    low, high = DELAY_RANGES[delay_type]
    duration = _secure_random.uniform(low, high)
    with _tracer.start_as_current_span(
        "delay.sleep",
        attributes={"delay.type": delay_type, "delay.duration_ms": int(duration * 1000)},
    ):
        await asyncio.sleep(duration)
    return int(duration * 1000)


def _build_base_url(request: Request) -> str:
    """Extract the base URL from the incoming request for self-referencing calls.

    Args:
        request: The incoming FastAPI request.

    Returns:
        Base URL string (e.g. "http://localhost:8000").
    """
    return str(request.base_url).rstrip("/")


async def _execute_chain_calls(base_url: str, chain: list[str]) -> list[CallResult]:
    """Execute chained delay calls sequentially without forwarding ?call=.

    Args:
        base_url: The base URL for self-referencing calls.
        chain: List of delay types to call sequentially.

    Returns:
        List of CallResult with endpoint name and delay duration from each call.
    """
    results: list[CallResult] = []
    async with httpx.AsyncClient(timeout=30.0) as client:
        for delay_type in chain:
            url = f"{base_url}/api/delay/{delay_type}"
            with _tracer.start_as_current_span(
                "delay.chain_call",
                attributes={"delay.target": delay_type},
            ):
                response = await client.get(url)
                data = response.json()
                results.append(CallResult(endpoint=data["endpoint"], delay_ms=data["delay_ms"]))
    return results


async def _handle_delay(request: Request, delay_type: str, call: str | None) -> DelayResponse:
    """Orchestrate delay application and optional chain execution.

    Args:
        request: The incoming FastAPI request.
        delay_type: The delay type for this endpoint (slow, med, fast).
        call: Optional comma-separated chain of delay types to call after.

    Returns:
        DelayResponse with timing data for this endpoint and all chained calls.
    """
    start = time.monotonic()
    chain = _parse_call_chain(call)
    _validate_chain(chain)

    with _tracer.start_as_current_span(
        f"delay.handle.{delay_type}",
        attributes={"delay.type": delay_type, "delay.chain_length": len(chain)},
    ):
        delay_ms = await _apply_delay(delay_type)
        calls: list[CallResult] = []
        if chain:
            base_url = _build_base_url(request)
            calls = await _execute_chain_calls(base_url, chain)

    total_ms = int((time.monotonic() - start) * 1000)
    logger.info("Delay endpoint completed", delay_type=delay_type, delay_ms=delay_ms, chain_length=len(chain))
    return DelayResponse(endpoint=delay_type, delay_ms=delay_ms, calls=calls, total_ms=total_ms)


@router.get("/slow", response_model=DelayResponse)
@get_rate_limiter().limit(get_security_config("api_data")["rate_limit"])
async def delay_slow(request: Request, call: str | None = None) -> DelayResponse:
    """Delay endpoint sleeping 2-3 seconds with optional chaining.

    Args:
        request: FastAPI request object.
        call: Optional comma-separated delay types to chain (e.g. "med,fast").

    Returns:
        DelayResponse with timing data.
    """
    return await _handle_delay(request, "slow", call)


@router.get("/med", response_model=DelayResponse)
@get_rate_limiter().limit(get_security_config("api_data")["rate_limit"])
async def delay_med(request: Request, call: str | None = None) -> DelayResponse:
    """Delay endpoint sleeping 0.5-1 second with optional chaining.

    Args:
        request: FastAPI request object.
        call: Optional comma-separated delay types to chain (e.g. "slow,fast").

    Returns:
        DelayResponse with timing data.
    """
    return await _handle_delay(request, "med", call)


@router.get("/fast", response_model=DelayResponse)
@get_rate_limiter().limit(get_security_config("api_data")["rate_limit"])
async def delay_fast(request: Request, call: str | None = None) -> DelayResponse:
    """Delay endpoint sleeping 50-100ms with optional chaining.

    Args:
        request: FastAPI request object.
        call: Optional comma-separated delay types to chain (e.g. "slow,med").

    Returns:
        DelayResponse with timing data.
    """
    return await _handle_delay(request, "fast", call)


@router.get("/health", include_in_schema=False)
@get_rate_limiter().limit(get_security_config("health_check")["rate_limit"])
async def delay_health(request: Request) -> dict[str, str]:
    """Health check endpoint for the delay module."""
    return {"status": "healthy", "module": "delay"}
