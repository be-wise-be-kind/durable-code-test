<!--
Purpose: User guide for managing Terraform workspace operations with complete deployment workflows
Scope: Practical operational procedures for workspace-separated infrastructure management
Overview: This guide provides comprehensive instructions for using the workspace-separated infrastructure
    system that divides resources into base (persistent) and runtime (ephemeral) workspaces. It covers
    all operational aspects including deployment commands, cost optimization workflows, troubleshooting,
    and best practices for daily infrastructure management. The guide is updated for the final workspace
    implementation with parameter-driven make commands and automated orchestration scripts.
Dependencies: Requires configured Terraform workspaces, AWS credentials, and updated make targets
Exports: Complete operational procedures and commands for workspace-separated infrastructure
Interfaces: Used by developers and operators managing infrastructure deployments
Implementation: Production-ready deployment workflows using SCOPE parameter system
-->

# Terraform Workspace Operations Guide

## Overview

Infrastructure is separated into two independent Terraform workspaces for optimized cost management and operational flexibility:

- **Base Workspace**: Persistent, expensive infrastructure (VPC, NAT, ECR, Route53, ALB)
- **Runtime Workspace**: Ephemeral, quick-to-recreate infrastructure (ECS, listeners, target groups)

This separation enables significant cost optimization by allowing runtime resources to be destroyed nightly while preserving expensive base resources.

## Quick Reference Commands

### Common Operations
```bash
# Deploy everything from scratch
make infra-up SCOPE=all ENV=dev

# Deploy only runtime (assumes base exists)
make infra-up SCOPE=runtime ENV=dev

# Nightly cost savings - destroy runtime only
make infra-down SCOPE=runtime ENV=dev

# Morning restore - recreate runtime
make infra-up SCOPE=runtime ENV=dev

# Deploy application after infrastructure is ready
make deploy ENV=dev

# Check infrastructure status
make infra-status ENV=dev
```

## Detailed Command Reference

### Infrastructure Deployment

#### Deploy All Infrastructure
```bash
# Creates both base and runtime infrastructure in proper order
make infra-up SCOPE=all ENV=dev
```
This command:
1. Deploys base infrastructure first (VPC, NAT, ECR, etc.)
2. Then deploys runtime infrastructure (ECS, ALB listeners, etc.)
3. Ensures proper dependency ordering

#### Deploy Base Infrastructure Only
```bash
# Creates only persistent, expensive resources
make infra-up SCOPE=base ENV=dev
```
Use when:
- Setting up a new environment for the first time
- Base infrastructure was destroyed and needs recreation
- Updating only base resource configurations

#### Deploy Runtime Infrastructure Only
```bash
# Creates only ephemeral, quick-to-recreate resources
make infra-up SCOPE=runtime ENV=dev
```
Use when:
- Base infrastructure already exists
- Restoring service after nightly shutdown
- Deploying runtime-only changes

### Infrastructure Destruction

#### Destroy Runtime Only (Recommended for Cost Savings)
```bash
# Destroys ECS services, ALB listeners, etc. while preserving base
make infra-down SCOPE=runtime ENV=dev
```
This is the **recommended daily shutdown** command that:
- Preserves expensive NAT Gateways and certificates
- Removes compute resources that accumulate charges
- Can be restored quickly in the morning

#### Destroy All Infrastructure (Full Teardown)
```bash
# DANGEROUS: Destroys everything including expensive base resources
CONFIRM=destroy-base make infra-down SCOPE=all ENV=dev
```
**Warning**: This destroys NAT Gateways (~$1.08/day) and other expensive resources that take time to recreate.

#### Base Destruction Protection
Direct base destruction is prohibited for safety:
```bash
# This will FAIL intentionally
make infra-down SCOPE=base ENV=dev

# To destroy base, use the all scope with confirmation
CONFIRM=destroy-base make infra-down SCOPE=all ENV=dev
```

### Status and Monitoring

#### Check Infrastructure Status
```bash
# Shows deployment status of both workspaces
make infra-status ENV=dev
```
Output shows:
- Which workspaces are deployed
- Resource counts and health
- Service URLs and endpoints

#### Plan Infrastructure Changes
```bash
# Plan changes for specific scope
make infra-plan SCOPE=runtime ENV=dev
make infra-plan SCOPE=base ENV=dev
make infra-plan SCOPE=all ENV=dev
```

## Cost Optimization Workflows

### Daily Cost Savings (Recommended)

#### End of Workday Shutdown
```bash
# Save ~60% on compute costs
make infra-down SCOPE=runtime ENV=dev
```
This preserves:
- ✅ VPC and networking (~$1.08/day for NAT)
- ✅ ECR repositories and container images
- ✅ Route53 zones and SSL certificates
- ✅ Application Load Balancer configuration

#### Start of Workday Restore
```bash
# Restore service in ~5 minutes
make infra-up SCOPE=runtime ENV=dev

# Deploy latest application version
make deploy ENV=dev
```

### Weekend/Extended Shutdown
For longer periods (weekends, holidays):
```bash
# Friday evening - complete shutdown
CONFIRM=destroy-base make infra-down SCOPE=all ENV=dev

# Monday morning - full restoration
make infra-up SCOPE=all ENV=dev
make deploy ENV=dev
```
**Note**: This saves maximum cost but requires ~10 minutes for NAT Gateway recreation.

