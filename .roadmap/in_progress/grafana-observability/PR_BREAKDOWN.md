# Grafana Stack Full Observability - PR Breakdown

**Purpose**: Detailed implementation breakdown of Grafana Stack Full Observability into 10 atomic pull requests

**Scope**: Complete feature implementation from architecture documentation through integration verification

**Overview**: Comprehensive breakdown of the Grafana Stack Full Observability feature into 10 manageable, atomic
    pull requests. Each PR is designed to be self-contained, testable, and maintains application functionality
    while incrementally building toward complete 4-pillar observability. Includes detailed implementation steps,
    file structures, testing requirements, and success criteria for each PR.

**Dependencies**: Existing AWS infrastructure, Terraform workspaces, Docker, OpenTelemetry SDK, Grafana Faro SDK

**Exports**: PR implementation plans, file structures, testing strategies, and success criteria for each phase

**Related**: AI_CONTEXT.md for architecture decisions, PROGRESS_TRACKER.md for status tracking

**Implementation**: Atomic PR approach with infrastructure-first, instrumentation-second, dashboards-third strategy

---

## PROGRESS TRACKER - MUST BE UPDATED AFTER EACH PR!

### Completed PRs
- [x] PR 1: Observability Architecture Documentation
- [x] PR 2: S3 Buckets & IAM Foundation (Base Workspace)
- [x] PR 3: EC2 Observability Instance (Runtime Workspace)
- [x] PR 4: Docker Compose & Component Configs
- [x] PR 5: Backend OpenTelemetry Instrumentation
- [x] PR 6: Frontend Grafana Faro SDK

### NEXT PR TO IMPLEMENT
START HERE: **PR 7** - Golden Signals & Method Dashboards

### Remaining PRs
- [x] PR 1: Observability Architecture Documentation
- [x] PR 2: S3 Buckets & IAM Foundation (Base Workspace)
- [x] PR 3: EC2 Observability Instance (Runtime Workspace)
- [x] PR 4: Docker Compose & Component Configs
- [x] PR 5: Backend OpenTelemetry Instrumentation
- [x] PR 6: Frontend Grafana Faro SDK
- [ ] PR 7: Golden Signals & Method Dashboards
- [ ] PR 8: Tracing Deep Dive & Profiling Correlation
- [ ] PR 9: Alerting & SLO Monitoring
- [ ] PR 10: Integration, Verification & CI/CD

**Progress**: 60% Complete (6/10 PRs)

---

## Overview
This document breaks down the Grafana Stack Full Observability feature into 10 manageable, atomic PRs. Each PR is:
- Self-contained and testable
- Maintains a working application
- Incrementally builds toward complete observability
- Revertible if needed

---

## PR 1: Observability Architecture Documentation

**Branch**: `docs/observability-architecture`
**Complexity**: Medium | **Dependencies**: None

**NOTE**: Re-read all files in `docs/` before starting to pick up any structural changes.

### New Files
- `docs/observability-architecture.html` - Architecture documentation page

### Modified Files
- `docs/index.html` - Add card linking to new page; add nav link
- `docs/terraform-architecture.html` - Add nav link
- `docs/terraform-resources.html` - Add nav link

### Content Sections
1. Page header with 4 Pillars overview cards
2. Architecture diagram (inline SVG) showing data flow
3. Golden Signals mapping table
4. Component detail cards (Grafana, Mimir, Loki, Tempo, Pyroscope, Alloy)
5. Cross-pillar correlation diagram (inline SVG)
6. Network & security diagram
7. Cost & lifecycle table
8. Instrumentation table
9. Implementation roadmap with PR dependency chain

### Success Criteria
- HTML page opens in browser with correct styling
- Nav links work across all docs pages
- SVG diagrams render correctly
- Content accurately represents the planned architecture

---

## PR 2: S3 Buckets & IAM Foundation (Base Workspace)

**Branch**: `infra/observability-foundation`
**Complexity**: Medium | **Dependencies**: None

### New Files
- `infra/terraform/workspaces/base/observability-storage.tf`
  - S3 bucket with prefixes: mimir/, loki/, tempo/, pyroscope/
  - Lifecycle rules: 7d dev, 30d prod
  - Encryption enabled, public access blocked
  - Conditional on `enable_observability`

