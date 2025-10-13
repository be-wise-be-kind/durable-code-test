# Dual-Architecture Terraform Configuration

**Purpose**: Define infrastructure management approach separating persistent base resources from ephemeral runtime resources

**Scope**: AWS infrastructure deployment, cost optimization, and development workflow efficiency

**Overview**: Establishes a dual-architecture approach to infrastructure management that separates
    slow-to-provision persistent resources (VPC, certificates, NAT gateways) from fast-to-deploy
    runtime resources (ECS clusters, services, listeners). This architecture eliminates certificate
    validation delays, enables rapid infrastructure recovery, and supports cost-effective development
    workflows by allowing selective resource destruction and recreation.

**Dependencies**: Terraform infrastructure code, AWS services, Makefile.infra, deployment scripts

**Exports**: Infrastructure architecture patterns, deployment workflows, cost optimization strategies

**Related**: Makefile.infra, infra/terraform/, TERRAFORM_STANDARDS.md, INFRASTRUCTURE_PRINCIPLES.md

**Implementation**: Terraform resource targeting with scope-based deployment scripts and automated target generation

---

## Architecture Overview
The dual-architecture approach separates persistent "base" resources from ephemeral "runtime" resources, eliminating certificate validation delays and enabling fast infrastructure recovery.

## Problem Solved
- **Certificate Validation Delays**: ACM certificates can take 30+ minutes to validate
- **NAT Gateway Provisioning**: NAT Gateways take 5-10 minutes to provision
- **Cost Optimization**: Destroying runtime resources saves money while preserving base infrastructure
- **Fast Recovery**: Runtime resources can be recreated in <5 minutes

## Architecture Separation

### Base Resources (Persistent)
Resources that are slow to provision and expensive to recreate:
- **VPC and Networking**: VPC, subnets, Internet Gateway, NAT Gateway
- **Security Groups**: ALB and ECS task security groups
- **ECR Repositories**: Container registries with lifecycle policies
- **Route53 and ACM**: DNS zones and SSL certificates (30+ min validation)
- **ALB**: Application Load Balancer (but not listeners)

### Runtime Resources (Ephemeral)
Resources that can be quickly destroyed and recreated:
- **ECS Cluster and Services**: Container orchestration
- **Task Definitions**: Container configurations
- **IAM Roles**: ECS execution and task roles
- **CloudWatch Logs**: Application logs
- **ALB Listeners and Targets**: HTTP/HTTPS listeners, target groups
- **Service Discovery**: Private DNS namespaces
- **Route53 Records**: ALB alias records

## Usage

### Deploy Infrastructure

```bash
# Deploy everything (first time setup)
just infra-up SCOPE=all AUTO=true

# Deploy only runtime resources (fast, default)
just infra-up

# Deploy only base resources
just infra-up SCOPE=base

# Deploy with specific environment
ENV=prod just infra-up SCOPE=all
```

### Destroy Infrastructure

```bash
# Destroy only runtime resources (default, safe, fast)
just infra-down

# Destroy everything (removes all AWS resources)
just infra-down SCOPE=all

# Destroy only base resources (rare)
just infra-down SCOPE=base

# Auto-approve destruction (use with caution)
just infra-down AUTO=true
```

### Plan Changes

```bash
# Plan runtime changes (default)
just infra-plan

# Plan all changes
just infra-plan SCOPE=all

# Plan base resource changes
just infra-plan SCOPE=base
```

## Cost Optimization Workflow

### Daily Development Workflow
```bash
# Morning: Spin up runtime resources
just infra-up              # Deploys ECS, listeners in <5 minutes

# Evening: Tear down runtime resources
just infra-down            # Removes ECS, saves ~$4/day

# Base resources remain: VPC, NAT ($1.50/day), ECR, Route53
```

### Weekend Shutdown
```bash
# Friday evening: Destroy everything
just infra-down SCOPE=all AUTO=true

# Monday morning: Recreate infrastructure
just infra-up SCOPE=all AUTO=true
```

## Implementation Details

