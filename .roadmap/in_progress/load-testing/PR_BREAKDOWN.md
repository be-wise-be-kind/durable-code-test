# Locust Load Testing - PR Breakdown

**Purpose**: Detailed implementation breakdown of Locust Load Testing into 5 atomic pull requests

**Scope**: Complete feature implementation from project foundation through observability integration

**Overview**: Comprehensive breakdown of the Locust Load Testing feature into 5 manageable, atomic
    pull requests. Each PR is designed to be self-contained, testable, and maintains application functionality
    while incrementally building toward complete load testing capability with metrics export and Grafana
    integration. Includes detailed implementation steps, file structures, testing requirements, and success
    criteria for each PR.

**Dependencies**: FastAPI backend endpoints, WebSocket oscilloscope service, Docker networking, Grafana observability stack (PR 5)

**Exports**: PR implementation plans, file structures, testing strategies, and success criteria for each development phase

**Related**: AI_CONTEXT.md for architecture decisions, PROGRESS_TRACKER.md for status tracking

**Implementation**: Atomic PR approach with foundation-first, protocol-coverage-second, integration-third strategy

---

## PROGRESS TRACKER - MUST BE UPDATED AFTER EACH PR!

### Completed PRs
- [x] PR 1: Load Testing Foundation & HTTP Scenarios (`98ac3b8`, PR #72)
- [x] PR 2: WebSocket Load Testing Scenarios (`6d283f5`, PR #76)
- [x] PR 3: Mixed Scenarios & Parameterized Profiles (PR pending)

### NEXT PR TO IMPLEMENT
START HERE: **PR 4** - Metrics Export to Prometheus/Mimir

### Remaining PRs
- [x] PR 1: Load Testing Foundation & HTTP Scenarios
- [x] PR 2: WebSocket Load Testing Scenarios
- [x] PR 3: Mixed Scenarios & Parameterized Profiles
- [ ] PR 4: Metrics Export to Prometheus/Mimir
- [ ] PR 5: Observability Integration & Dashboard

**Progress**: 60% Complete (3/5 PRs)

---

## Overview
This document breaks down the Locust Load Testing feature into 5 manageable, atomic PRs. Each PR is:
- Self-contained and testable
- Maintains a working application
- Incrementally builds toward complete load testing capability
- Revertible if needed

---

## PR 1: Load Testing Foundation & HTTP Scenarios

**Branch**: `feat/load-testing-foundation`
**Complexity**: High | **Dependencies**: None

### New Files

- `load-testing/Dockerfile`
  - Base image: `locustio/locust`
  - Copy locustfiles, lib, and requirements
  - Install additional Python dependencies

- `load-testing/docker-compose.yml`
  - Master service: exposes port 8089 (web UI), mounts locustfiles
  - Worker service: scales via `--scale worker=N`
  - Network: `durable-network-dev` (external)
  - Environment variables: `LOCUST_HOST`, `LOCUST_USERS`, `LOCUST_SPAWN_RATE`

- `load-testing/requirements.txt`
  - `locust` (pinned version)
  - Additional dependencies added in later PRs

- `load-testing/locustfiles/__init__.py`
  - Empty init for Python package

- `load-testing/locustfiles/http_users.py`
  - `DurableCodeHttpUser(HttpUser)` class
  - `wait_time = between(1, 3)`
  - Tasks for all REST endpoints:
    - `GET /api/health` (health check)
    - `GET /api/status` (app status)
    - `GET /api/oscilloscope/config` (oscilloscope config)
    - `PUT /api/oscilloscope/config` (update config)
    - `GET /api/oscilloscope/status` (oscilloscope status)
    - `POST /api/oscilloscope/start` (start oscilloscope)
    - `POST /api/oscilloscope/stop` (stop oscilloscope)
    - `GET /api/oscilloscope/snapshot` (data snapshot)
  - Task weights reflecting realistic usage patterns
  - Assertions on response status codes

- `load-testing/lib/__init__.py`
  - Empty init for Python package

### Modified Files

- `justfile`
  - Add `load-test` dispatch target with subcommands:
    - `run [args]`: `docker compose -f load-testing/docker-compose.yml up --abort-on-container-exit`
    - `ui [args]`: `docker compose -f load-testing/docker-compose.yml up -d` (detached, web UI on 8089)
    - `stop`: `docker compose -f load-testing/docker-compose.yml down`
    - `status`: `docker compose -f load-testing/docker-compose.yml ps`

### Success Criteria
- `just load-test run` executes headless test against running backend
- `just load-test ui` starts Locust web UI accessible at http://localhost:8089
- All HTTP endpoint tasks complete without 5xx errors
- `just load-test stop` cleanly shuts down containers

---

## PR 2: WebSocket Load Testing Scenarios

**Branch**: `feat/load-testing-websocket`
**Complexity**: High | **Dependencies**: PR 1

**NOTE**: Read the WebSocket oscilloscope implementation in the backend before starting to understand the exact protocol sequence.

### New Files

- `load-testing/lib/websocket_client.py`
  - Async WebSocket client wrapper using `websockets` library
  - Connection management (connect, close, reconnect)
  - Message send/receive with timing measurement
  - Context manager support for clean resource handling
  - Reports timing data to Locust `request` event system

- `load-testing/locustfiles/websocket_users.py`
  - `OscilloscopeWebSocketUser(User)` custom user class (not HttpUser)
  - Implements oscilloscope protocol sequence:
    1. Connect to `ws://<host>/api/oscilloscope/ws`
    2. Send start command
    3. Receive data frames (configurable count)
    4. Send configuration change
    5. Receive additional data frames
    6. Send stop command
    7. Disconnect
  - Reports each protocol step as a Locust request event with timing
  - `wait_time = between(2, 5)` between full cycles
  - Error handling for connection drops and timeouts

### Modified Files

- `load-testing/requirements.txt`
  - Add `websockets` library

### Success Criteria
- WebSocket tasks appear in Locust statistics table
- Each protocol step (connect, start, receive, configure, stop, disconnect) tracked separately
- Sustained 10+ concurrent WebSocket connections without errors
- Clean reconnection after connection drops

---

## PR 3: Mixed Scenarios & Parameterized Profiles

**Branch**: `feat/load-testing-scenarios`
**Complexity**: Medium | **Dependencies**: PR 2

### New Files

- `load-testing/locustfiles/mixed_users.py`
  - Combines `DurableCodeHttpUser` and `OscilloscopeWebSocketUser`
  - Configurable weight ratio (default: 70% HTTP, 30% WebSocket)
  - Weight ratio overridable via environment variables

- `load-testing/profiles/smoke.yml`
  ```yaml
  name: smoke
  description: Quick validation test
  users: 5
  spawn_rate: 1
  duration: 30s
  scenarios:
    http_weight: 80
    websocket_weight: 20
  ```

- `load-testing/profiles/load.yml`
  ```yaml
  name: load
  description: Standard load test
  users: 50
  spawn_rate: 5
  duration: 5m
  scenarios:
    http_weight: 70
    websocket_weight: 30
  ```

- `load-testing/profiles/stress.yml`
  ```yaml
  name: stress
  description: Find breaking points
  users: 200
  spawn_rate: 20
  duration: 10m
  scenarios:
    http_weight: 60
    websocket_weight: 40
  ```

- `load-testing/profiles/soak.yml`
  ```yaml
  name: soak
  description: Extended duration stability test
  users: 30
  spawn_rate: 2
  duration: 30m
  scenarios:
    http_weight: 70
    websocket_weight: 30
  ```

- `load-testing/lib/profile_loader.py`
  - Reads YAML profile files from `profiles/` directory
  - Converts profile settings to Locust CLI arguments
  - Validates required fields (users, spawn_rate, duration)
  - Returns dict of configuration values

### Modified Files

- `justfile`
  - Enhance `just load-test run` to accept `--profile <name>` flag
  - Profile flag reads YAML and passes settings to Locust via environment variables
  - Default profile: smoke (when no profile specified)

- `load-testing/docker-compose.yml`
  - Add environment variable passthrough for profile settings
  - Add volume mount for `profiles/` directory

### Success Criteria
- `just load-test run --profile smoke` completes in ~30 seconds
- `just load-test run --profile load` runs for 5 minutes with 50 users
- Each profile produces distinct load patterns visible in Locust stats
- Mixed scenarios exercise both HTTP and WebSocket endpoints per configured weights

---

## PR 4: Metrics Export to Prometheus/Mimir

**Branch**: `feat/load-testing-metrics-export`
**Complexity**: Medium | **Dependencies**: PR 3

### New Files

- `load-testing/lib/metrics_exporter.py`
  - Uses `prometheus-client` library
  - Hooks into Locust `request` event via `events.request.add_listener`
  - Prometheus metrics exposed:
    - `locust_requests_total` (Counter): labels: method, name, status
    - `locust_request_duration_seconds` (Histogram): labels: method, name
    - `locust_errors_total` (Counter): labels: method, name, exception
    - `locust_users_active` (Gauge): current active user count
    - `locust_requests_per_second` (Gauge): current RPS
  - Starts HTTP server on port 9646 serving `/metrics`
  - Controlled by `LOCUST_METRICS_EXPORT` environment variable
  - Graceful no-op when disabled (no port binding, no listeners)

### Modified Files

- `load-testing/requirements.txt`
  - Add `prometheus-client`

- `load-testing/docker-compose.yml`
  - Expose port 9646 on master service
  - Add `LOCUST_METRICS_EXPORT` environment variable

- `load-testing/locustfiles/http_users.py`
  - Import and initialize metrics exporter in `@events.init` handler

### Success Criteria
- `curl http://localhost:9646/metrics` returns valid Prometheus text format during test run
- Metrics update in real-time as Locust generates load
- Disabling `LOCUST_METRICS_EXPORT` prevents port binding
- No performance impact on Locust test execution

---

## PR 5: Observability Integration & Dashboard

**Branch**: `feat/load-testing-observability`
**Complexity**: Medium | **Dependencies**: PR 4 + Observability PR 4+

**NOTE**: This PR has a soft dependency on the Grafana observability stack. The dashboard JSON and Alloy config can be created before the stack is deployed; they activate when the stack is running.

### New Files

- `infra/observability/grafana/dashboards/load-testing.json`
  - Grafana dashboard provisioned via existing dashboard provisioning
  - Panels:
    - Request rate by endpoint (time series)
    - Error rate percentage (stat + time series)
    - Response time percentiles p50/p95/p99 (time series)
    - Active users over time (time series)
    - Requests per second aggregate (stat)
    - Error breakdown by exception type (table)
    - Request duration heatmap (heatmap)
  - Variables: `$interval` (auto), `$method` (GET/POST/PUT/DELETE/WS)
  - Datasource: Mimir (Prometheus-compatible queries)

- `infra/observability/alloy/scrape-configs/locust.alloy`
  - Alloy scrape configuration targeting `locust-master:9646`
  - Scrape interval: 15s
  - Job label: `locust`
  - Conditional inclusion (only when load-testing containers are running)

### Modified Files

- `justfile`
  - Add `report` subcommand to `just load-test`
  - Opens Grafana dashboard URL for load testing (prints URL if no browser available)

### Success Criteria
- Dashboard JSON is valid and importable into Grafana
- Alloy scrape config targets the correct Locust metrics endpoint
- Dashboard panels populate when load test runs against instrumented application
- `just load-test report` outputs the dashboard URL

---

## Implementation Guidelines

### Code Standards
- Follow existing patterns in each language/framework
- All files require headers per `.ai/docs/FILE_HEADER_STANDARDS.md`
- Python: PEP 8, type hints, docstrings on public functions
- YAML: consistent indentation (2 spaces), descriptive comments
- Docker: multi-stage builds where beneficial, pinned base images

### Testing Requirements
- Each locustfile must be importable without errors (`python -c "import locustfiles.http_users"`)
- `just load-test run --profile smoke` must complete without errors
- Prometheus metrics endpoint must serve valid format (test with `promtool check metrics`)
- All just targets must function correctly

### Documentation Standards
- Inline code comments for non-obvious logic
- Configuration files include descriptive comments
- YAML profiles include `name` and `description` fields

### Security Considerations
- Load tests must only target the local development environment by default
- No credentials stored in locustfiles or profiles
- Docker network isolation prevents external traffic
- Prometheus metrics endpoint bound to container network only

### Performance Targets
- Locust master process CPU < 50% during smoke tests
- Metrics export adds < 5% overhead to Locust execution
- WebSocket client handles 50+ concurrent connections
- Profile loader parses YAML in < 100ms

## Rollout Strategy

### Phase 1: Foundation (PR 1)
HTTP load testing with basic just targets

### Phase 2: Protocol Coverage (PR 2)
WebSocket load testing with custom user class

### Phase 3: Operational Convenience (PR 3)
Mixed scenarios and preset profiles

### Phase 4: Metrics Pipeline (PR 4)
Prometheus export for quantitative analysis

### Phase 5: Visual Integration (PR 5)
Grafana dashboard and observability correlation

## Success Metrics

### Launch Metrics
- All REST endpoints exercised without application errors
- WebSocket protocol cycles complete under load
- 4 distinct load profiles produce expected patterns
- Prometheus metrics serve valid data

### Ongoing Metrics
- Load tests detect performance regressions when run before/after deployments
- Grafana dashboard provides at-a-glance load test results
- Mixed scenarios reveal interaction effects between HTTP and WebSocket load
- Soak tests identify memory leaks or connection exhaustion