- `infra/terraform/workspaces/base/observability-iam.tf`
  - IAM role for EC2 with assume role policy
  - Instance profile for EC2 attachment
  - S3 read/write policy for observability bucket
  - SSM managed policy for Session Manager access
  - Conditional on `enable_observability`

- `infra/terraform/workspaces/base/observability-security.tf`
  - Security group for observability EC2
  - Ingress from ALB SG: ports 3001 (Grafana), 12347 (Faro/Alloy)
  - Ingress from ECS SG: ports 4317, 4318 (OTLP), 4040 (Pyroscope)
  - Egress: all (S3, package downloads)
  - Conditional on `enable_observability`

### Modified Files
- `infra/terraform/workspaces/base/variables.tf` - Add `enable_observability` (bool, default false)
- `infra/terraform/workspaces/base/outputs.tf` - Export bucket name/ARN, instance profile name/ARN, SG ID

### Success Criteria
- `just infra validate base` passes
- `just infra plan base` shows expected resources (when enabled)
- All resources conditional on `enable_observability`

---

## PR 3: EC2 Observability Instance (Runtime Workspace)

**Branch**: `infra/observability-ec2`
**Complexity**: High | **Dependencies**: PR 2

### New Files
- `infra/terraform/workspaces/runtime/observability-ec2.tf`
  - Amazon Linux 2023 AMI data source
  - EC2 instance in first private subnet
  - t3.medium, 20GB gp3 root volume
  - Instance profile from base workspace
  - Security group from base workspace
  - user_data bootstraps Docker + Docker Compose
  - Conditional on `enable_observability`

- `infra/terraform/workspaces/runtime/observability-alb.tf`
  - Target group for Grafana (port 3001, instance type)
  - Target group for Alloy Faro (port 12347, instance type)
  - Target group attachments to EC2 instance
  - ALB listener rule: `/grafana/*` priority 90 (HTTP)
  - ALB listener rule: `/collect/*` priority 91 (HTTP)
  - Conditional HTTPS rules if certificate exists
  - Conditional on `enable_observability`

### Modified Files
- `infra/terraform/workspaces/runtime/data.tf` - Add data sources for base observability outputs
- `infra/terraform/workspaces/runtime/variables.tf` - Add `enable_observability`, `observability_instance_type`
- `infra/terraform/workspaces/runtime/outputs.tf` - Export EC2 private IP, Grafana URL

### Success Criteria
- `just infra plan runtime` succeeds
- After apply, SSM Session Manager connects to EC2
- Docker and Docker Compose installed and running
- ALB health checks configured

---

## PR 4: Docker Compose & Component Configs

**Branch**: `infra/observability-stack-config`
**Complexity**: High | **Dependencies**: PR 3

### New Files (under `infra/observability/`)

- `docker-compose.yml` - 6 services with memory limits:
  - grafana (384MB), mimir (768MB), loki (384MB), tempo (384MB), pyroscope (384MB), alloy (384MB)
  - Total: ~2.7GB of 4GB available

- `grafana/grafana.ini` - Subpath `/grafana/`, anonymous viewer, admin password from env
- `grafana/datasources.yml` - Mimir, Loki, Tempo, Pyroscope with cross-links
- `grafana/dashboard-provisioning.yml` - Auto-load from directory
- `mimir/mimir.yml` - Single-binary, S3 blocks, 7d retention
- `loki/loki.yml` - Single-binary, S3 chunks + TSDB index, 7d retention
- `tempo/tempo.yml` - Single-binary, S3 backend, OTLP receivers, metrics generator
- `pyroscope/pyroscope.yml` - Single-binary, S3 storage
- `alloy/config.alloy` - OTLP receiver (4317/4318), Faro receiver (12347), exports to all backends

### Modified Files
- `infra/terraform/workspaces/runtime/observability-ec2.tf` - Update user_data templatefile to write configs and run docker compose

### Success Criteria
- Access `<ALB>/grafana/` shows Grafana UI
- All 4 datasources report healthy status
- `docker compose logs` on EC2 shows no errors
- Alloy receiving on configured ports

---

## PR 5: Backend OpenTelemetry Instrumentation

