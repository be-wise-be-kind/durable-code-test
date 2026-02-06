# Purpose: Container image for Locust load testing framework with HTTP and WebSocket support
# Scope: Build configuration for the load testing service targeting deployed web instances
# Overview: Builds a lightweight Locust container using python:3.11-slim as the base image,
#     matching the backend Python version. Installs project dependencies (Locust, websockets)
#     via pip from pyproject.toml, copies locustfiles and the lib shared utility package into
#     the container, and runs as a non-root user for security. Exposes port 8089 for the
#     Locust web UI. The container targets external URLs (deployed web instances) rather than
#     Docker-internal service names, with the target host configurable via LOCUST_HOST
#     environment variable.
# Dependencies: python:3.11-slim base image, pyproject.toml for pip dependencies
# Exports: Locust container image with HTTP and WebSocket load test scenarios
# Interfaces: Port 8089 (Locust web UI), LOCUST_HOST environment variable for target URL
# Environment: Docker container runtime, targets deployed web instances
# Related: docker-compose.yml for orchestration, locustfiles/ for test scenarios, lib/ for shared utilities
# Implementation: Single-stage build with non-root user, pip install from pyproject.toml

FROM python:3.11-slim

WORKDIR /load-testing

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY locustfiles/ locustfiles/
COPY lib/ lib/

RUN useradd --create-home locust
USER locust

EXPOSE 8089

ENTRYPOINT ["locust"]
