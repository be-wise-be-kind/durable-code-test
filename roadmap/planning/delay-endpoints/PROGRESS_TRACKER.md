# Delay Endpoints - Progress Tracker & AI Agent Handoff Document

**Purpose**: Primary AI agent handoff document for delay endpoints with current progress tracking and implementation guidance

**Scope**: Backend delay endpoints for distributed tracing validation and load testing

**Overview**: Primary handoff document for AI agents working on the delay endpoints feature.
    Tracks current implementation progress, provides next action guidance, and coordinates AI agent work across
    pull requests. Contains current status, prerequisite validation, PR dashboard, detailed checklists,
    implementation strategy, success metrics, and AI agent instructions. Essential for maintaining development
    continuity and ensuring systematic feature implementation with proper validation and testing.

**Dependencies**: FastAPI, httpx, opentelemetry-instrumentation-httpx, Locust load testing framework

**Exports**: Progress tracking, implementation guidance, AI agent coordination, and feature development roadmap

**Related**: PR_BREAKDOWN.md for detailed tasks

**Implementation**: Progress-driven coordination with systematic validation, checklist management, and AI agent handoff procedures

---

## Document Purpose
This is the **PRIMARY HANDOFF DOCUMENT** for AI agents working on the delay endpoints feature. When starting work on any PR, the AI agent should:
1. **Read this document FIRST** to understand current progress and feature requirements
2. **Check the "Next PR to Implement" section** for what to do
3. **Reference the linked documents** for detailed instructions
4. **Update this document** after completing each PR

## Current Status
**Current PR**: PR1 - Delay endpoints implementation
**Infrastructure State**: Backend running on ECS, Grafana Tempo configured for distributed tracing
**Feature Target**: Three delay endpoints (slow, med, fast) with ?call= chaining for multi-hop distributed traces

## Required Documents Location
```
roadmap/planning/delay-endpoints/
├── PR_BREAKDOWN.md        # Detailed instructions for each PR
├── PROGRESS_TRACKER.md    # THIS FILE - Current progress and handoff notes
```

## Next PR to Implement

### START HERE: PR1 - Delay Endpoints with Chaining and Load Test Integration

**Quick Summary**:
Add three delay endpoints (/api/delay/slow, /api/delay/med, /api/delay/fast) with ?call= chaining parameter,
instrument httpx for trace propagation, and add delay tasks to the Locust load testing suite.

**Pre-flight Checklist**:
- [ ] Git worktree created on feat/delay-endpoints branch
- [ ] Dependencies added (httpx, opentelemetry-instrumentation-httpx)
- [ ] Telemetry httpx instrumentation added
- [ ] Delay endpoint module created
- [ ] Router registered in main.py
- [ ] Load testing tasks added
- [ ] Linting passes (`just lint python`)
- [ ] Pre-commit hooks pass

---

## Overall Progress
**Total Completion**: 0% (0/1 PRs completed)

```
[                    ] 0% Complete
```

---

## PR Status Dashboard

| PR | Title | Status | Completion | Complexity | Priority | Notes |
|----|-------|--------|------------|------------|----------|-------|
| PR1 | Delay endpoints with chaining and load test integration | In Progress | 0% | Medium | High | Single PR feature |

### Status Legend
- Not Started
- In Progress
- Complete
- Blocked

---

## Implementation Strategy

Single-PR feature implementing:
1. httpx + otel-httpx dependencies in pyproject.toml
2. httpx instrumentation in telemetry.py for trace context propagation
3. delay.py module with slow/med/fast endpoints and ?call= chaining
4. Router registration in main.py
5. Load testing tasks in http_users.py with random chain generation

## Success Metrics

### Technical Metrics
- All three delay endpoints respond with correct timing data
- Chained calls produce linked parent-child spans in Grafana Tempo
- Load testing generates continuous, varied trace data
- `just lint python` passes with exit code 0

### Feature Metrics
- Multi-hop traces visible in Grafana Tempo
- Delay ranges respected (slow: 2-3s, med: 0.5-1s, fast: 50-100ms)
- Chain depth limited to 5 maximum

## Update Protocol

After completing each PR:
1. Update the PR status to Complete
2. Fill in completion percentage
3. Add any important notes or blockers
4. Update the "Next PR to Implement" section
5. Update overall progress percentage
6. Commit changes to the progress document

## Notes for AI Agents

### Critical Context
- Chained calls do NOT forward ?call= parameter (prevents infinite recursion)
- httpx instrumentation auto-injects traceparent/tracestate headers
- Uses random.SystemRandom() for delay durations (avoids Bandit S311)
- Rate limited via get_security_config("api_data")

### Common Pitfalls to Avoid
- Do not forward ?call= in chained requests
- Do not exceed max chain depth of 5
- Do not use random.uniform directly (triggers Bandit S311)

### Resources
- `.ai/howtos/add-api-endpoint.md`
- `.ai/templates/fastapi-endpoint.py.template`
- Existing patterns: oscilloscope.py, racing/api/routes.py

## Definition of Done

The feature is considered complete when:
- [ ] All delay endpoints return correct responses
- [ ] Chained calls produce linked spans in Tempo
- [ ] Load testing generates varied trace data
- [ ] All linting passes
- [ ] PR merged to main
