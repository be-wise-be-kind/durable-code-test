"""
Purpose: HTTP load test scenarios exercising all backend REST endpoints

Scope: Locust HttpUser definition targeting the Durable Code backend API

Overview: Defines a BackendHttpUser class that exercises all HTTP REST endpoints exposed by the
    FastAPI backend. Tasks are weighted to simulate realistic traffic patterns, with health checks
    and read-heavy endpoints receiving higher weights. Delay endpoints generate distributed traces
    with configurable chaining depth. Locust natively reports non-2xx responses as failures. The
    host defaults to LOCUST_HOST environment variable, enabling flexible targeting of local
    development, staging, or production instances.

Dependencies: Locust framework (HttpUser, task, between), random (SystemRandom)

Exports: BackendHttpUser class for use by Locust master/worker processes

Interfaces: All backend REST endpoints: /, /health, /api/racing/*, /api/oscilloscope/*,
    /api/delay/*

Implementation: Weighted task distribution reflecting realistic usage patterns with Locust
    native response status validation
"""

import random

from locust import HttpUser, between, task

# Cryptographically secure RNG for load test randomization (avoids Bandit S311)
_secure_random = random.SystemRandom()

_DELAY_TYPES = ["slow", "med", "fast"]


def _random_call_chain() -> str:
    """Build a random ?call= query string for delay endpoint chaining.

    Returns:
        Query string with ?call= parameter, or empty string for no chaining.
        40% chance of no chain, 60% chance of 1-3 chained calls.
    """
    if _secure_random.random() < 0.4:
        return ""
    count = _secure_random.randint(1, 3)
    targets = [_secure_random.choice(_DELAY_TYPES) for _ in range(count)]
    return f"?call={','.join(targets)}"


class BackendHttpUser(HttpUser):
    """Simulates HTTP traffic against all backend REST endpoints."""

    wait_time = between(1, 3)

    @task(3)
    def health_check(self) -> None:
        """High-frequency health check endpoint."""
        self.client.get("/health")

    @task(1)
    def root(self) -> None:
        """Root endpoint returning welcome message."""
        self.client.get("/")

    @task(2)
    def racing_track_simple(self) -> None:
        """Fetch a simple oval track."""
        self.client.get("/api/racing/track/simple")

    @task(1)
    def racing_track_generate(self) -> None:
        """Generate a procedural track with default parameters."""
        self.client.post("/api/racing/track/generate", json={})

    @task(1)
    def racing_health(self) -> None:
        """Racing API health check."""
        self.client.get("/api/racing/health")

    @task(2)
    def oscilloscope_config(self) -> None:
        """Fetch oscilloscope configuration and supported parameters."""
        self.client.get("/api/oscilloscope/config")

    @task(1)
    def oscilloscope_stream_info(self) -> None:
        """Fetch WebSocket streaming endpoint information."""
        self.client.get("/api/oscilloscope/stream/info")

    @task(1)
    def oscilloscope_health(self) -> None:
        """Oscilloscope API health check."""
        self.client.get("/api/oscilloscope/health")

    @task(2)
    def delay_slow(self) -> None:
        """Slow delay endpoint with random chaining for distributed traces."""
        self.client.get(f"/api/delay/slow{_random_call_chain()}")

    @task(3)
    def delay_med(self) -> None:
        """Medium delay endpoint with random chaining for distributed traces."""
        self.client.get(f"/api/delay/med{_random_call_chain()}")

    @task(4)
    def delay_fast(self) -> None:
        """Fast delay endpoint with random chaining for distributed traces."""
        self.client.get(f"/api/delay/fast{_random_call_chain()}")

    @task(1)
    def delay_health(self) -> None:
        """Delay API health check."""
        self.client.get("/api/delay/health")
