# Purpose: Comprehensive guide for implementing and managing Terraform workspace separation
# Scope: Base and runtime workspace architecture, deployment procedures, and cost optimization
# Overview: This guide documents the Terraform workspace separation strategy that divides infrastructure
#     into base (persistent) and runtime (ephemeral) workspaces for independent lifecycle management.
#     The separation enables significant cost optimization by allowing runtime resources to be destroyed
#     nightly while preserving expensive base resources like NAT Gateways and Route53 zones. It covers
#     workspace naming conventions, initialization procedures, deployment workflows, and operational
#     best practices. The guide includes detailed steps for managing both workspaces, implementing
#     cross-workspace data sources, and maintaining clean separation between resource lifecycles.
# Dependencies: Terraform CLI, AWS credentials, backend configurations, workspace scripts
# Exports: Workspace management procedures, deployment commands, architectural patterns
# Configuration: Separate backend states, workspace naming conventions, environment variables
# Environment: Supports dev, staging, and production with isolated workspace states
# Related: terraform-base-workspace.md for base details, terraform-runtime-workspace.md for runtime
# Implementation: PR-based implementation approach with 6 phases of deployment

# Terraform Workspaces Management Guide

## Overview

This directory contains Terraform workspace configurations that separate infrastructure into two distinct workspaces:

- **Base Workspace**: Persistent infrastructure resources (VPC, NAT, ECR, Route53)
- **Runtime Workspace**: Ephemeral infrastructure resources (ECS, ALB listeners, target groups)

This separation enables:
- Independent lifecycle management
- Cost optimization through runtime shutdown
- Reduced blast radius for changes
- Clean dependency management

## Directory Structure

```
workspaces/
├── base/           # Base infrastructure workspace (PR2)
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   └── providers.tf
├── runtime/        # Runtime infrastructure workspace (PR3)
│   ├── main.tf
│   ├── data.tf    # Data sources for base resources
│   ├── variables.tf
│   └── outputs.tf
└── README.md       # Pointer to AI documentation
```

## Related Documentation

- [Base Workspace Guide](terraform-base-workspace.md) - Detailed guide for base infrastructure
- [Runtime Workspace Guide](terraform-runtime-workspace.md) - Detailed guide for runtime infrastructure (coming in PR3)

## Workspace Naming Convention

Workspaces follow the naming pattern: `{workspace}-{environment}`

- `base-dev`: Base infrastructure for development
- `runtime-dev`: Runtime infrastructure for development
- `base-staging`: Base infrastructure for staging
- `runtime-staging`: Runtime infrastructure for staging
- `base-prod`: Base infrastructure for production
- `runtime-prod`: Runtime infrastructure for production

## Quick Start

### Initialize Workspaces

```bash
# Initialize base workspace for dev
./infra/scripts/workspace-init.sh base dev

# Initialize runtime workspace for dev
./infra/scripts/workspace-init.sh runtime dev
```

### Deploy Infrastructure

```bash
# Deploy base infrastructure (rarely needed)
make infra-up-base ENV=dev

# Deploy runtime infrastructure (daily)
make infra-up-runtime ENV=dev
```

### Destroy Infrastructure

```bash
# Destroy runtime only (nightly for cost savings)
make infra-down-runtime ENV=dev

# Destroy base (requires confirmation - DANGEROUS)
CONFIRM=destroy-base make infra-down-base ENV=dev
```

## Resource Separation

### Base Workspace Resources
Resources that are expensive to recreate and rarely change:
- VPC and Subnets
- Internet Gateway
- NAT Gateways and Elastic IPs
- Route Tables
- Security Groups
- ECR Repositories
- Route53 Hosted Zones
- ACM Certificates
- Application Load Balancer (ALB)

### Runtime Workspace Resources
Resources that can be quickly recreated and change frequently:
- ECS Cluster
- ECS Task Definitions
- ECS Services
- ALB Target Groups
- ALB Listeners and Rules
- Service Discovery
- CloudWatch Log Groups
- IAM Roles (ECS specific)

## Cross-Workspace Communication

