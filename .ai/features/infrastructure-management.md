# Infrastructure as Code

**Purpose**: Treat infrastructure as a software engineering discipline with complete lifecycle management through code

**Scope**: Complete infrastructure lifecycle management, deployment automation, environment management, cost optimization

**Overview**: Infrastructure as Code implementation that enables reliable, repeatable, and auditable
    infrastructure management through software engineering practices. Provides complete infrastructure
    lifecycle management with the same benefits as application development: version control, code
    review, testing, and automation. Supports declarative infrastructure definition, environment
    parity, and cost-effective deployment strategies.

**Dependencies**: Terraform infrastructure code, AWS services, deployment automation, environment configuration

**Exports**: Infrastructure management patterns, deployment workflows, environment configuration, automation tools

**Related**: TERRAFORM_STANDARDS.md, INFRASTRUCTURE_PRINCIPLES.md, deployment documentation

**Implementation**: Terraform-based infrastructure definitions, automated deployment pipelines, environment management

---

## Infrastructure Management Overview

Infrastructure as Code capability that enables reliable, repeatable, and auditable infrastructure management through software engineering discipline.

## The Feature

### Declarative Infrastructure
Write what you want, not how to build it. Terraform handles the complexity of resource dependencies, creation order, and state management.

### Environment Parity
```bash
just infra-up ENV=dev    # Deploys development
just infra-up ENV=prod   # Deploys production
```
Same code, different configurations. Environment differences are data, not logic.

### Instant Infrastructure
```bash
just infra-plan  # See what will change
just infra-up    # Apply changes
just infra-down  # Destroy everything
```
Complete infrastructure lifecycle in three commands.

### Cost Visibility
Every resource is tagged, tracked, and attributed. Know exactly what costs what and why.

## Architecture

### Terraform State Management
- Remote state in S3 ensures team collaboration
- DynamoDB locking prevents concurrent modifications
- State versioning enables rollback if needed

### Docker-Based Execution
- No local tool installation required
- Consistent versions across team and CI/CD
- Isolated execution environment

### Make Target Abstraction
- Simple commands hide complexity
- Consistent interface across all operations
- Self-documenting through just help

## Capabilities

### What You Can Do

**Create Complete Environments**
```bash
# Spin up a complete development environment
ENV=feature-xyz just infra-up
```

**Preview Changes**
```bash
# See exactly what will change before applying
just infra-plan
```

**Import Existing Resources**
```bash
# Bring manually created resources under Terraform control
just infra-import RESOURCE=aws_s3_bucket.legacy ID=my-bucket
```

**Destroy and Recreate**
```bash
# Complete environment refresh
just infra-down && just infra-up
```

**Cost Optimization**
```bash
# Schedule automatic shutdown
just infra-schedule-shutdown
```

### What Gets Deployed

See `.ai/docs/INFRASTRUCTURE_PRINCIPLES.md` for architectural decisions and component details.

## Development Workflow

### 1. Local Development
```bash
# Start local environment
just dev

# Make infrastructure changes
vim infra/terraform/something.tf

# Validate changes
just infra-validate
```

### 2. Test in Isolation
```bash
# Create feature environment
ENV=feature-123 just infra-up

# Test your changes
# ...

# Tear down when done
ENV=feature-123 just infra-down
```

### 3. Deploy to Shared Environments
```bash
# Plan production changes
ENV=prod just infra-plan

# Apply with approval
ENV=prod just infra-up
```

## Safety Features

### Plan Before Apply
Never blindly apply changes. Always review the plan to understand impact.

### Automated Backups
State files are versioned. Infrastructure can be restored to any previous state.

### Resource Protection
Production resources have deletion protection. Critical resources require additional confirmation.

### Rollback Capability
```bash
# If something goes wrong
just infra-rollback
```

## Integration Points

### CI/CD Pipeline
Infrastructure changes flow through the same pipeline as application code:
1. Branch protection requires PR review
2. Automated plan on PR creation
3. Apply on merge to main
4. Automatic rollback on failure

### Monitoring
Infrastructure changes trigger alerts:
- Cost anomaly detection
- Resource creation/deletion
- Configuration drift
- Compliance violations

### Documentation
Infrastructure is self-documenting:
- Terraform generates dependency graphs
- Resources are tagged with purpose
- Changes are logged in git history

## Best Practices

### Keep It Simple
Don't over-engineer. Start simple and evolve as needed.

### Version Everything
Infrastructure code, variables, and even Just targets are versioned.

### Test Destructively
Regularly destroy and recreate development environments to ensure reproducibility.

### Cost as a Metric
Every PR shows cost impact. Reviews consider cost alongside functionality.

## Common Operations

### Check AWS Credentials
```bash
just infra-check-aws
```

### Format Terraform Code
```bash
just infra-fmt
```

### Clean Terraform Cache
```bash
just infra-clean-cache
```

### Generate Resource Graph
```bash
just infra-graph
```

### Show Current State
```bash
just infra-state-list
```

## Extending the System

### Adding New Resources
1. Write Terraform configuration
2. Add appropriate tags
3. Update outputs if needed
4. Document in PR

### Adding New Environments
1. Create new tfvars file
2. Update Just targets if needed
3. Configure backend
4. Deploy

### Adding New Regions
1. Update provider configuration
2. Adjust resource availability
3. Update variables
4. Test thoroughly

## Philosophy

Infrastructure as Code is about applying software engineering discipline to infrastructure:

- **Reproducibility**: Same code produces same infrastructure
- **Versioning**: Every change is tracked and revertible
- **Testing**: Changes can be validated before production
- **Collaboration**: Team members can review and improve
- **Automation**: Machines do the work, humans just decisions

This isn't just about automation - it's about treating infrastructure with the same rigor, care, and craftsmanship we apply to application code.
