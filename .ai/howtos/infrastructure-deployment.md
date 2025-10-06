<!--
Purpose: Complete guide for infrastructure deployment using workspace-separated architecture
Scope: End-to-end deployment procedures, best practices, and operational workflows
Overview: This guide provides comprehensive instructions for deploying and managing infrastructure
    using the workspace-separated architecture. It covers the complete deployment lifecycle from
    initial setup through daily operations, cost optimization, and maintenance. The guide includes
    both automated and manual deployment procedures, troubleshooting guidance, and integration
    with application deployment workflows. Updated for the final implementation with parameter-driven
    make commands and automated orchestration.
Dependencies: Terraform workspaces, AWS credentials, Docker, make targets, GitHub Actions
Exports: Complete deployment procedures, operational workflows, best practices
Environment: Supports dev, staging, and production with environment-specific configurations
Implementation: Production-ready deployment system with cost optimization and automation
-->

# Infrastructure Deployment Guide

## Overview

This guide covers the complete infrastructure deployment system using workspace-separated architecture. The system divides infrastructure into base (persistent) and runtime (ephemeral) workspaces for optimal cost management and operational flexibility.

## Architecture Overview

### Workspace Separation
- **Base Workspace**: Expensive, persistent resources (VPC, NAT, ECR, Route53, ALB)
- **Runtime Workspace**: Quick-to-recreate resources (ECS, listeners, target groups)

### Benefits
- **Cost Optimization**: 40-60% savings through selective shutdown
- **Operational Safety**: Base resources protected from accidental destruction
- **Development Efficiency**: Fast runtime restoration (5 minutes)
- **Clean Dependencies**: Clear separation of resource lifecycles

## Quick Start

### Prerequisites
```bash
# Required tools
terraform --version  # >= 1.0
docker --version     # Latest
aws --version        # Latest

# AWS credentials
export AWS_PROFILE=terraform-deploy
aws sts get-caller-identity

# Verify make targets
make -f Makefile.infra infra-help
```

### First-Time Deployment
```bash
# Deploy complete infrastructure
make infra-up SCOPE=all ENV=dev

# Deploy application
make deploy ENV=dev

# Verify deployment
make infra-status ENV=dev
```

## Deployment Commands

### Infrastructure Deployment

#### Complete Infrastructure
```bash
# Deploy everything (base + runtime)
make infra-up SCOPE=all ENV=dev

# With auto-approval (for automation)
make infra-up SCOPE=all ENV=dev AUTO=true
```

#### Base Infrastructure Only
```bash
# Deploy persistent resources only
make infra-up SCOPE=base ENV=dev

# Use cases:
# - New environment setup
# - Base resource updates
# - Recovery from complete teardown
```

#### Runtime Infrastructure Only
```bash
# Deploy ephemeral resources only (assumes base exists)
make infra-up SCOPE=runtime ENV=dev

# Use cases:
# - Daily restoration after cost optimization
# - Runtime-only updates
# - Development workflow
```

### Infrastructure Destruction

#### Cost-Optimized Teardown (Recommended)
```bash
# Preserve base, destroy runtime
make infra-down SCOPE=runtime ENV=dev

# Benefits:
# - ~50% cost savings
# - 5-minute restoration time
# - Preserves expensive NAT Gateways
```

#### Complete Teardown (Emergency/Weekend)
```bash
# DANGEROUS: Destroys everything including expensive resources
CONFIRM=destroy-base make infra-down SCOPE=all ENV=dev

# Use only for:
# - Complete environment cleanup
# - Extended holidays
# - Emergency cost reduction
```

### Status and Monitoring

#### Infrastructure Status
```bash
# Check deployment status
make infra-status ENV=dev

# Example output:
# Base Infrastructure: ✓ Deployed (7 resources)
# Runtime Infrastructure: ✗ Not deployed
```

#### Planning Changes
```bash
# Plan infrastructure changes
make infra-plan SCOPE=runtime ENV=dev
make infra-plan SCOPE=base ENV=dev
make infra-plan SCOPE=all ENV=dev

# View outputs
make infra-output ENV=dev FORMAT=json
```

## Deployment Workflows

### Daily Development Workflow

