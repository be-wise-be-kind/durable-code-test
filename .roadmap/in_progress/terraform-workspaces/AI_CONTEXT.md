# Terraform Workspaces Implementation - AI Context

## 🎯 Feature Vision

### Problem Statement
The current Terraform infrastructure uses a single state file with conditional `count` logic to separate base (persistent) and runtime (ephemeral) resources. This approach causes "empty tuple" errors when trying to destroy only runtime resources because:
- Runtime resources reference base resources using `[0]` index
- When `deployment_scope=runtime`, base resources have `count = 0`
- Terraform can't resolve references to non-existent resources

### Solution Overview
Implement Terraform workspaces to cleanly separate base and runtime infrastructure:
- **Base Workspace**: VPC, NAT Gateways, ECR repositories, Route53 zones
- **Runtime Workspace**: ECS services, ALB listeners, target groups
- **Data Sources**: Runtime workspace references base resources via data lookups

## 🏗️ Current Architecture

### Existing Structure
```
infra/terraform/
├── resource-scopes.tf    # Defines scope logic
├── networking.tf         # VPC, subnets (base)
├── ecr.tf               # Container registries (base)
├── ecs.tf               # ECS services (runtime)
├── alb.tf               # Load balancer (mixed)
└── variables.tf         # Shared variables
```

### Current Scope Logic
```hcl
# resource-scopes.tf
locals {
  create_base_resources = var.deployment_scope == "base" || var.deployment_scope == "all"
  create_runtime_resources = var.deployment_scope == "runtime" || var.deployment_scope == "all"
}

# Problem: Runtime resources can't reference base when count = 0
resource "aws_lb_target_group" "frontend" {
  count = local.should_create_resource.alb_target_groups ? 1 : 0
  vpc_id = aws_vpc.main[0].id  # Fails when vpc has count = 0
}
```

## 🎯 Target Architecture

### Workspace Structure
```
infra/terraform/
├── workspaces/
│   ├── base/
│   │   ├── main.tf         # Base resources only
│   │   ├── outputs.tf      # Expose IDs for runtime
│   │   └── variables.tf    # Base-specific vars
│   └── runtime/
│       ├── main.tf         # Runtime resources only
│       ├── data.tf         # Lookup base resources
│       └── variables.tf    # Runtime-specific vars
├── modules/               # Shared modules if needed
└── shared/               # Shared configurations
```

### Workspace Separation
**Base Workspace** (`terraform workspace select base`):
- VPC and networking
- NAT Gateways
- Security groups
- ECR repositories
- Route53 zones
- ACM certificates
- ALB (the load balancer itself)

**Runtime Workspace** (`terraform workspace select runtime`):
- ECS cluster
- ECS task definitions
- ECS services
- ALB target groups
- ALB listeners
- Service discovery
- CloudWatch logs

### Data Source Pattern
```hcl
# runtime/data.tf
data "aws_vpc" "main" {
  filter {
    name = "tag:Name"
    values = ["${var.project_name}-${var.environment}-vpc"]
  }
}

# runtime/main.tf
resource "aws_lb_target_group" "frontend" {
  vpc_id = data.aws_vpc.main.id  # Always works
}
```

## 🔧 Implementation Strategy

### Phase 1: Foundation (PR1)
- Create workspace directory structure
- Configure separate backend state paths
- Set up workspace management scripts

### Phase 2: Resource Separation (PR2-3)
- Move base resources to base workspace
- Move runtime resources to runtime workspace
- Maintain backward compatibility during transition

### Phase 3: Cross-Workspace References (PR4)
- Implement data sources in runtime workspace
- Create outputs in base workspace
- Test dependency resolution

### Phase 4: Operational Integration (PR5)
- Update Makefile commands
- Create workspace-aware deployment scripts
- Add safety checks and validations

### Phase 5: Documentation (PR6)
- Migration guide for existing infrastructure
- Operational runbooks
- Troubleshooting guides

## 🎨 Design Decisions

### Why Workspaces Over Modules?
- **Clean State Separation**: Each workspace has independent state
- **Selective Operations**: Can destroy runtime without touching base
- **Cost Optimization**: Destroy expensive runtime resources nightly
- **Safety**: Harder to accidentally destroy base infrastructure

### Why Not Separate Repositories?
- **Complexity**: Would require separate CI/CD pipelines
- **Versioning**: Harder to keep base/runtime in sync
- **Development**: More overhead for local development

