# Grafana Stack Full Observability - AI Context

**Purpose**: AI agent context document for implementing Grafana Stack Full Observability

**Scope**: Complete 4-pillar observability (metrics, logs, traces, profiling) using Grafana stack components on AWS infrastructure

**Overview**: Comprehensive context document for AI agents working on the Grafana Stack Full Observability feature.
    Implements Chapter 3 concepts from the "Before the 3 AM Alert" ebook using the Grafana open-source stack.
    Covers architecture decisions, component selection rationale, cost optimization strategies, and integration
    patterns for delivering metrics (Mimir), logs (Loki), traces (Tempo), and profiling (Pyroscope) with
    unified collection (Alloy) and visualization (Grafana).

**Dependencies**: Existing AWS infrastructure (VPC, ALB, ECS, S3), Terraform workspaces, Docker, OpenTelemetry SDK, Grafana Faro SDK

**Exports**: Architecture decisions, component configuration guidance, integration patterns, and cross-pillar correlation strategies

**Related**: PR_BREAKDOWN.md for implementation tasks, PROGRESS_TRACKER.md for current status, `docs/observability-architecture.html` for visual architecture reference

**Implementation**: Phased PR approach with infrastructure-first, instrumentation-second, dashboards-third strategy

---

## Overview
This feature implements complete observability for the Durable Code application using the Grafana open-source stack. It demonstrates the 4 Golden Signals, flame graphs, latency waterfalls, and full cross-pillar correlation as described in Chapter 3 of "Before the 3 AM Alert."

## Project Background
The Durable Code Test project demonstrates AI-ready development practices with a React/TypeScript frontend and FastAPI backend deployed on AWS ECS. The existing infrastructure uses a 3-workspace Terraform pattern (bootstrap/base/runtime) with cost-optimized ephemeral runtime resources. Adding observability extends this pattern by placing persistent storage (S3) in the base workspace and ephemeral compute (EC2) in the runtime workspace.

## Feature Vision
- **4 Pillars**: Metrics (Mimir), Logs (Loki), Traces (Tempo), Profiling (Pyroscope)
- **Unified Collection**: Grafana Alloy as the single telemetry collector
- **Cross-Pillar Correlation**: Navigate from any signal to any other signal
- **Cost Optimization**: Feature-flagged, single EC2 instance, ephemeral compute
- **Ebook Alignment**: Demonstrates all Chapter 3 concepts with working infrastructure

## Current Application Context
- **Frontend**: React/TypeScript SPA served via ECS Fargate behind ALB
- **Backend**: FastAPI Python application on ECS Fargate behind ALB
- **Infrastructure**: VPC with public/private subnets, ALB with path-based routing, ECS cluster
- **Deployment**: GitHub Actions CI/CD with daily up/down lifecycle for cost savings

## Target Architecture

### Core Components

```
[Browser/Faro SDK] --HTTPS--> [ALB /collect/*] --> [Alloy :12347]
[ECS Backend]      --OTLP-->  [Alloy :4317/:4318] (via private subnet)
                                    |
                   +----------------+----------------+
                   |                |                |                |
              [Mimir:9009]    [Loki:3100]     [Tempo:3200]    [Pyroscope:4040]
                   |                |                |                |
                   +--------> [S3 bucket (persistent in base workspace)]
                                    |
                            [Grafana :3001] <-- ALB /grafana/*
```

### Data Flow
1. **Frontend**: Faro SDK captures web vitals, errors, sessions, and traces; sends to ALB `/collect/*`
2. **ALB**: Routes `/collect/*` to Alloy port 12347, `/grafana/*` to Grafana port 3001
3. **Backend**: OTel SDK sends metrics, traces, and logs via OTLP gRPC to Alloy port 4317
4. **Alloy**: Receives all telemetry, batches, and forwards to appropriate backends
5. **Backends**: Mimir/Loki/Tempo/Pyroscope store data in S3 with local caching
6. **Grafana**: Reads from all 4 backends with cross-pillar correlation configured

