<!--
Purpose: User guide for managing Terraform deployment scopes in infrastructure operations
Scope: Practical usage instructions and operational procedures for deployment scopes
Overview: Step-by-step guide for using the conditional deployment system to manage base and runtime
    infrastructure resources. Covers common operations, cost optimization workflows, troubleshooting,
    and best practices for daily infrastructure management with different deployment scopes.
Dependencies: Requires configured Terraform environment and access to make targets
Exports: Operational procedures and commands for infrastructure deployment management
Interfaces: Used by developers and operators managing infrastructure deployments
Implementation: Production-ready deployment workflows using SCOPE parameter
-->

# How to Manage Terraform Deployment Scopes

## Overview
The infrastructure supports conditional deployment based on deployment scope, allowing you to manage base (persistent) and runtime (ephemeral) resources independently using native Terraform conditionals.

## Deployment Scopes

### Base Resources (Persistent, Expensive)
Deploy only persistent, expensive-to-recreate resources:
- VPC and networking infrastructure
- NAT Gateways (most expensive component ~$45/month)
- ECR repositories
- Route53 hosted zones
- ACM certificates
- Application Load Balancer

### Runtime Resources (Ephemeral, Quick)
Deploy only ephemeral, quick-to-recreate resources:
- ECS cluster and services
- Task definitions
- ALB listeners and target groups
- Service discovery
- CloudWatch log groups
- Route53 A records pointing to ALB

### All Resources (Default)
Deploy everything - both base and runtime resources.

## Common Operations

### Deploy Infrastructure

```bash
# Deploy only base infrastructure
make infra-up SCOPE=base

# Deploy only runtime infrastructure (assumes base exists)
make infra-up SCOPE=runtime

# Deploy everything (default)
make infra-up
make infra-up SCOPE=all
```

### Destroy Infrastructure

```bash
# Destroy only runtime (preserves base)
make infra-down SCOPE=runtime

# Destroy only base (requires confirmation)
make infra-down SCOPE=base CONFIRM=destroy-base

# Destroy everything (requires confirmation)
make infra-down SCOPE=all CONFIRM=destroy-all
```

### Plan Changes

Always plan before applying to understand what will be changed:

```bash
# Plan base resources only
make infra-plan SCOPE=base

# Plan runtime resources only
make infra-plan SCOPE=runtime

# Plan all resources
make infra-plan SCOPE=all
```

## Cost Optimization Strategy

### Daily Cost Savings Workflow

1. **End of Day - Shutdown Runtime**:
   ```bash
   make infra-down SCOPE=runtime
   ```
   Destroys ECS services, listeners, etc. while preserving NAT Gateway and certificates.

2. **Start of Day - Startup Runtime**:
   ```bash
   make infra-up SCOPE=runtime
   ```
   Recreates all runtime resources in ~5 minutes.

### Cost Impact
- NAT Gateway (base): ~$45/month if running 24/7
- Runtime resources: ~$10-15/month if running 24/7
- **Savings: ~66% on runtime costs with daily shutdown**

## Migration from Previous Infrastructure

If you have existing infrastructure created before the conditional deployment feature:

1. **Take a backup of your state**:
   ```bash
   terraform state pull > terraform.tfstate.backup
   ```

2. **Plan with `SCOPE=all`** to see the changes:
   ```bash
   make infra-plan SCOPE=all
   ```

3. **Apply with `SCOPE=all`** to update resource indexing:
   ```bash
   make infra-up SCOPE=all
   ```

The resources will be updated in place to use the new indexing scheme.

## Troubleshooting

### Error: "index [0] is out of range"
This means you're trying to reference a resource that doesn't exist in the current scope.
- Check your deployment scope matches what you expect
- Ensure base resources exist before deploying runtime-only

### Error: "Resource not found"
Runtime resources depend on base resources.
```bash
# Ensure base infrastructure is deployed first
make infra-up SCOPE=base
```

### State Issues
If you encounter state inconsistencies:
```bash
# Refresh the state
make infra-refresh

# Check current resources
make infra-state-list

# As last resort, reinitialize
make infra-reinit
```

## Best Practices

1. **Always plan before applying** to understand changes
2. **Deploy base first** when starting fresh
3. **Use cost optimization** by destroying runtime when not needed
4. **Keep base resources minimal** to reduce always-on costs
5. **Document your deployment schedule** for team awareness
6. **Use the appropriate scope** for your current task
