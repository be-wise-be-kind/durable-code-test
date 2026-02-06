# Locust Load Testing - Progress Tracker & AI Agent Handoff Document

**Purpose**: Primary AI agent handoff document for Locust Load Testing with progress tracking and implementation guidance

**Scope**: Complete load testing implementation using Locust for HTTP and WebSocket endpoints, with metrics export to the Grafana observability stack

**Overview**: Primary handoff document for AI agents working on the Locust Load Testing feature.
    Tracks implementation progress across 5 pull requests that deliver HTTP load testing, WebSocket load testing,
    mixed scenarios with configurable profiles, Prometheus metrics export, and observability integration.
    Contains current status, prerequisite validation, PR dashboard, detailed checklists, implementation strategy,
    success metrics, and AI agent instructions. Essential for maintaining development continuity and ensuring
    systematic feature implementation with proper validation and testing.

**Dependencies**: Existing FastAPI backend endpoints, WebSocket oscilloscope service, Docker networking, Grafana observability stack (for PRs 4-5)

**Exports**: Progress tracking, implementation guidance, AI agent coordination, and feature development roadmap

**Related**: AI_CONTEXT.md for architecture decisions, PR_BREAKDOWN.md for detailed implementation steps

**Implementation**: Progress-driven coordination with systematic validation, checklist management, and AI agent handoff procedures

---

## Document Purpose
This is the **PRIMARY HANDOFF DOCUMENT** for AI agents working on the Locust Load Testing feature. When starting work on any PR, the AI agent should:
1. **Read this document FIRST** to understand progress and requirements
2. **Check the "Next PR to Implement" section** for what to do
3. **Reference the linked documents** for detailed instructions
4. **Update this document** after completing each PR

## Current Status
**Current PR**: PR 4 - Metrics Export to Prometheus/Mimir
**Infrastructure State**: `load-testing/` directory contains Dockerfile, docker-compose.yml, pyproject.toml, HTTP scenarios, WebSocket scenarios, mixed scenario locustfile, profile loader, and 4 YAML load profiles (smoke/load/stress/soak). `just load-test` dispatch target supports ui/run/stop/status/help subcommands with `--profile` flag for predefined test configurations.
**Feature Target**: Locust-based load testing for all HTTP and WebSocket endpoints with metrics export to Grafana

## Required Documents Location
```
.roadmap/in_progress/load-testing/
├── AI_CONTEXT.md          # Architecture decisions, tool choice rationale, integration patterns
├── PR_BREAKDOWN.md        # Detailed instructions for each PR
├── PROGRESS_TRACKER.md    # THIS FILE - Progress and handoff notes
```

## Next PR to Implement

### START HERE: PR 4 - Metrics Export to Prometheus/Mimir

**Quick Summary**:
Add Prometheus metrics export to the Locust master process. Create a metrics exporter that hooks into Locust request events, exposes histograms/counters/gauges on port 9646, and is controllable via the `LOCUST_METRICS_EXPORT` environment variable.

**Pre-flight Checklist**:
- [ ] Review existing load-testing infrastructure (Dockerfile, docker-compose.yml, locustfiles)
- [ ] Understand Locust event system for hooking into request events
- [ ] Review prometheus-client library patterns for custom metrics