### GitHub Actions Automation
The infrastructure includes automated workflows:
- **Nightly Teardown**: Destroys runtime at 8 PM PST (weekdays)
- **Morning Startup**: Restores runtime at 8 AM PST (weekdays)
- **Manual Triggers**: Can be run on-demand from GitHub Actions tab

## Deployment Scenarios

### New Environment Setup
```bash
# 1. Deploy all infrastructure
make infra-up SCOPE=all ENV=dev

# 2. Deploy application
make deploy ENV=dev

# 3. Verify deployment
make infra-status ENV=dev
```

### Daily Development Workflow
```bash
# Morning: Restore runtime (if automated shutdown occurred)
make infra-up SCOPE=runtime ENV=dev

# Deploy your changes
make deploy ENV=dev

# Evening: Optional manual shutdown for cost savings
make infra-down SCOPE=runtime ENV=dev
```

### Hotfix Deployment
```bash
# Ensure runtime is up
make infra-status ENV=dev

# If runtime is down, restore it
make infra-up SCOPE=runtime ENV=dev

# Deploy the hotfix
make deploy ENV=dev
```

### Staging/Production Deployment
```bash
# Staging deployment
make infra-up SCOPE=all ENV=staging
make deploy ENV=staging

# Production deployment (after staging validation)
make infra-up SCOPE=all ENV=prod
make deploy ENV=prod
```

## Integration with Application Deployment

### Pre-deployment Checks
Always verify infrastructure status before deploying:
```bash
# Check if runtime infrastructure is ready
make infra-status ENV=dev

# If runtime is down, restore it first
if ! make infra-check ENV=dev; then
    echo "Restoring runtime infrastructure..."
    make infra-up SCOPE=runtime ENV=dev
fi

# Now deploy application
make deploy ENV=dev
```

### Application Deployment Process
The `make deploy` command automatically:
1. Checks if runtime infrastructure exists
2. Builds and pushes container images to ECR
3. Updates ECS task definitions
4. Performs rolling deployment of services
5. Verifies deployment health

## Environment Management

### Multiple Environments
```bash
# Development environment
make infra-up SCOPE=all ENV=dev
make deploy ENV=dev

# Staging environment
make infra-up SCOPE=all ENV=staging
make deploy ENV=staging

# Production environment
make infra-up SCOPE=all ENV=prod
make deploy ENV=prod
```

### Environment-Specific Considerations
- **dev**: Aggressive cost optimization with nightly shutdowns
- **staging**: Selective shutdowns, always up during business hours
- **prod**: Always-on runtime, base resources never destroyed

## Workspace Architecture Details

### Base Workspace Resources
Located in `infra/terraform/workspaces/base/`:
- VPC with public/private subnets
- Internet Gateway and NAT Gateways
- Security Groups (ALB and ECS tasks)
- ECR repositories for container images
- Route53 hosted zone (conditional)
- ACM SSL certificates (conditional)
- Application Load Balancer (ALB)

### Runtime Workspace Resources
Located in `infra/terraform/workspaces/runtime/`:
- ECS cluster with Container Insights
- ECS task definitions (frontend/backend)
- ECS services with Fargate launch type
- ALB target groups and listeners
- CloudWatch log groups
- IAM roles for ECS tasks

### Cross-Workspace Communication
Runtime workspace references base resources via data sources:
```hcl
# Example: VPC lookup by tags
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

## Best Practices

### Operational Best Practices
1. **Always plan before applying** to understand changes
2. **Deploy base infrastructure first** when starting fresh
3. **Use runtime-only operations** for daily workflows
4. **Verify infrastructure status** before application deployment
5. **Leverage automation** for consistent cost optimization
6. **Monitor costs** through AWS Cost Explorer

### Safety Practices
1. **Never destroy base in production** without explicit planning
2. **Use confirmation flags** for destructive operations
3. **Backup state files** before major changes
4. **Test in dev/staging** before production deployment
5. **Document deployment schedules** for team awareness

### Cost Optimization Practices
1. **Implement nightly runtime shutdowns** for development
2. **Use GitHub Actions** for automated scheduling
3. **Monitor NAT Gateway costs** as primary expense driver
4. **Right-size ECS tasks** based on actual usage
5. **Review costs monthly** and adjust strategies

## Troubleshooting Quick Reference

See the comprehensive [Terraform Workspaces Troubleshooting Guide](.ai/troubleshooting/terraform-workspaces.md) for detailed solutions.

### Common Issues
```bash
# Runtime deployment fails - check if base exists
make infra-status ENV=dev

# Application deployment fails - restore runtime
make infra-up SCOPE=runtime ENV=dev

# State corruption - refresh and retry
make infra-refresh ENV=dev
```

## Cost Impact Summary

### Monthly Cost Breakdown (24/7 operation)
- **NAT Gateways**: ~$32/month (2 AZs × $45/month ÷ 2.8)
- **ALB**: ~$22/month
- **ECS Fargate**: ~$45/month (2 services)
- **ECR**: ~$1/month
- **Route53**: ~$0.50/month
- **Total**: ~$100/month

### Cost Savings with Workspace Separation
- **Nightly Runtime Shutdown** (12 hours/day): ~50% savings on ECS costs
- **Weekend Full Shutdown**: Additional ~15% total savings
- **Maximum Savings**: ~40-60% total infrastructure costs

The workspace separation enables granular cost control while maintaining operational simplicity.