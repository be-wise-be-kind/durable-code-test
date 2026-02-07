# Delay Endpoints - PR Breakdown

**Purpose**: Detailed implementation breakdown of delay endpoints into a single atomic pull request

**Scope**: Complete feature implementation from dependency addition through load test integration

**Overview**: Comprehensive breakdown of the delay endpoints feature into 1 manageable, atomic
    pull request. The PR is designed to be self-contained, testable, and maintains application functionality
    while delivering the complete feature. Includes detailed implementation steps, file structures,
    testing requirements, and success criteria.

**Dependencies**: FastAPI, httpx, opentelemetry-instrumentation-httpx, Locust

**Exports**: PR implementation plan, file structures, testing strategy, and success criteria

**Related**: PROGRESS_TRACKER.md for status tracking

**Implementation**: Atomic PR approach with detailed step-by-step implementation guidance and comprehensive testing validation

---

## PROGRESS TRACKER - MUST BE UPDATED AFTER EACH PR!

### Completed PRs
- None yet - Implementation in progress

### NEXT PR TO IMPLEMENT
- **START HERE: PR1** - Delay Endpoints with Chaining and Load Test Integration

### Remaining PRs
- [ ] PR1: Delay endpoints with chaining and load test integration

**Progress**: 0% Complete (0/1 PRs)

---

## Overview
This document breaks down the delay endpoints feature into a single atomic PR. The PR is designed to be:
- Self-contained and testable
- Maintains a working application
- Delivers the complete feature
- Revertible if needed

---

## PR1: Delay Endpoints with Chaining and Load Test Integration

### Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `durable-code-app/backend/pyproject.toml` | MODIFY | Add httpx + otel-httpx to main deps |
| `durable-code-app/backend/app/core/telemetry.py` | MODIFY | Add httpx instrumentation |
| `durable-code-app/backend/app/delay.py` | CREATE | Delay endpoints with chaining |
| `durable-code-app/backend/app/main.py` | MODIFY | Register delay_router |
| `load-testing/locustfiles/http_users.py` | MODIFY | Add delay endpoint tasks |

### Implementation Steps

1. **Add dependencies to pyproject.toml**
   - Move httpx from dev to main dependencies
   - Add opentelemetry-instrumentation-httpx
   - Add mypy override for otel httpx module

2. **Instrument httpx in telemetry.py**
   - Add _instrument_httpx() helper function
   - Call from configure_telemetry() after other providers

3. **Create delay.py endpoint module**
   - Three endpoints: /api/delay/slow, /api/delay/med, /api/delay/fast
   - ?call= parameter for chaining (e.g. ?call=med,fast)
   - Chained calls omit ?call= to prevent recursion
   - Max chain depth of 5
   - Custom OTel spans with delay.type, delay.chain_length attributes
   - Rate limiting via get_security_config("api_data")

4. **Register router in main.py**
   - Import delay_router
   - app.include_router(delay_router)

5. **Add load testing tasks**
   - delay_slow (weight 2), delay_med (weight 3), delay_fast (weight 4)
   - delay_health (weight 1)
   - _random_call_chain() helper: 40% no chain, 60% random 1-3 targets

### Testing Requirements
- `just lint python` passes with exit code 0
- Pre-commit hooks pass
- curl /api/delay/slow?call=med,fast returns valid JSON
- Traces visible in Grafana Tempo with parent-child spans

### Success Criteria
- All delay endpoints respond within expected timing ranges
- Chain calls produce linked distributed traces
- Load testing generates varied trace patterns
- All linting and quality gates pass

---

## Implementation Guidelines

### Code Standards
- Python 3.11+, type hints on all functions
- Docstrings on all public functions
- Max cyclomatic complexity of 5 per function
- Follow existing patterns from oscilloscope.py

### Testing Requirements
- Manual verification via curl and Grafana Tempo
- Load testing via Locust

### Security Considerations
- Rate limiting on all endpoints
- Max chain depth prevents abuse
- Uses random.SystemRandom() for cryptographically secure randomization
- Input validation on ?call= parameter

### Performance Targets
- slow: 2-3 second response (without chaining)
- med: 0.5-1 second response (without chaining)
- fast: 50-100ms response (without chaining)

## Success Metrics

### Launch Metrics
- Endpoints respond with correct timing ranges
- Distributed traces appear in Grafana Tempo
- Load test generates continuous trace data

### Ongoing Metrics
- Trace data visible in Tempo dashboards
- No rate limit violations under normal load
