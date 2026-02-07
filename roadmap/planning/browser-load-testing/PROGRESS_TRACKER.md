# Browser-Based Frontend Load Testing - Progress Tracker & AI Agent Handoff Document

**Purpose**: Primary AI agent handoff document for browser-based frontend load testing with progress tracking and implementation guidance

**Scope**: Playwright-based browser load testing integration with Locust via locust-plugins PlaywrightUser

**Overview**: Primary handoff document for AI agents working on the browser-based frontend load testing
    feature. Tracks implementation progress across a single PR that adds Playwright browser automation
    to the existing Locust load testing framework. The feature enables real browser-based load testing
    of frontend user journeys (oscilloscope demo, racing game, tab navigation) alongside existing
    HTTP and WebSocket load tests, using locust-plugins PlaywrightUser for unified metric reporting.

**Dependencies**: locust-plugins[playwright], Playwright, Microsoft Playwright Docker base image,
    existing Locust load testing infrastructure

**Exports**: Progress tracking, implementation guidance, AI agent coordination

**Related**: PR_BREAKDOWN.md for detailed tasks

**Implementation**: Single-PR implementation with progress-driven coordination and systematic validation

---

## Document Purpose
This is the **PRIMARY HANDOFF DOCUMENT** for AI agents working on the browser-based frontend load testing feature. When starting work:
1. **Read this document FIRST** to understand current progress
2. **Check the "Next PR to Implement" section** for what to do
3. **Reference PR_BREAKDOWN.md** for detailed instructions
4. **Update this document** after completing each PR

## Current Status
**Current PR**: PR1 - In Progress
**Infrastructure State**: Existing Locust load testing framework operational
**Feature Target**: Browser-based frontend load testing with Playwright via locust-plugins

## Required Documents Location
```
roadmap/planning/browser-load-testing/
├── PR_BREAKDOWN.md        # Detailed instructions for each PR
├── PROGRESS_TRACKER.md    # THIS FILE - Current progress and handoff notes
```

## Next PR to Implement

### START HERE: PR1 - Browser Load Testing Infrastructure and Scenarios

**Quick Summary**:
Add Playwright-based browser load testing to the existing Locust framework using locust-plugins
PlaywrightUser. Creates Dockerfile.browser, docker-compose browser profile, three PlaywrightUser
scenario classes, and justfile targets for browser-ui/browser-stop.

**Pre-flight Checklist**:
- [ ] Existing load testing works (`just load-test ui` starts on port 8089)
- [ ] Frontend dev environment available (`just dev` running)

**Prerequisites Complete**:
- [x] Locust load testing framework exists
- [x] Docker Compose infrastructure in place
- [x] Justfile load testing targets exist

---

## Overall Progress
**Total Completion**: 0% (0/1 PRs completed)

```
[░░░░░░░░░░░░░░░░░░░░] 0% Complete
```

---

## PR Status Dashboard

| PR | Title | Status | Completion | Complexity | Priority | Notes |
|----|-------|--------|------------|------------|----------|-------|
| PR1 | Browser Load Testing Infrastructure and Scenarios | In Progress | 0% | Medium | High | Single PR covers all changes |

### Status Legend
- Not Started
- In Progress
- Complete
- Blocked
- Cancelled

---

## Implementation Strategy

Single-PR approach covering:
1. **Dependencies**: Bump locust, add browser optional extras to pyproject.toml
2. **Container**: Dockerfile.browser using MS Playwright Python base image
3. **Orchestration**: locust-browser service in docker-compose.yml with browser profile
4. **Scenarios**: Three PlaywrightUser classes (oscilloscope, racing, tab navigation)
5. **Automation**: Justfile browser-ui and browser-stop targets

## Success Metrics

### Technical Metrics
- [ ] `just load-test browser-ui` builds and starts Locust UI on port 8090
- [ ] Existing `just load-test ui` unaffected (port 8089)
- [ ] Locust shows per-step events for browser scenarios
- [ ] Pre-commit hooks pass

### Feature Metrics
- [ ] Oscilloscope journey completes: page_load through click_disconnect
- [ ] Racing journey completes: page_load through canvas_mouse_interaction
- [ ] Tab navigation reports timing for all 7 tabs

## Update Protocol

After completing each PR:
1. Update the PR status to Complete
2. Fill in completion percentage
3. Add commit hash to Notes column
4. Update overall progress percentage
5. Commit changes to the progress document

## Notes for AI Agents

### Critical Context
- Browser instances are heavy: limit to 4-5 concurrent users per worker
- Use `wait_until="domcontentloaded"` for SPA page loads to prevent stalling
- Selectors use text-based patterns, not CSS module class names (hashed/unstable)
- The browser Docker Compose profile keeps the ~400MB Playwright image out of default builds

### Common Pitfalls to Avoid
- Do not use `page.goto("/")` with default wait_until (waits for all resources including WebSocket)
- Do not reference CSS module class names as selectors (they change per build)
- Do not expect high user counts with browser instances (4-5 max per worker)

### Resources
- locust-plugins PlaywrightUser: `locust_plugins.users.playwright`
- MS Playwright Docker image: `mcr.microsoft.com/playwright/python:v1.48.0-jammy`
- Existing Playwright integration tests: `test/integration_test/test_oscilloscope_playwright.py`

## Definition of Done

The feature is considered complete when:
- [ ] Dockerfile.browser builds successfully
- [ ] docker-compose browser profile starts locust-browser on port 8090
- [ ] Three PlaywrightUser scenarios report metrics to Locust UI
- [ ] `just load-test ui` (HTTP/WS) remains unaffected
- [ ] `just load-test browser-ui` and `browser-stop` work correctly
- [ ] Pre-commit hooks pass on all changed files