### Makefile Parameters
- `SCOPE=runtime` (default): Deploy/destroy only runtime resources
- `SCOPE=base`: Deploy/destroy only base resources
- `SCOPE=all`: Deploy/destroy everything
- `AUTO=true`: Skip confirmation prompts (use with caution)
- `ENV=dev|staging|prod`: Select environment (default: dev)

### Resource Targeting
The `generate-targets.sh` script creates appropriate Terraform `-target` flags based on the SCOPE parameter. This ensures only the specified resources are affected.

### State Management
All resources remain in a single Terraform state file. The separation is achieved through targeted operations, not separate state files. This maintains dependency tracking and prevents orphaned resources.

## Benefits

1. **Fast Recovery**: Runtime resources recreate in <5 minutes vs 30+ minutes for full stack
2. **Cost Savings**: Destroy runtime resources during off-hours (saves ~60% on compute costs)
3. **Certificate Preservation**: ACM certificates remain validated, avoiding 30+ minute delays
4. **NAT Gateway Persistence**: Avoid 5-10 minute NAT Gateway provisioning times
5. **Flexible Management**: Choose what to deploy/destroy based on needs

## Migration Notes

### From Existing Infrastructure
1. The current infrastructure remains compatible
2. No state migration required
3. Default behavior (`just infra-down`) now only affects runtime resources
4. To maintain old behavior, use `just infra-down SCOPE=all`

### Rollback Plan
If issues occur, the previous behavior can be restored by:
```bash
# Deploy everything
just infra-up SCOPE=all

# Or use Terraform directly
cd infra/terraform
terraform apply -var-file=../environments/dev.tfvars
```

## Testing

### Verify Scope Targeting
```bash
# Check what would be destroyed (dry run)
just infra-plan SCOPE=runtime
just infra-plan SCOPE=base
just infra-plan SCOPE=all
```

### Test Deployment
```bash
# 1. Deploy base infrastructure
just infra-up SCOPE=base

# 2. Deploy runtime on top
just infra-up SCOPE=runtime

# 3. Destroy runtime only
just infra-down SCOPE=runtime

# 4. Verify base remains
aws ec2 describe-vpcs --region us-west-2
aws ec2 describe-nat-gateways --region us-west-2

# 5. Recreate runtime (should be fast)
just infra-up SCOPE=runtime
```

## Troubleshooting

### State Lock Issues
```bash
# If terraform state is locked
just infra-plan SCOPE=runtime  # Will show if state is accessible
```

### Missing Dependencies
If runtime resources fail to deploy due to missing base resources:
```bash
# Ensure base resources exist
just infra-up SCOPE=base
# Then deploy runtime
just infra-up SCOPE=runtime
```

### Verification Commands
```bash
# Check what's currently deployed
aws ecs list-clusters
aws ec2 describe-vpcs
aws elbv2 describe-load-balancers

# View Terraform state
cd infra/terraform
terraform state list
```

## Cost Impact

### Before PR4.5
- Full deployment: ~$70/month (24/7)
- Full teardown/recreation: 30-45 minutes
- Certificate validation: 30+ minutes each time

### After PR4.5
- Base resources only: ~$47/month (VPC, NAT, ECR, Route53)
- Runtime resources: ~$23/month when active
- Runtime recreation: <5 minutes
- Certificate validation: One-time, then preserved

### Savings Potential
- Daily shutdown (12 hours): Save ~$11/month
- Weekend shutdown: Save ~$7/month
- Combined: Save ~$18/month (26% reduction)

## Files Modified

1. **Makefile.infra**: Added SCOPE parameter logic
2. **infra/terraform/resource-scopes.tf**: Defines resource categorization
3. **infra/scripts/generate-targets.sh**: Generates Terraform target flags
4. **This README**: Documentation

## Next Steps

After PR4.5, consider:
1. Implement scheduled Lambda functions for automated shutdown/startup
2. Add CloudWatch dashboards to monitor resource states
3. Create cost allocation tags for better tracking
4. Set up SNS notifications for infrastructure changes
