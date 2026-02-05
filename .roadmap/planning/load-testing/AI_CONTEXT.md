# Locust Load Testing - AI Context

**Purpose**: AI agent context document for implementing Locust Load Testing

**Scope**: Load testing infrastructure for HTTP and WebSocket endpoints with metrics export and Grafana integration

**Overview**: Comprehensive context document for AI agents working on the Locust Load Testing feature.
    Covers the rationale for choosing Locust over alternatives, project structure decisions, Docker setup,
    justfile dispatch patterns, metrics export strategy, WebSocket testing approach, and integration with
    the Grafana observability stack. Provides guidance for implementing each PR with awareness of the
    existing codebase patterns and infrastructure.

**Dependencies**: FastAPI backend API, WebSocket oscilloscope service, Docker Compose, durable-network-dev, Grafana observability stack (optional for PRs 4-5)

**Exports**: Architecture decisions, tool selection rationale, integration patterns, and implementation guidance

**Related**: PR_BREAKDOWN.md for implementation tasks, PROGRESS_TRACKER.md for current status

**Implementation**: Phased PR approach with foundation-first, protocol-coverage-second, integration-third strategy

---

## Overview
This feature adds load testing capability to the Durable Code application using Locust, a Python-based load testing framework. It exercises all HTTP REST endpoints and the WebSocket oscilloscope service under configurable load patterns, exports metrics in Prometheus format, and integrates with the Grafana observability stack for visual analysis.

## Project Background
The Durable Code Test project has a FastAPI backend with REST endpoints and a WebSocket-based oscilloscope service, plus a React/TypeScript frontend. The application runs in Docker containers on a shared `durable-network-dev` network during development. Load testing validates that the backend handles concurrent requests and sustained WebSocket connections without degradation. The project uses a justfile-based command dispatch pattern (`just infra`, `just dev`, etc.) that the load testing feature extends.

## Feature Vision
- **Protocol Coverage**: Test both HTTP REST endpoints and WebSocket connections under load
- **Configurable Profiles**: Preset load patterns (smoke, load, stress, soak) for different testing scenarios
- **Metrics Export**: Prometheus-format metrics for quantitative analysis and alerting
- **Observability Integration**: Grafana dashboard correlating load test metrics with application metrics
- **Developer Experience**: Simple `just load-test` commands matching existing project patterns

## Current Application Context
- **Backend**: FastAPI with REST endpoints under `/api/` and WebSocket at `/api/oscilloscope/ws`
- **Frontend**: React/TypeScript SPA (not directly load-tested; backend is the target)
- **Docker**: Services connected via `durable-network-dev` bridge network
- **Justfile**: Command dispatch pattern with subcommands (e.g., `just infra plan base`)
- **Observability**: Grafana stack (Mimir, Loki, Tempo, Pyroscope) behind `enable_observability` feature flag

## Target Architecture

### Core Components

```
[Locust Master :8089]  ──── Web UI (browser)
        │
        ├── [Worker 1] ──── HTTP tasks ──→ [Backend :8000/api/*]
        ├── [Worker N] ──── HTTP tasks ──→ [Backend :8000/api/*]
        │
        ├── [Worker 1] ──── WS tasks ───→ [Backend :8000/api/oscilloscope/ws]
        ├── [Worker N] ──── WS tasks ───→ [Backend :8000/api/oscilloscope/ws]
        │
        └── [:9646/metrics] ──→ [Alloy] ──→ [Mimir] ──→ [Grafana Dashboard]
```

### Project Structure
```
load-testing/
├── Dockerfile                    # Based on locustio/locust
├── docker-compose.yml            # Master + worker services
├── requirements.txt              # Python dependencies
├── locustfiles/
│   ├── __init__.py
│   ├── http_users.py             # HttpUser for REST endpoints
│   ├── websocket_users.py        # Custom User for WebSocket
│   └── mixed_users.py            # Combined scenarios
├── profiles/
│   ├── smoke.yml                 # Quick validation (5 users, 30s)
│   ├── load.yml                  # Standard load (50 users, 5m)
│   ├── stress.yml                # Breaking point (200 users, 10m)
│   └── soak.yml                  # Stability (30 users, 30m)
└── lib/
    ├── __init__.py
    ├── websocket_client.py       # Async WS client with Locust event reporting
    ├── profile_loader.py         # YAML profile parser
    └── metrics_exporter.py       # Prometheus metrics server
```

### Justfile Dispatch Pattern
```
just load-test run [--profile <name>]    # Headless test execution
just load-test ui                         # Start web UI on :8089
just load-test stop                       # Shut down all containers
just load-test status                     # Show container status
just load-test report                     # Open Grafana dashboard URL
```

This mirrors the existing `just infra [subcommand]` dispatch pattern used throughout the project.

## Key Decisions Made

### 1. Locust over k6
**Decision**: Use Locust as the load testing framework
**Rationale**: Locust is Python-native, matching the FastAPI backend language. This allows developers to write test scenarios in familiar syntax, reuse backend data models, and share utility code. Locust provides a built-in web UI for real-time monitoring during test runs. While k6 offers higher per-instance throughput via Go, Locust's Python ecosystem and WebSocket flexibility (via custom User classes) better fit this project's needs.

### 2. Top-Level `load-testing/` Directory
**Decision**: Place load testing in a top-level `load-testing/` directory
**Rationale**: Follows the project's concern-separation pattern where `durable-code-app/`, `infra/`, and `tools/` each occupy top-level directories. Load testing is a distinct concern from application code and infrastructure, warranting its own directory rather than nesting under `test/` (which contains unit/integration tests).