#### Morning Startup
```bash
# Check if runtime needs restoration
make infra-status ENV=dev

# If runtime is down, restore it
make infra-up SCOPE=runtime ENV=dev

# Deploy latest application changes
make deploy ENV=dev

# Verify services are healthy
curl -f http://$(make infra-output ENV=dev | grep alb_dns_name)/health
```

#### Evening Shutdown (Cost Optimization)
```bash
# Save costs by destroying runtime
make infra-down SCOPE=runtime ENV=dev

# Estimated savings: $1.50/day (~$30/month)
```

### Staging/Production Workflow

#### Staging Deployment
```bash
# Deploy staging infrastructure
make infra-up SCOPE=all ENV=staging

# Deploy and test application
make deploy ENV=staging
make test ENV=staging

# Monitor for issues
make infra-status ENV=staging
```

#### Production Deployment
```bash
# Ensure staging is validated
make test ENV=staging

# Deploy production infrastructure (if needed)
make infra-up SCOPE=all ENV=prod

# Deploy application with zero-downtime
make deploy ENV=prod

# Monitor deployment
make infra-status ENV=prod
aws ecs describe-services --cluster durableai-prod-cluster --services durableai-prod-frontend
```

### Emergency Procedures

#### Service Restoration
```bash
# Quick service restoration
make infra-up SCOPE=runtime ENV=dev
make deploy ENV=dev

# If base infrastructure is missing
make infra-up SCOPE=all ENV=dev
make deploy ENV=dev
```

#### Emergency Cost Reduction
```bash
# Immediate cost reduction
make infra-down SCOPE=runtime ENV=dev
make infra-down SCOPE=runtime ENV=staging

# If maximum savings needed
CONFIRM=destroy-base make infra-down SCOPE=all ENV=dev
CONFIRM=destroy-base make infra-down SCOPE=all ENV=staging
```

## Environment Management

### Development Environment
```bash
# Aggressive cost optimization
make infra-down SCOPE=runtime ENV=dev    # Nightly
make infra-up SCOPE=runtime ENV=dev      # Morning

# Weekend extended shutdown
CONFIRM=destroy-base make infra-down SCOPE=all ENV=dev    # Friday
make infra-up SCOPE=all ENV=dev          # Monday
```

### Staging Environment
```bash
# Moderate optimization
make infra-down SCOPE=runtime ENV=staging  # Off-hours only
# Keep base infrastructure always up for quick testing
```

### Production Environment
```bash
# Always-on with monitoring
make infra-status ENV=prod
# No automated shutdowns
# Focus on right-sizing rather than shutdown
```

## Automation and Scheduling

### GitHub Actions Integration
The infrastructure includes automated workflows:

#### Automated Schedules
- **Nightly Teardown**: 8 PM PST (weekdays) - Runtime only
- **Morning Startup**: 8 AM PST (weekdays) - Runtime restoration
- **Weekend Shutdown**: Friday 8 PM - Complete teardown (optional)

#### Manual Triggers
```bash
# Trigger automation manually
gh workflow run nightly-teardown --field environment=dev
gh workflow run morning-startup --field environment=dev

# Check automation status
gh run list --workflow=nightly-teardown --limit=5
```

### Cost Monitoring
```bash
# Daily cost check
make infra-status ENV=dev
echo "Expected daily cost: ~$1.50 (runtime down), ~$3.50 (runtime up)"

# Monthly cost review
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-02-01 \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --group-by Type=DIMENSION,Key=SERVICE
```

## Integration with Application Deployment

### Pre-Deployment Checks
```bash
# Always verify infrastructure before deploying
make infra-check ENV=dev || {
    echo "Infrastructure not ready, restoring..."
    make infra-up SCOPE=runtime ENV=dev
}

# Then deploy application
make deploy ENV=dev
```

### Application Deployment Flow
```bash
# Complete deployment workflow
make infra-up SCOPE=runtime ENV=dev    # Ensure runtime exists
make build-and-push ENV=dev            # Build containers
make deploy ENV=dev                     # Deploy to ECS
make test ENV=dev                       # Run health checks
```

## Troubleshooting

### Common Issues

