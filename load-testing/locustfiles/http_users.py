"""
Purpose: HTTP load test scenarios exercising all backend REST endpoints

Scope: Locust HttpUser definition targeting the Durable Code backend API

Overview: Defines a BackendHttpUser class that exercises all HTTP REST endpoints exposed by the
    FastAPI backend. Tasks are weighted to simulate realistic traffic patterns, with health checks
    and read-heavy endpoints receiving higher weights. Each task validates the response status code
    to detect errors under load. The host defaults to LOCUST_HOST environment variable, enabling
    flexible targeting of local development, staging, or production instances.

Dependencies: Locust framework (HttpUser, task, between)

Exports: BackendHttpUser class for use by Locust master/worker processes

Interfaces: All backend REST endpoints: /, /health, /api/racing/*, /api/oscilloscope/*

Implementation: Weighted task distribution reflecting realistic usage patterns with response
    status code validation on each request
"""

from locust import HttpUser, between, task


class BackendHttpUser(HttpUser):
    """Simulates HTTP traffic against all backend REST endpoints."""

    wait_time = between(1, 3)

    @task(3)
    def health_check(self) -> None:
        """High-frequency health check endpoint."""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Status {response.status_code}")

    @task(1)
    def root(self) -> None:
        """Root endpoint returning welcome message."""
        with self.client.get("/", catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Status {response.status_code}")

    @task(2)
    def racing_track_simple(self) -> None:
        """Fetch a simple oval track."""
        with self.client.get(
            "/api/racing/track/simple", catch_response=True
        ) as response:
            if response.status_code != 200:
                response.failure(f"Status {response.status_code}")

    @task(1)
    def racing_track_generate(self) -> None:
        """Generate a procedural track with default parameters."""
        with self.client.post(
            "/api/racing/track/generate",
            json={},
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"Status {response.status_code}")

    @task(1)
    def racing_health(self) -> None:
        """Racing API health check."""
        with self.client.get(
            "/api/racing/health", catch_response=True
        ) as response:
            if response.status_code != 200:
                response.failure(f"Status {response.status_code}")

    @task(2)
    def oscilloscope_config(self) -> None:
        """Fetch oscilloscope configuration and supported parameters."""
        with self.client.get(
            "/api/oscilloscope/config", catch_response=True
        ) as response:
            if response.status_code != 200:
                response.failure(f"Status {response.status_code}")

    @task(1)
    def oscilloscope_stream_info(self) -> None:
        """Fetch WebSocket streaming endpoint information."""
        with self.client.get(
            "/api/oscilloscope/stream/info", catch_response=True
        ) as response:
            if response.status_code != 200:
                response.failure(f"Status {response.status_code}")

    @task(1)
    def oscilloscope_health(self) -> None:
        """Oscilloscope API health check."""
        with self.client.get(
            "/api/oscilloscope/health", catch_response=True
        ) as response:
            if response.status_code != 200:
                response.failure(f"Status {response.status_code}")