Runtime workspace references base resources through data sources:

```hcl
# runtime/data.tf
data "aws_vpc" "main" {
  filter {
    name   = "tag:Environment"
    values = [local.environment]
  }
  filter {
    name   = "tag:Scope"
    values = ["base"]
  }
}
```

## Cost Optimization

### Estimated Monthly Savings
- NAT Gateways: ~$90/month (always running)
- ALB: ~$20/month (always running)
- ECS/Fargate: ~$30/month (12 hours/day = ~$15/month)
- **Total Savings: ~$15/month (11%)**

### Automated Shutdown Schedule
```bash
# Nightly shutdown (cron: 0 20 * * *)
make infra-down-runtime ENV=dev

# Morning startup (cron: 0 8 * * *)
make infra-up-runtime ENV=dev
```

## Implementation Status

This is being implemented in phases:

| PR | Description | Status |
|----|-------------|--------|
| PR1 | Workspace Foundation | **In Progress** |
| PR2 | Base Infrastructure Workspace | Not Started |
| PR3 | Runtime Infrastructure Workspace | Not Started |
| PR4 | Data Sources and Cross-References | Not Started |
| PR5 | Makefile Integration | Not Started |
| PR6 | Documentation and Testing | Not Started |

## Important Notes

### For PR1 (Current)
- Directory structure is created but workspaces don't contain actual infrastructure yet
- Temporary `main.tf` files are created for testing workspace initialization
- Full infrastructure will be added in PR2 and PR3

### State Management
- Each workspace has its own state file in S3
- State paths: `{workspace}/{environment}/terraform.tfstate`
- State locking via DynamoDB table: `terraform-state-lock`

### Backend Configuration
Backend configs are stored in `infra/terraform/backend-config/`:
- `base-{env}.hcl`: Backend config for base workspace
- `runtime-{env}.hcl`: Backend config for runtime workspace

## Common Operations

### Check Workspace Status
```bash
# Show current workspace and available resources
make infra-status ENV=dev
```

### Switch Between Workspaces
```bash
# Work with base infrastructure
cd infra/terraform/workspaces/base
terraform workspace select base-dev

# Work with runtime infrastructure
cd infra/terraform/workspaces/runtime
terraform workspace select runtime-dev
```

### List All Workspaces
```bash
cd infra/terraform/workspaces/base
terraform workspace list
```

## Troubleshooting

### Issue: "No matching VPC found"
**Cause**: Runtime workspace can't find base resources
**Solution**:
1. Verify base workspace is deployed: `make infra-status ENV=dev`
2. Check tags on base resources
3. Redeploy base if needed: `make infra-up-base ENV=dev`

### Issue: "Workspace already exists"
**Cause**: Trying to create an existing workspace
**Solution**: The init script automatically handles this by selecting the existing workspace

### Issue: "Backend initialization failed"
**Cause**: S3 backend not accessible or doesn't exist
**Solution**:
1. Check AWS credentials: `aws sts get-caller-identity`
2. Verify S3 bucket exists: `aws s3 ls s3://durable-code-terraform-state`
3. Check backend config file exists

## Migration from Single State

When migrating from the current single-state setup (PR2-PR3):
1. Backup current state: `terraform state pull > backup.tfstate`
2. Import resources into appropriate workspaces
3. Verify all resources are accounted for
4. Test destroy/recreate cycles

## Safety Measures

1. **Base Destruction Protection**: Requires explicit confirmation
2. **Workspace Isolation**: Separate state files prevent accidental cross-workspace changes
3. **Tag-Based Resource Discovery**: Reduces hardcoded dependencies
4. **Automated Validation**: CI/CD checks workspace configurations

## Next Steps

After PR1 is complete:
- PR2 will add actual base infrastructure to the base workspace
- PR3 will add runtime infrastructure to the runtime workspace
- PR4 will implement data sources for cross-workspace references
- PR5 will integrate everything with Makefile commands
- PR6 will add comprehensive documentation and testing

For detailed implementation status, see: `roadmap/planning/terraform-workspaces/PROGRESS_TRACKER.md`