**Branch**: `feat/backend-otel-instrumentation`
**Complexity**: High | **Dependencies**: PR 4

### New Files
- `durable-code-app/backend/app/core/telemetry.py` - TracerProvider + MeterProvider, OTLP gRPC exporter, FastAPIInstrumentor, resource attributes, head-based sampler
- `durable-code-app/backend/app/core/logging_config.py` - Structured JSON Loguru with trace_id/span_id injection, OTel logging bridge
- `durable-code-app/backend/app/core/metrics.py` - Request duration histogram, request counter, error counter, active connections gauge
- `durable-code-app/backend/app/core/profiling.py` - Pyroscope SDK push-based profiling with trace_id labels

### Modified Files
- `durable-code-app/backend/pyproject.toml` - Add OTel and Pyroscope dependencies
- `durable-code-app/backend/app/main.py` - Call configure_telemetry() and configure_profiling() at startup
- `infra/terraform/workspaces/runtime/ecs.tf` - Add OTEL env vars to backend task definition

### Success Criteria
- Traces visible in Tempo for API requests
- Metrics visible in Mimir (request duration, counts)
- Logs in Loki contain trace_id and span_id
- Profiles in Pyroscope show CPU/memory data

---

## PR 6: Frontend Grafana Faro SDK

**Branch**: `feat/frontend-faro-instrumentation`
**Complexity**: Medium | **Dependencies**: PR 4

### New Files
- `durable-code-app/frontend/src/core/observability/faro.ts` - initializeFaro() with ConsoleInstrumentation, ErrorsInstrumentation, WebVitalsInstrumentation, SessionInstrumentation, TracingInstrumentation with W3C propagation
- `durable-code-app/frontend/src/core/observability/FaroErrorBoundary.tsx` - Error boundary reporting to Faro
- `durable-code-app/frontend/src/core/observability/index.ts` - Barrel exports

### Modified Files
- `durable-code-app/frontend/package.json` - Add @grafana/faro-web-sdk, @grafana/faro-web-tracing, @grafana/faro-react
- `durable-code-app/frontend/src/main.tsx` - Call initializeFaro() conditional on VITE_FARO_ENABLED
- `.docker/dockerfiles/Dockerfile.frontend` - ARG/ENV for VITE_FARO_ENABLED, VITE_FARO_COLLECTOR_URL

### Success Criteria
- Browser DevTools shows POST to `/collect/`
- Frontend spans visible in Tempo
- Web vitals metrics in Mimir (LCP, INP, CLS)
- Frontend-to-backend trace correlation (same trace ID across services)

---

## PR 7: Golden Signals & Method Dashboards

**Branch**: `feat/golden-signals-dashboards`
**Complexity**: Medium | **Dependencies**: PRs 5, 6

### New Files (under `infra/observability/grafana/dashboards/`)
- `golden-signals-overview.json` - Latency (p50/p95/p99), Traffic (req/sec), Errors (rate %), Saturation (CPU/memory)
- `backend-red-method.json` - Rate/Errors/Duration per endpoint, histogram heatmap, exemplar links
- `frontend-web-vitals.json` - LCP, INP, CLS with threshold indicators, JS error rate, session count
- `infrastructure-use-method.json` - Utilization/Saturation/Errors for ECS and EC2

### Modified Files
- `infra/observability/docker-compose.yml` - Volume mount dashboards directory

### Success Criteria
- All dashboards load in Grafana
- Panels populate after traffic generation
- Exemplar links navigate to traces

---

## PR 8: Tracing Deep Dive & Profiling Correlation

**Branch**: `feat/tracing-profiling-deep-dive`
**Complexity**: High | **Dependencies**: PRs 5, 6

### New Files
- `infra/observability/grafana/dashboards/trace-analysis.json` - Trace search, latency waterfall, service graph
- `infra/observability/grafana/dashboards/profiling.json` - Flame graph, CPU/memory profiles, diff flame graphs

### Modified Files
- `durable-code-app/backend/app/core/telemetry.py` - Custom spans for WebSocket, business logic; span attributes
- `durable-code-app/backend/app/core/profiling.py` - tag_wrapper with trace_id/span_id for trace-to-profile linking
- `infra/observability/tempo/tempo.yml` - Enable metrics generator, span metrics dimensions
- `infra/observability/grafana/datasources.yml` - Configure traceToLogs, traceToMetrics, traceToProfiles, exemplars

