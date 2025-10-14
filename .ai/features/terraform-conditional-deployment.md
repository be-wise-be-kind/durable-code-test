# Terraform Conditional Deployment Feature

**Purpose**: Feature documentation for Terraform conditional deployment system with native count-based resource management

**Scope**: Technical implementation details and architecture patterns for deployment scopes and conditional resource creation

**Overview**: Documents the native Terraform conditional deployment system that replaces target-based
    deployment with count parameters for efficient infrastructure management. Covers implementation
    patterns, resource categorization, and integration points for managing base vs runtime infrastructure
    resources through conditional deployment logic. Provides production-ready patterns for selective
    resource creation based on deployment scope variables.

**Dependencies**: Terraform 1.0+, count parameters, local variables, deployment scope configuration

**Exports**: Technical patterns, implementation guidelines, conditional resource creation strategies

**Related**: Infrastructure management documentation, Terraform standards, deployment automation

**Implementation**: Production-ready conditional deployment using deployment_scope variable and count parameters

---

## Feature Overview
Native Terraform conditional deployment using `count` parameters to selectively create resources based on deployment scope, replacing the problematic `-target` flag approach.

## Technical Implementation

### Core Architecture

The conditional deployment system uses Terraform's native `count` parameter with local variables to determine which resources should be created:

```hcl
# Each resource uses a count parameter based on scope
resource "aws_ecs_cluster" "main" {
  count = local.should_create_resource.ecs_cluster ? 1 : 0
  # ... configuration ...
}
```

### Helper Variables Structure

In `infra/terraform/resource-scopes.tf`:

```hcl
locals {
  # Determine if base resources should be created
  create_base_resources = var.deployment_scope == "base" || var.deployment_scope == "all"

  # Determine if runtime resources should be created
  create_runtime_resources = var.deployment_scope == "runtime" || var.deployment_scope == "all"

  # Resource creation map
  should_create_resource = {
    # Base resources
    vpc               = local.create_base_resources
    networking        = local.create_base_resources
    ecr               = local.create_base_resources
    route53           = local.create_base_resources
    acm               = local.create_base_resources
    alb               = local.create_base_resources

    # Runtime resources
    ecs_cluster       = local.create_runtime_resources
    ecs_services      = local.create_runtime_resources
    alb_listeners     = local.create_runtime_resources
    alb_target_groups = local.create_runtime_resources
    service_discovery = local.create_runtime_resources
    cloudwatch_logs   = local.create_runtime_resources
  }
}
```

### Resource Reference Pattern

All references to conditional resources must use indexing:

```hcl
# Reference to conditional VPC
vpc_id = aws_vpc.main[0].id

# Reference to conditional security group
security_groups = [aws_security_group.alb[0].id]
```

### Output Handling

Outputs handle conditional resources with ternary operators to avoid errors:

```hcl
output "vpc_id" {
  value = local.should_create_resource.vpc ? aws_vpc.main[0].id : ""
}

output "ecs_cluster_name" {
  value = local.should_create_resource.ecs_cluster ? aws_ecs_cluster.main[0].name : "Not created"
}
```

## Resource Categorization

### Base Resources
Resources that are expensive to create/destroy and should persist:
- VPC and all networking components
- NAT Gateways (highest cost ~$45/month)
- ECR repositories
- Route53 hosted zones
- ACM certificates and validation
- Application Load Balancer (ALB itself)
- Security groups

### Runtime Resources
Resources that can be quickly recreated and are safe to destroy:
- ECS cluster and capacity providers
- ECS services and task definitions
- ALB listeners and target groups
- ALB listener rules
- Service discovery namespace and services
- CloudWatch log groups
- Route53 A records (pointing to ALB)
- IAM roles for ECS tasks

## Benefits Over Target-Based Approach

1. **Terraform Native**: Uses built-in conditional features, no external scripts
2. **No Warnings**: Eliminates `-target` flag warnings from Terraform
3. **Dependency Safety**: Terraform manages all dependencies correctly
4. **State Consistency**: Single source of truth in state file
5. **Cleaner Implementation**: All logic in Terraform files
6. **Better Maintenance**: No external bash scripts to maintain

## Integration Points

### Makefile Integration
The Makefile passes the deployment scope as a Terraform variable:
```justfile
# No more target generation needed
infra-up:
	terraform apply -var="deployment_scope=$(SCOPE)" -auto-approve
```

### Variable Definition
```hcl
variable "deployment_scope" {
  description = "Deployment scope: runtime, base, or all"
  type        = string
  default     = "all"

  validation {
    condition     = contains(["runtime", "base", "all"], var.deployment_scope)
    error_message = "The deployment_scope must be one of: runtime, base, all."
  }
}
```

## Implementation Checklist

When adding new resources, follow this pattern:

1. **Categorize the resource** as base or runtime
2. **Add conditional count**:
   ```hcl
   count = local.should_create_resource.<category> ? 1 : 0
   ```
3. **Update all references** to use `[0]` indexing
4. **Handle outputs** with ternary operators
5. **Test all three scopes** to ensure proper behavior
6. **Document the resource category** in resource-scopes.tf comments

## Known Considerations

1. **Resource Dependencies**: Runtime resources often depend on base resources
2. **Index References**: All conditional resources require `[0]` indexing
3. **For_each Compatibility**: Resources using `for_each` need special handling
4. **Data Sources**: Generally don't need conditionals
5. **Module Compatibility**: Modules need count parameter passed through