**Prerequisites Complete**:
- [x] PR1 merged - load-testing foundation exists (`98ac3b8`, PR #72)
- [x] PR2 merged - WebSocket load testing exists (`6d283f5`, PR #76)
- [x] PR3 merged - Mixed scenarios and profiles operational
- [x] Backend WebSocket oscilloscope service functional
- [x] `just load-test` dispatch target operational with `--profile` flag

---

## Overall Progress
**Total Completion**: 60% (3/5 PRs completed, PR 4 next)

```
[████████████░░░░░░░░] 60% Complete
```

---

## PR Status Dashboard

| PR | Title | Status | Complexity | Notes |
|----|-------|--------|------------|-------|
| 1 | Load Testing Foundation & HTTP Scenarios | Complete | High | `98ac3b8`, PR #72 |
| 2 | WebSocket Load Testing Scenarios | Complete | High | `6d283f5`, PR #76 |
| 3 | Mixed Scenarios & Parameterized Profiles | Complete | Medium | PR pending |
| 4 | Metrics Export to Prometheus/Mimir | Not Started | Medium | Depends on PR 3 |
| 5 | Observability Integration & Dashboard | Not Started | Medium | Depends on PR 4 + Observability PR 4+ |

### Status Legend
- Not Started
- In Progress
- Complete
- Blocked
- Cancelled

---

## PR 1: Load Testing Foundation & HTTP Scenarios ✅
**Branch**: `feat/load-testing-foundation` | **Merged**: `98ac3b8` (PR #72)
- [x] Create `load-testing/` directory structure (locustfiles/, Dockerfile, docker-compose.yml, pyproject.toml)
- [x] Create Dockerfile based on `python:3.11-slim` with pip install from pyproject.toml
- [x] Create `docker-compose.yml` with locust-master service, configurable via LOAD_TEST_HOST env var
- [x] Create `locustfiles/http_users.py` with HttpUser class exercising all 8 REST endpoints
- [x] Add `just load-test` dispatch target to justfile (ui, run, stop, status, help subcommands)
- [x] `just load-test run` executes headless load test against configured host
- [x] `just load-test ui` starts Locust web UI on port 8089
- [x] Verified all HTTP endpoint tasks produce 200 responses (70 requests, 0 failures)

## PR 2: WebSocket Load Testing Scenarios ✅
**Branch**: `feat/load-testing-websocket` | **Merged**: `6d283f5` (PR #76)
- [x] Create `locustfiles/websocket_users.py` with custom WebSocketUser class
- [x] Implement oscilloscope protocol flow (connect, start, receive, configure, stop, disconnect)
- [x] Report WebSocket timing metrics to Locust event system
- [x] Create `load-testing/lib/websocket_client.py` helper using `websockets` library
- [x] Add `websockets` to pyproject.toml dependencies
- [x] Verify WebSocket tasks appear in Locust statistics with correct timing

## PR 3: Mixed Scenarios & Parameterized Profiles ✅
**Branch**: `feat/load-testing-scenarios` | **Merged**: PR pending
- [x] Create `locustfiles/mixed_users.py` combining HTTP and WebSocket with weight ratios
- [x] Create YAML load profiles under `profiles/` (smoke.yml, load.yml, stress.yml, soak.yml)
- [x] Create `load-testing/lib/profile_loader.py` to parse YAML profiles into Locust configuration
- [x] Enhance `just load-test` with `--profile` flag (e.g., `just load-test run --profile smoke`)
- [x] Each profile defines user count, spawn rate, duration, and scenario weights
- [x] Verify each profile runs to completion without errors

## PR 4: Metrics Export to Prometheus/Mimir
**Branch**: `feat/load-testing-metrics-export`
- [ ] Create `load-testing/lib/metrics_exporter.py` using `prometheus-client`
- [ ] Hook into Locust `request` events to record histograms, counters, gauges
- [ ] Serve `/metrics` endpoint on port 9646 from the Locust master process
- [ ] Add `prometheus-client` to requirements.txt
- [ ] Graceful no-op when metrics export is disabled (env var `LOCUST_METRICS_EXPORT`)
- [ ] Verify `/metrics` endpoint returns valid Prometheus text format

## PR 5: Observability Integration & Dashboard
**Branch**: `feat/load-testing-observability`
- [ ] Create `infra/observability/grafana/dashboards/load-testing.json` Grafana dashboard
- [ ] Create Alloy scrape config snippet for Locust metrics endpoint
- [ ] Add `just load-test report` subcommand that opens Grafana dashboard URL
- [ ] Dashboard panels: request rate, error rate, response time percentiles, active users, RPS by endpoint
- [ ] Verify dashboard populates when load test runs against instrumented application
- [ ] Document integration with observability stack in load-testing README or inline comments

---

## Implementation Strategy

### Project Isolation
- Top-level `load-testing/` directory parallels `durable-code-app/` and `infra/`
- Dedicated Dockerfile and docker-compose prevent dependency conflicts
- Locust master+worker pattern supports future distributed testing

### Justfile Dispatch Pattern
- `just load-test [subcommand]` mirrors `just infra [subcommand]` pattern
- Subcommands: run, ui, stop, status, report
- Profile selection via `--profile` flag with YAML-defined presets

### Incremental Capability
- PR 1: HTTP testing (immediate value)
- PR 2: WebSocket testing (protocol coverage)
- PR 3: Combined scenarios with presets (operational convenience)
- PR 4: Metrics pipeline (quantitative analysis)
- PR 5: Grafana dashboards (visual analysis and correlation with app metrics)

## Success Metrics

### Technical Metrics
- All REST endpoints exercised under load without application errors
- WebSocket oscilloscope protocol survives sustained concurrent connections
- Prometheus metrics endpoint serves valid data during test runs
- Grafana dashboard renders load test metrics alongside application metrics

### Feature Metrics
- `just load-test run` completes a smoke test in under 60 seconds
- `just load-test ui` provides accessible web interface on port 8089
- Load profiles (smoke/load/stress/soak) each produce distinct load patterns
- Metrics export imposes negligible overhead on Locust master process

## Update Protocol

After completing each PR:
1. Update the PR status to Complete
2. Add commit hash to Notes column
3. Update overall progress percentage
4. Update the "Next PR to Implement" section
5. Check if directory move needed (0% -> >0%: move to `in_progress/`)
6. Commit changes to the progress document

## Notes for AI Agents

### Critical Context
- The backend API endpoints are defined in `durable-code-app/backend/app/api/`
- The WebSocket oscilloscope service has a specific protocol sequence that must be followed exactly
- The `durable-network-dev` Docker network connects the application containers
- PR 5 has a soft dependency on the Grafana observability stack (PRs 4+ of the grafana-observability roadmap)

### Common Pitfalls to Avoid
- Do not install Locust in the backend container; it has its own dedicated container
- Do not use Locust's built-in WebSocket support (it does not exist natively); use a custom User class with the `websockets` library
- Do not hardcode backend URLs; use Docker service names or environment variables
- Do not run load tests against production endpoints without explicit user instruction
- Profile YAML files must be valid and parseable; test each profile independently

### Resources
- Locust documentation: docs.locust.io
- Prometheus client library: github.com/prometheus/client_python
- Existing justfile patterns for dispatch targets
- Backend API route definitions in `durable-code-app/backend/app/api/`

## Definition of Done

The feature is considered complete when:
- [ ] All 5 PRs merged
- [ ] `just load-test run` executes a headless smoke test against the running application
- [ ] `just load-test ui` opens Locust web UI with all scenario types available
- [ ] All 4 load profiles (smoke/load/stress/soak) run to completion
- [ ] WebSocket load tests maintain concurrent connections through full protocol cycle
- [ ] `/metrics` endpoint on port 9646 serves Prometheus-format data during test runs
- [ ] Grafana dashboard displays load test metrics when observability stack is active
- [ ] `just load-test stop` cleanly shuts down all Locust containers