### Resource Placement
| Resource | Workspace | Lifecycle | Rationale |
|----------|-----------|-----------|-----------|
| S3 bucket (observability data) | Base | Persistent | Survives runtime destroy/recreate |
| IAM role + instance profile | Base | Persistent | Stable identity for EC2 |
| Security group (observability) | Base | Persistent | Referenced by ALB and ECS SGs |
| EC2 instance (Grafana stack) | Runtime | Ephemeral | Destroyed with `just infra down runtime` |
| ALB target groups + rules | Runtime | Ephemeral | Path routing for /grafana/* and /collect/* |
| ECS task env vars | Runtime | Ephemeral | OTel endpoint configuration |

## Key Decisions Made

### 1. EC2 vs ECS for Grafana Stack
**Decision**: Single EC2 instance with Docker Compose
**Rationale**: 6 containers on Fargate requires 6 task definitions and complex networking. A single EC2 instance with Docker Compose provides simpler management, shared memory, and localhost networking between components. The t3.medium (4GB RAM) fits all components with memory limits.

### 2. Single-Binary Mode
**Decision**: All Grafana stack components run in single-binary (monolithic) mode
**Rationale**: Microservices mode provides horizontal scaling but adds complexity. For a dev/demo environment with low traffic, single-binary mode provides the same functionality with minimal resource overhead.

### 3. Push-Based Telemetry
**Decision**: Applications push telemetry to Alloy (no scraping)
**Rationale**: ECS Fargate tasks have no host-level agent access. Push-based OTel SDK is the standard pattern for containerized workloads. Faro SDK also pushes from the browser.

### 4. Alloy as Unified Collector
**Decision**: Grafana Alloy instead of OpenTelemetry Collector
**Rationale**: Alloy provides native Faro receiver support, built-in Grafana ecosystem integration, and handles all telemetry types. Avoids running a separate OTel Collector.

### 5. S3 Object Storage
**Decision**: Single S3 bucket with prefixes (mimir/, loki/, tempo/, pyroscope/)
**Rationale**: Simpler management than 4 separate buckets. Lifecycle rules apply per prefix. Cost-effective for low-volume dev data.

### 6. Feature Flag Pattern
**Decision**: `enable_observability` boolean variable on all resources
**Rationale**: Follows the project's cost-first philosophy. When disabled, zero additional cost. All resources use `count = var.enable_observability ? 1 : 0`.

### 7. ALB Path Routing
**Decision**: `/grafana/*` and `/collect/*` routes on existing ALB
**Rationale**: Reuses existing ALB (no additional load balancer cost). Path-based routing provides clean separation. Grafana runs at a subpath natively.

## Integration Points

### With Existing Features
- **ALB**: Additional listener rules at priorities 90-91 (below existing rules)
- **VPC**: EC2 in existing private subnets
- **Security Groups**: New SG references existing ALB and ECS SGs for ingress
- **ECS Task Definitions**: Additional env vars for OTel configuration
- **CI/CD**: Health check step added to deployment workflow

### Cross-Pillar Correlation Paths
- **Metric Exemplar -> Trace**: Mimir exemplar config links to Tempo trace ID
- **Trace -> Logs**: Tempo traceToLogs config filters Loki by trace_id
- **Trace -> Profile**: Tempo traceToProfiles config links to Pyroscope via span labels
- **Alert -> Dashboard -> Trace -> Root Cause**: Full investigation workflow

## Success Metrics
- All 4 Grafana datasources report healthy status
- Frontend-to-backend distributed traces show same trace ID
- Metric exemplars navigate directly to specific traces
- Flame graphs display CPU/memory profiles linked to specific spans
- Structured logs contain trace_id and span_id fields
- Full correlation path: metric -> trace -> log -> profile

## Technical Constraints
- **t3.medium memory**: 4GB total, allocate ~2.7GB to Docker containers, leave headroom for OS
- **Private subnet**: EC2 has no public IP; accessed only via ALB or SSM Session Manager
- **Fargate networking**: No host networking mode; OTLP must use EC2 private IP
- **ALB path routing**: Grafana subpath requires `GF_SERVER_ROOT_URL` and `GF_SERVER_SERVE_FROM_SUB_PATH`
- **S3 permissions**: EC2 instance profile requires specific S3 bucket policy

## Architecture Documentation

The file `docs/observability-architecture.html` is the canonical visual reference for this feature. It contains:
- System architecture diagram (data flow from sources through Alloy to backends)
- Resource ERD showing all AWS resources and their relationships across workspaces
- Component details (ports, memory limits, modes)
- Cross-pillar correlation paths
- Network and security layout
- Cost analysis
- Dashboard mockups for all planned Grafana dashboards

**This document is both a reference and a living artifact.** When implementing PRs:
- **Read it** before starting work to understand the architecture visually
- **Update it** if any architectural decision changes (e.g., ports, memory limits, resource placement, data flow)

## AI Agent Guidance

### When Implementing Infrastructure (PRs 2-3)
- Follow existing Terraform patterns in `infra/terraform/workspaces/`
- Use `count = var.enable_observability ? 1 : 0` on all resources
- Include proper file headers per `.ai/docs/FILE_HEADER_STANDARDS.md`
- Reference base outputs in runtime via `data.terraform_remote_state.base`
- Tag all resources consistently with Environment, Project, Component tags

### When Implementing Instrumentation (PRs 5-6)
- Gate all instrumentation behind environment variables (OTEL_ENABLED, VITE_FARO_ENABLED)
- Ensure structured logging includes trace_id/span_id in every log line
- Use head-based sampling with configurable rate for traces
- Frontend Faro must propagate W3C TraceContext to API calls for distributed tracing

### Common Patterns
- **Feature flags**: All resources conditional on `enable_observability`
- **S3 prefixes**: `mimir/`, `loki/`, `tempo/`, `pyroscope/` within single bucket
- **Docker memory limits**: Sum must not exceed ~2.7GB on t3.medium
- **OTLP endpoint**: `http://<EC2_PRIVATE_IP>:4317` for gRPC, `:4318` for HTTP
- **Grafana subpath**: All internal links must respect `/grafana/` prefix

## Risk Mitigation
- **Memory pressure**: Monitor EC2 memory; Docker Compose memory limits prevent OOM-kill cascading
- **S3 costs**: Lifecycle rules delete old data (7d dev, 30d prod)
- **Network latency**: All components on same EC2 instance = localhost communication
- **Data persistence**: S3 in base workspace survives runtime destroy/recreate
- **Rollback**: Feature flag disables all resources; no data migration needed

## Ebook Chapter 3 Coverage
| Concept | PR | Implementation |
|---------|-----|---------------|
| Four Pillars | PRs 4-6 | Mimir, Loki, Tempo, Pyroscope |
| Four Golden Signals | PR 7 | Latency/Traffic/Errors/Saturation dashboard |
| OpenTelemetry Standard | PR 5 | OTel SDK for FastAPI |
| Distributed Tracing | PRs 5, 6, 8 | Tempo + W3C TraceContext |
| Structured Logging | PR 5 | JSON Loguru with trace_id injection |
| Continuous Profiling | PRs 5, 8 | Pyroscope SDK + flame graphs |
| Exemplars | PR 8 | Mimir exemplar -> Tempo links |
| Trace-to-Log Correlation | PR 8 | Tempo -> Loki via trace_id |
| Trace-to-Profile Correlation | PR 8 | Tempo -> Pyroscope via span labels |
| RED Method | PR 7 | Backend Rate/Errors/Duration dashboard |
| USE Method | PR 7 | Infrastructure Utilization/Saturation/Errors |
| SLO-based Alerting | PR 9 | Multi-window burn rate rules |
| Sampling Strategies | PR 5 | Head-based sampling |
| Frontend Observability | PR 6 | Faro: LCP, INP, CLS, errors, sessions |