#### Runtime Won't Deploy
```bash
# Check if base infrastructure exists
make infra-status ENV=dev

# If base missing, deploy it first
make infra-up SCOPE=base ENV=dev
make infra-up SCOPE=runtime ENV=dev
```

#### Application Deployment Fails
```bash
# Verify runtime infrastructure
make infra-check ENV=dev

# Check ECS services
aws ecs describe-services --cluster durableai-dev-cluster --services durableai-dev-frontend

# Force new deployment
aws ecs update-service --cluster durableai-dev-cluster --service durableai-dev-frontend --force-new-deployment
```

#### Cost Optimization Not Working
```bash
# Verify automation is running
gh run list --workflow=nightly-teardown --status=success --limit=7

# Manual cost optimization
make infra-down SCOPE=runtime ENV=dev

# Check for rogue resources
aws ec2 describe-instances --filters "Name=instance-state-name,Values=running"
```

### Detailed Troubleshooting
See [Terraform Workspaces Troubleshooting Guide](.ai/troubleshooting/terraform-workspaces.md) for comprehensive problem resolution.

## Best Practices

### Operational Best Practices
1. **Always plan before applying** changes
2. **Use runtime-only operations** for daily workflows
3. **Verify infrastructure status** before application deployment
4. **Leverage automation** for consistent cost optimization
5. **Monitor costs** through AWS Cost Explorer

### Safety Best Practices
1. **Never destroy base in production** without explicit planning
2. **Use confirmation flags** for destructive operations
3. **Test in dev/staging** before production deployment
4. **Backup state files** before major changes
5. **Document deployment schedules** for team awareness

### Development Best Practices
1. **Use cost optimization** aggressively in development
2. **Preserve base infrastructure** for quick restoration
3. **Automate repetitive operations** with GitHub Actions
4. **Monitor automation success** daily
5. **Plan capacity** based on actual usage patterns

## Cost Impact Summary

### Monthly Savings Potential
- **Development**: 40-60% savings with automated scheduling
- **Staging**: 25-50% savings with selective optimization
- **Production**: 0% savings (always-on for reliability)

### Cost Breakdown (per environment)
```
Base Infrastructure (always-on): ~$55/month
├── NAT Gateways (2): ~$32/month
├── ALB: ~$22/month
└── Other (ECR, Route53): ~$1/month

Runtime Infrastructure: ~$50/month (if always-on)
├── ECS Fargate: ~$45/month
└── CloudWatch Logs: ~$5/month

Total: ~$105/month per environment
Optimized: ~$55-75/month (30-50% savings)
```

### Annual Savings
- **Per Environment**: $360-600/year
- **All Environments**: $1,080-1,800/year (3 environments)

## Advanced Operations

### State Management
```bash
# List resources in state
make infra-state-list SCOPE=base ENV=dev

# Show resource details
make infra-state-show SCOPE=base ENV=dev RESOURCE=aws_vpc.main

# Import existing resources
make infra-import SCOPE=base ENV=dev RESOURCE=aws_vpc.main ID=vpc-12345678
```

### Workspace Management
```bash
# List workspaces
make infra-workspace-list SCOPE=base ENV=dev

# Create new workspace
make infra-workspace-new SCOPE=base ENV=dev WORKSPACE=base-staging

# Switch workspace
make infra-workspace-select SCOPE=base ENV=dev WORKSPACE=base-dev
```

### Performance Optimization
```bash
# Parallel deployment (experimental)
make infra-up SCOPE=base ENV=dev &
sleep 60  # Wait for base to start
make infra-up SCOPE=runtime ENV=dev &
wait  # Wait for both to complete
```

## Security Considerations

### Access Control
- AWS IAM roles with least privilege
- GitHub Actions secrets for automation
- Terraform state encryption at rest
- DynamoDB state locking for concurrency

### Network Security
- Private subnets for ECS tasks
- Security groups with minimal access
- ALB with HTTPS termination
- VPC flow logs for monitoring

### Operational Security
- Backend state stored in S3 with versioning
- Terraform state locking prevents corruption
- Automated backups of critical resources
- Audit trails through CloudTrail

---

**Result**: A production-ready, cost-optimized infrastructure deployment system with 40-60% cost savings through intelligent workspace separation and automated scheduling.