### 3. Dedicated Docker Compose
**Decision**: Separate `docker-compose.yml` in `load-testing/` rather than adding to the main compose file
**Rationale**: Load testing is an optional, on-demand activity. Separating it prevents load test containers from starting during normal development (`just dev`). The Locust containers connect to the existing `durable-network-dev` as an external network, enabling communication with the backend without coupling lifecycles.

### 4. Master+Worker Pattern
**Decision**: Docker Compose with separate master and worker services
**Rationale**: The master handles the web UI, statistics aggregation, and metrics export. Workers perform the actual load generation. This pattern supports scaling workers (`--scale worker=N`) for higher load without changing configuration. It also prepares the architecture for distributed testing across multiple machines.

### 5. Custom WebSocket User Class
**Decision**: Implement a custom `User` class with the `websockets` library instead of seeking a Locust WebSocket plugin
**Rationale**: Locust does not have built-in WebSocket support. The oscilloscope WebSocket service uses a specific protocol (start/receive/configure/stop) that requires custom message sequencing. Using the `websockets` library directly provides full control over the connection lifecycle and allows manual timing measurement reported to the Locust event system.

### 6. YAML Load Profiles
**Decision**: Define load profiles as YAML files in `profiles/` directory
**Rationale**: YAML profiles provide a declarative way to configure test parameters (users, spawn rate, duration, scenario weights) without modifying Python code. Named presets (smoke, load, stress, soak) make common testing scenarios accessible via a single `--profile` flag. Profiles are version-controlled and self-documenting.

### 7. Prometheus Metrics on Port 9646
**Decision**: Export Locust metrics in Prometheus text format on port 9646
**Rationale**: Prometheus format is the standard for the Grafana/Mimir metrics pipeline already used in the observability stack. Port 9646 avoids conflicts with other services. The `prometheus-client` Python library integrates naturally with Locust's event system. Export is opt-in via environment variable to avoid overhead when metrics collection is not needed.

### 8. Grafana Dashboard Integration
**Decision**: Provision a Grafana dashboard JSON alongside the observability stack dashboards
**Rationale**: Placing the dashboard in `infra/observability/grafana/dashboards/` uses the existing auto-provisioning mechanism. When the observability stack is active, the load testing dashboard appears alongside application dashboards, enabling correlation between load patterns and application behavior (e.g., latency increases under load).

## Integration Points

### With Existing Features
- **Docker Networking**: Load testing containers join `durable-network-dev` to reach the backend
- **Justfile**: New `load-test` dispatch target follows established patterns
- **Backend API**: Exercises all REST endpoints and WebSocket service
- **Observability Stack**: Metrics flow into Mimir via Alloy; dashboard provisioned in Grafana

### With Grafana Observability Roadmap
- **Soft Dependency**: PR 5 creates artifacts (dashboard JSON, Alloy config) that activate when the observability stack is deployed
- **Correlation**: Running load tests against an instrumented application generates traces, logs, and metrics visible in the observability stack
- **Dashboard Coexistence**: Load testing dashboard appears alongside Golden Signals and application dashboards

## Success Metrics
- All REST endpoints respond correctly under 50 concurrent users
- WebSocket oscilloscope protocol completes under 30 concurrent connections
- Prometheus metrics endpoint serves valid data with < 5% overhead
- Grafana dashboard displays all panels with live data during test runs
- Four distinct load profiles produce measurably different load patterns

## Technical Constraints
- **Docker network**: Locust containers must join `durable-network-dev` (external network)
- **Port allocation**: 8089 (Locust UI), 9646 (Prometheus metrics) must not conflict
- **Python version**: Must match or be compatible with the backend Python version
- **WebSocket protocol**: Oscilloscope WS has a specific message sequence that must be followed
- **Metrics export**: Optional (env-var controlled) to avoid port conflicts when not needed

## AI Agent Guidance

### When Implementing Foundation (PR 1)
- Read all backend API routes in `durable-code-app/backend/app/api/` to identify endpoints
- Study the justfile for the `infra` dispatch pattern to replicate for `load-test`
- Use `durable-network-dev` as an external network in docker-compose.yml
- Include proper file headers per `.ai/docs/FILE_HEADER_STANDARDS.md`
- Pin the Locust version in requirements.txt

### When Implementing WebSocket Testing (PR 2)
- Read the oscilloscope WebSocket handler in the backend to understand the exact protocol
- Use `websockets` library (async) with Locust's `gevent` concurrency via `gevent.spawn`
- Report each protocol step as a separate Locust request event for granular statistics
- Handle connection drops gracefully with automatic reconnection

### Common Patterns
- **Justfile dispatch**: `just load-test [subcommand]` maps to docker compose operations
- **Docker Compose**: master exposes ports, workers scale independently
- **Environment variables**: Configuration passed via env vars, not hardcoded
- **Profile loading**: YAML parsed at startup, converted to Locust CLI flags
- **Metrics export**: Hook into `events.request` listener, serve on separate port

## Risk Mitigation
- **Network isolation**: Load tests target `durable-network-dev` only; no external access by default
- **Resource consumption**: Profiles define upper bounds (users, duration) to prevent runaway tests
- **Port conflicts**: Dedicated ports (8089, 9646) documented and configurable
- **Graceful shutdown**: `just load-test stop` runs `docker compose down` for clean cleanup
- **Optional metrics**: Export disabled by default to avoid port binding when not needed

## Future Enhancements
- **Distributed testing**: Deploy Locust workers across multiple machines or EC2 instances
- **CI/CD integration**: Run smoke profile as a deployment gate in GitHub Actions
- **Custom shape classes**: Locust LoadTestShape for ramp-up/plateau/ramp-down patterns
- **Result storage**: Persist Locust CSV results to S3 for historical comparison
- **Threshold alerts**: Fail tests automatically when response times exceed defined thresholds