### Success Criteria
- Full correlation: metric exemplar -> trace -> logs -> flame graph
- Custom spans appear in trace waterfall
- Flame graphs linked to specific traces

---

## PR 9: Alerting & SLO Monitoring

**Branch**: `feat/observability-alerting`
**Complexity**: Medium | **Dependencies**: PR 7

### New Files (under `infra/observability/grafana/alerting/`)
- `alert-rules.yml` - Error rate >5%, latency >2s p99, service down, saturation >85%, SLO burn-rate (multi-window)
- `contact-points.yml` - Built-in Grafana notifications (placeholder for Slack/email)
- `notification-policies.yml` - Severity-based routing, group-by alertname/service

### Modified Files
- `infra/observability/grafana/grafana.ini` - Enable unified alerting
- `infra/observability/docker-compose.yml` - Volume mount alerting directory

### Success Criteria
- Alert rules visible in Grafana Alerting UI
- Triggering errors causes alert to fire
- Notification policies route by severity

---

## PR 10: Integration, Verification & CI/CD

**Branch**: `feat/observability-integration`
**Complexity**: Medium | **Dependencies**: All previous PRs

### New Files
- `infra/observability/grafana/dashboards/correlation-demo.json` - "Chapter 3 Demo" dashboard showing all 4 pillars
- `infra/scripts/observability-health-check.sh` - Verifies Grafana, datasources, data flow, dashboards

### Modified Files
- `justfile` - Add `just observability status` and `just observability open`
- `.github/workflows/up.yml` - Add observability health check after deploy
- `infra/observability/alloy/config.alloy` - Fine-tune sampling, labels, relabeling

### Success Criteria
- `just observability status` passes all checks
- Correlation demo dashboard shows all 4 pillars
- Full path: latency spike -> exemplar -> trace waterfall -> correlated logs -> flame graph
- CI/CD health check passes

---

## Implementation Guidelines

### Code Standards
- Follow existing patterns in each language/framework
- All files require headers per `.ai/docs/FILE_HEADER_STANDARDS.md`
- Terraform: tags on all resources, locals for repeated values, conditional deployment
- Python: PEP 8, type hints, docstrings on public functions
- TypeScript: strict mode, no `any` types, React hooks rules

### Testing Requirements
- Terraform: `just infra validate` and `just infra plan` for each workspace change
- Backend: Existing tests must continue to pass
- Frontend: Existing tests must continue to pass
- Integration: Health check script validates end-to-end

### Documentation Standards
- Inline code comments for non-obvious logic
- Configuration files include descriptive comments
- Architecture docs page serves as primary documentation

### Security Considerations
- No public access to S3 observability bucket
- EC2 in private subnet only
- ALB routes are the only external access path
- Grafana anonymous access limited to viewer role (read-only)
- No secrets in Docker Compose (use environment variables)

### Performance Targets
- Grafana dashboard load time < 3 seconds
- Trace query response < 5 seconds
- Log query response < 5 seconds
- Memory usage stays within Docker Compose limits

## Rollout Strategy

### Phase 1: Documentation & Foundation (PRs 1-2)
Architecture review gate, then persistent storage and IAM

### Phase 2: Infrastructure (PRs 3-4)
EC2 instance, ALB routing, Docker Compose stack

### Phase 3: Instrumentation (PRs 5-6)
Backend OTel SDK, frontend Faro SDK

### Phase 4: Visualization & Alerting (PRs 7-9)
Dashboards, cross-pillar correlation, alerting rules

### Phase 5: Integration (PR 10)
Health checks, CI/CD integration, demo dashboard

## Success Metrics

### Launch Metrics
- All 4 datasources healthy in Grafana
- Distributed traces span frontend-to-backend
- Golden Signals dashboard populated with live data
- Health check script passes all validations

### Ongoing Metrics
- Observability stack restores after runtime destroy/recreate
- S3 data persists across runtime lifecycle
- Alert rules fire on genuine threshold violations
- Dashboard queries complete within performance targets
