<!--
Purpose: Complete guide for infrastructure deployment using workspace-separated architecture
Scope: End-to-end deployment procedures, best practices, and operational workflows
Overview: This guide provides comprehensive instructions for deploying and managing infrastructure
    using the workspace-separated architecture. It covers the complete deployment lifecycle from
    initial setup through daily operations, cost optimization, and maintenance. The guide includes
    both automated and manual deployment procedures, troubleshooting guidance, and integration
    with application deployment workflows. Updated for the final implementation with parameter-driven
    just commands and automated orchestration.
Dependencies: Terraform workspaces, AWS credentials, Docker, just targets, GitHub Actions
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

# Verify just targets
just -f Makefile.infra infra-help
```

### First-Time Deployment
```bash
# Deploy complete infrastructure
just infra-up SCOPE=all ENV=dev

# Deploy application
just deploy ENV=dev

# Verify deployment
just infra-status ENV=dev
```

## Deployment Commands

### Infrastructure Deployment

#### Complete Infrastructure
```bash
# Deploy everything (base + runtime)
just infra-up SCOPE=all ENV=dev

# With auto-approval (for automation)
just infra-up SCOPE=all ENV=dev AUTO=true
```

#### Base Infrastructure Only
```bash
# Deploy persistent resources only
just infra-up SCOPE=base ENV=dev

# Use cases:
# - New environment setup
# - Base resource updates
# - Recovery from complete teardown
```

#### Runtime Infrastructure Only
```bash
# Deploy ephemeral resources only (assumes base exists)
just infra-up SCOPE=runtime ENV=dev

# Use cases:
# - Daily restoration after cost optimization
# - Runtime-only updates
# - Development workflow
```

### Infrastructure Destruction

#### Cost-Optimized Teardown (Recommended)
```bash
# Preserve base, destroy runtime
just infra-down SCOPE=runtime ENV=dev

# Benefits:
# - ~50% cost savings
# - 5-minute restoration time
# - Preserves expensive NAT Gateways
```

#### Complete Teardown (Emergency/Weekend)
```bash
# DANGEROUS: Destroys everything including expensive resources
CONFIRM=destroy-base just infra-down SCOPE=all ENV=dev

# Use only for:
# - Complete environment cleanup
# - Extended holidays
# - Emergency cost reduction
```

### Status and Monitoring

#### Infrastructure Status
```bash
# Check deployment status
just infra-status ENV=dev

# Example output:
# Base Infrastructure: ✓ Deployed (7 resources)
# Runtime Infrastructure: ✗ Not deployed
```

#### Planning Changes
```bash
# Plan infrastructure changes
just infra-plan SCOPE=runtime ENV=dev
just infra-plan SCOPE=base ENV=dev
just infra-plan SCOPE=all ENV=dev

# View outputs
just infra-output ENV=dev FORMAT=json
```

## Deployment Workflows

### Daily Development Workflow

#### Morning Startup
```bash
# Check if runtime needs restoration
just infra-status ENV=dev

# If runtime is down, restore it
just infra-up SCOPE=runtime ENV=dev

# Deploy latest application changes
just deploy ENV=dev

# Verify services are healthy
curl -f http://$(just infra-output ENV=dev | grep alb_dns_name)/health
```

#### Evening Shutdown (Cost Optimization)
```bash
# Save costs by destroying runtime
just infra-down SCOPE=runtime ENV=dev

# Estimated savings: $1.50/day (~$30/month)
```

### Staging/Production Workflow

#### Staging Deployment
```bash
# Deploy staging infrastructure
just infra-up SCOPE=all ENV=staging

# Deploy and test application
just deploy ENV=staging
just test ENV=staging

# Monitor for issues
just infra-status ENV=staging
```

#### Production Deployment
```bash
# Ensure staging is validated
just test ENV=staging

# Deploy production infrastructure (if needed)
just infra-up SCOPE=all ENV=prod

# Deploy application with zero-downtime
just deploy ENV=prod

# Monitor deployment
just infra-status ENV=prod
aws ecs describe-services --cluster durableai-prod-cluster --services durableai-prod-frontend
```

### Emergency Procedures

#### Service Restoration
```bash
# Quick service restoration
just infra-up SCOPE=runtime ENV=dev
just deploy ENV=dev

# If base infrastructure is missing
just infra-up SCOPE=all ENV=dev
just deploy ENV=dev
```

#### Emergency Cost Reduction
```bash
# Immediate cost reduction
just infra-down SCOPE=runtime ENV=dev
just infra-down SCOPE=runtime ENV=staging

# If maximum savings needed
CONFIRM=destroy-base just infra-down SCOPE=all ENV=dev
CONFIRM=destroy-base just infra-down SCOPE=all ENV=staging
```

## Environment Management

### Development Environment
```bash
# Aggressive cost optimization
just infra-down SCOPE=runtime ENV=dev    # Nightly
just infra-up SCOPE=runtime ENV=dev      # Morning

# Weekend extended shutdown
CONFIRM=destroy-base just infra-down SCOPE=all ENV=dev    # Friday
just infra-up SCOPE=all ENV=dev          # Monday
```

### Staging Environment
```bash
# Moderate optimization
just infra-down SCOPE=runtime ENV=staging  # Off-hours only
# Keep base infrastructure always up for quick testing
```

### Production Environment
```bash
# Always-on with monitoring
just infra-status ENV=prod
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
just infra-status ENV=dev
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
just infra-check ENV=dev || {
    echo "Infrastructure not ready, restoring..."
    just infra-up SCOPE=runtime ENV=dev
}

# Then deploy application
just deploy ENV=dev
```

### Application Deployment Flow
```bash
# Complete deployment workflow
just infra-up SCOPE=runtime ENV=dev    # Ensure runtime exists
just build-and-push ENV=dev            # Build containers
just deploy ENV=dev                     # Deploy to ECS
just test ENV=dev                       # Run health checks
```

## Troubleshooting

### Common Issues

#### Runtime Won't Deploy
```bash
# Check if base infrastructure exists
just infra-status ENV=dev

# If base missing, deploy it first
just infra-up SCOPE=base ENV=dev
just infra-up SCOPE=runtime ENV=dev
```

#### Application Deployment Fails
```bash
# Verify runtime infrastructure
just infra-check ENV=dev

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
just infra-down SCOPE=runtime ENV=dev

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
just infra-state-list SCOPE=base ENV=dev

# Show resource details
just infra-state-show SCOPE=base ENV=dev RESOURCE=aws_vpc.main

# Import existing resources
just infra-import SCOPE=base ENV=dev RESOURCE=aws_vpc.main ID=vpc-12345678
```

### Workspace Management
```bash
# List workspaces
just infra-workspace-list SCOPE=base ENV=dev

# Create new workspace
just infra-workspace-new SCOPE=base ENV=dev WORKSPACE=base-staging

# Switch workspace
just infra-workspace-select SCOPE=base ENV=dev WORKSPACE=base-dev
```

### Performance Optimization
```bash
# Parallel deployment (experimental)
just infra-up SCOPE=base ENV=dev &
sleep 60  # Wait for base to start
just infra-up SCOPE=runtime ENV=dev &
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