### Workspace Naming Convention
- `base-{environment}`: e.g., `base-dev`, `base-prod`
- `runtime-{environment}`: e.g., `runtime-dev`, `runtime-prod`
- Default workspace unused to prevent accidents

## 🔐 Security Considerations

### State File Security
- Separate state files per workspace
- Different access patterns possible
- Base state more restricted than runtime

### Resource Access
- Base resources tagged with workspace
- Runtime can only read base via data sources
- No direct modification across workspaces

### Operational Security
- Separate IAM roles per workspace (optional)
- Audit trail via CloudTrail
- Workspace operations logged

## 💰 Cost Optimization Benefits

### Current Costs (Estimated)
- NAT Gateways: ~$90/month (always running)
- ALB: ~$20/month (always running)
- ECS/Fargate: ~$30/month (when running)
- Total: ~$140/month

### With Workspaces
- Base (always on): ~$110/month
- Runtime (12 hours/day): ~$15/month
- Total: ~$125/month
- **Savings: ~$15/month (11%)**

### Shutdown Strategy
```bash
# Nightly shutdown (cron)
make infra-down-runtime ENV=dev

# Morning startup
make infra-up-runtime ENV=dev
```

## 🚀 Migration Strategy

### Step 1: Prepare
1. Backup current state
2. Document existing resources
3. Test in dev environment first

### Step 2: Create Base Workspace
1. Import existing base resources
2. Verify state integrity
3. Test operations

### Step 3: Create Runtime Workspace
1. Import existing runtime resources
2. Update references to use data sources
3. Test deployments

### Step 4: Cutover
1. Final state backup
2. Switch to workspace-based operations
3. Monitor for issues

## 📊 Success Metrics

### Technical Success
- ✅ Zero "empty tuple" errors
- ✅ Clean destroy operations per scope
- ✅ Faster deployment times
- ✅ Reduced blast radius for changes

### Operational Success
- ✅ Simplified runbooks
- ✅ Clear separation of concerns
- ✅ Easier troubleshooting
- ✅ Better cost tracking

## ⚠️ Potential Challenges

### State Migration
- **Risk**: Corrupted state during migration
- **Mitigation**: Comprehensive backups, test in dev

### Workspace Confusion
- **Risk**: Operators unsure which workspace they're in
- **Mitigation**: Clear prompts, status commands

### Increased Complexity
- **Risk**: More complex than single state
- **Mitigation**: Strong documentation, automation

## 🤖 AI Agent Guidance

### Key Principles
1. **Always Check Workspace**: Before any operation
2. **Never Mix Resources**: Keep separation clean
3. **Use Data Sources**: Don't hardcode cross-workspace values
4. **Tag Everything**: Include workspace in resource tags
5. **Document Changes**: Update runbooks immediately

### Common Patterns
```hcl
# Check workspace
output "current_workspace" {
  value = terraform.workspace
}

# Conditional resources
count = terraform.workspace == "runtime" ? 1 : 0

# Workspace-specific naming
name = "${var.project_name}-${terraform.workspace}-${var.environment}"
```

### Testing Approach
1. Deploy base workspace
2. Verify base resources
3. Deploy runtime workspace
4. Verify runtime can reference base
5. Destroy runtime
6. Verify base intact
7. Redeploy runtime
8. Verify functionality restored

## 📚 Reference Documentation

### Terraform Resources
- [Workspace Documentation](https://www.terraform.io/docs/language/state/workspaces.html)
- [Data Sources](https://www.terraform.io/docs/language/data-sources/index.html)
- [State Management](https://www.terraform.io/docs/language/state/index.html)

### AWS Best Practices
- [Multi-Account Strategy](https://aws.amazon.com/organizations/getting-started/best-practices/)
- [Infrastructure as Code](https://docs.aws.amazon.com/whitepapers/latest/introduction-devops-aws/infrastructure-as-code.html)

### Internal Context
- Current infrastructure costs: See AWS Cost Explorer
- Existing resource IDs: Check Terraform state
- Deployment frequency: ~5-10 times per day in dev

## 🎯 Definition of Done

The feature is complete when:
1. All resources separated into appropriate workspaces
2. Zero errors during scoped destroy operations
3. Makefile commands updated and tested
4. Documentation complete and reviewed
5. Migration completed in dev environment
6. Runbooks updated for operations team
7. Cost optimization verified working

---
**Remember**: This is a high-impact infrastructure change. Test thoroughly in dev before touching production. The goal is zero downtime and improved operational efficiency.