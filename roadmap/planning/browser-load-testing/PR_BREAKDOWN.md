# Browser-Based Frontend Load Testing - PR Breakdown

**Purpose**: Detailed implementation breakdown for browser-based frontend load testing into a single atomic PR

**Scope**: Complete feature implementation from dependency updates through justfile automation

**Overview**: Comprehensive breakdown of the browser-based frontend load testing feature into implementation
    steps within a single PR. Covers dependency management, Dockerfile creation, Docker Compose profile
    configuration, PlaywrightUser scenario classes, and justfile target integration. Each step is designed
    to be testable and maintains existing application functionality while adding browser-based load testing
    capabilities.

**Dependencies**: locust-plugins[playwright], Playwright, existing Locust load testing infrastructure

**Exports**: PR implementation plan, file structures, testing strategies, and success criteria

**Related**: PROGRESS_TRACKER.md for status tracking

**Implementation**: Single-PR approach with detailed step-by-step implementation guidance

---

## PROGRESS TRACKER - MUST BE UPDATED AFTER EACH PR!

### Completed PRs
- None yet - Implementation in progress

### NEXT PR TO IMPLEMENT
START HERE: PR1 - Browser Load Testing Infrastructure and Scenarios

### Remaining PRs
- [ ] PR1: Browser Load Testing Infrastructure and Scenarios

**Progress**: 0% Complete (0/1 PRs)

---

## Overview
This document breaks down the browser-based frontend load testing feature into a single PR containing all required changes. The PR is designed to be self-contained, testable, and maintains the existing HTTP/WebSocket load testing functionality.

---

## PR1: Browser Load Testing Infrastructure and Scenarios

### Summary
Add Playwright-based browser load testing using locust-plugins PlaywrightUser integration. Creates a separate Docker image with browser binaries, a Docker Compose profile for isolated browser testing, three browser scenario classes, and justfile automation targets.

### Files Changed

| File | Action | Description |
|------|--------|-------------|
| `load-testing/pyproject.toml` | MODIFY | Bump locust to >=2.35.0, add browser optional deps |
| `load-testing/Dockerfile.browser` | CREATE | Playwright-based container image |
| `load-testing/docker-compose.yml` | MODIFY | Add locust-browser service with browser profile |
| `load-testing/locustfiles/browser_users.py` | CREATE | Three PlaywrightUser scenario classes |
| `justfile` | MODIFY | Add LOAD_TEST_FRONTEND_HOST var, browser-ui/browser-stop targets |

### Implementation Steps

#### Step 1: Update pyproject.toml
- Bump locust from `>=2.29.0` to `>=2.35.0` (required by locust-plugins)
- Add `[project.optional-dependencies]` section with browser extras:
  - `locust-plugins[playwright]>=4.5.0`
  - `playwright>=1.40.0`

#### Step 2: Create Dockerfile.browser
- Base: `mcr.microsoft.com/playwright/python:v1.48.0-jammy` (ships Chromium pre-installed)
- Install project with browser extras: `pip install ".[browser]"`
- Copy locustfiles and lib directories
- Set `PLAYWRIGHT_BROWSERS_PATH=/ms-playwright`
- Run as non-root user, expose port 8089

#### Step 3: Update docker-compose.yml
- Add `locust-browser` service with:
  - `dockerfile: Dockerfile.browser`
  - `profiles: [browser]` (isolates from default builds)
  - Port mapping `8090:8089` (separate from HTTP/WS UI)
  - Environment vars: LOCUST_HOST, LOCUST_LOCUSTFILE, PLAYWRIGHT_BROWSERS_PATH, LOAD_TEST_FRONTEND_HOST
  - Volume mounts for locustfiles and lib

#### Step 4: Create browser_users.py
Three PlaywrightUser subclasses:

**OscilloscopePlaywrightUser**:
1. Navigate to frontend (wait_until="domcontentloaded")
2. Click "Demo" tab
3. Click Oscilloscope link
4. Click "Connect" button
5. Change waveform via select dropdown
6. Wait for streaming data (2s)
7. Click "Disconnect"

**RacingPlaywrightUser**:
1. Navigate to frontend
2. Click "Demo" tab
3. Click Racing Game link
4. Wait for canvas and auto-loaded track
5. Click "Start" button
6. Simulate mouse movements on canvas
7. Wait for game interaction (3s)

**TabNavigationPlaywrightUser**:
1. Navigate to frontend
2. Loop through all 7 tabs
3. Click each tab, wait 500ms for content render
4. Each tab click reported as separate Locust event

#### Step 5: Update justfile
- Add `LOAD_TEST_FRONTEND_HOST` variable
- Add `browser-ui` and `browser-stop` to dispatch case block
- Add `_load-test-browser-ui` and `_load-test-browser-stop` internal targets
- Update `_load-test-help` with browser subcommand documentation

### Testing Requirements
- [ ] `just load-test browser-ui` builds Dockerfile.browser and starts on port 8090
- [ ] `just load-test browser-stop` tears down browser containers
- [ ] `just load-test ui` continues working on port 8089 (unaffected)
- [ ] Locust browser UI shows per-step events (page_load, navigate_to_demo, etc.)
- [ ] Pre-commit hooks pass on all modified files

### Success Criteria
- Browser load testing container builds from Dockerfile.browser
- locust-browser service starts via `--profile browser` only
- Three PlaywrightUser classes load in Locust and execute browser scenarios
- Locust UI on port 8090 shows timing metrics for each scenario step
- Existing HTTP/WS load testing on port 8089 is unaffected

### Rollback
- Remove Dockerfile.browser
- Revert docker-compose.yml to remove locust-browser service
- Revert pyproject.toml locust version bump and optional deps
- Remove browser_users.py
- Revert justfile browser targets

---

## Implementation Guidelines

### Code Standards
- Python files require comprehensive file headers per FILE_HEADER_STANDARDS.md
- Use type hints for all function signatures
- Docstrings required for all public classes and methods
- Line length under 100 characters

### Testing Requirements
- Smoke test: 1 browser user for 30s against running frontend
- Verify Locust reports events for each scenario step
- Verify existing HTTP/WS tests are not affected

### Security Considerations
- Docker container runs as non-root user
- No sensitive data in environment variables (only host URLs)
- Browser container is isolated via Docker Compose profiles

### Performance Targets
- Browser instances limited to 4-5 per worker
- Each scenario completes within 30s timeout
- No memory leaks from browser context management (handled by @pw decorator)
