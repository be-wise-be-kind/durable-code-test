# Purpose: Comprehensive guide for managing the base infrastructure Terraform workspace
# Scope: Base workspace configuration, deployment, and operational procedures
# Overview: This guide provides complete documentation for the base infrastructure workspace which
#     manages persistent resources that are expensive to recreate and form the foundation of the
#     application infrastructure. It covers all base resources including VPC networking, NAT Gateways,
#     ECR repositories, Route53 zones, ACM certificates, and the Application Load Balancer. The guide
#     includes deployment procedures, configuration examples, cost optimization strategies, troubleshooting
#     steps, and best practices for managing these persistent resources. Base resources are designed to
#     survive runtime deployments and provide a stable foundation for ephemeral runtime resources.
# Dependencies: Terraform, AWS credentials, backend configuration, environment tfvars files
# Exports: Operational procedures, configuration examples, troubleshooting guides
# Configuration: Backend state separation, workspace naming conventions, tagging strategies
# Environment: Supports dev, staging, and production environments with workspace isolation
# Related: terraform-workspaces.md for overview, terraform-runtime-workspace.md for runtime guide
# Implementation: Step-by-step procedures for workspace management and resource deployment

# Base Infrastructure Workspace Guide

## Overview

The base workspace manages persistent infrastructure that is rarely modified and expensive to recreate. These resources form the foundation for the application and persist across runtime deployments.

## Resources Managed

### Networking Resources
- **VPC (Virtual Private Cloud)**
  - DNS support enabled
  - Custom CIDR block configuration
  - Tagged for workspace identification

- **Subnets**
  - Public subnets across availability zones for ALB
  - Private subnets across availability zones for ECS tasks
  - Auto-assign public IPs for public subnets

- **Internet Gateway**
  - Provides public subnet internet connectivity
  - Attached to VPC

- **NAT Gateways (Optional)**
  - Enable private subnet internet access
  - One per availability zone for high availability
  - Can be disabled for cost savings in dev

- **Route Tables**
  - Public route table with IGW route
  - Private route tables with NAT routes (if enabled)
  - Proper associations to subnets

- **Security Groups**
  - ALB security group (ports 80/443 ingress)
  - ECS tasks security group (ALB ingress only)
  - VPC endpoints security group (when NAT disabled)

- **VPC Endpoints (When NAT Disabled)**
  - S3 Gateway endpoint (free)
  - ECR API/DKR Interface endpoints
  - CloudWatch Logs Interface endpoint

### Container Registry
- **ECR Repositories**
  - Frontend repository with immutable tags
  - Backend repository with immutable tags
  - Image scanning enabled on push
  - AES256 encryption at rest

- **ECR Lifecycle Policies**
  - Keep last 10 production-tagged images
  - Keep dev/staging images for 7 days
  - Remove untagged images after 1 day

- **ECR Repository Policies**
  - Allow GitHub Actions push access
  - Allow ECS task execution pull access
  - Scoped to specific AWS account

### DNS and Certificates
- **Route53 Hosted Zone (Conditional)**
  - Created when domain_name is configured
  - Manages DNS records for the domain
  - Name servers output for domain delegation

- **ACM Certificate (Conditional)**
  - SSL/TLS certificate for HTTPS
  - DNS validation for automatic renewal
  - Wildcard and subdomain SANs included

### Load Balancer
- **Application Load Balancer**
  - Deployed in public subnets
  - HTTP/2 enabled
  - Cross-zone load balancing disabled (cost optimization)
  - Deletion protection in production

- **S3 Bucket for ALB Logs (Production Only)**
  - Access logs storage with lifecycle rules
  - 30-day retention policy
  - Public access blocked
  - Proper IAM policy for ALB service account

## Outputs for Runtime Workspace

The base workspace exposes comprehensive outputs for the runtime workspace to consume:

### Network Outputs
- `vpc_id` - VPC identifier
- `vpc_cidr` - VPC CIDR block
- `public_subnet_ids` - List of public subnet IDs
- `private_subnet_ids` - List of private subnet IDs
- `alb_security_group_id` - ALB security group ID
- `ecs_tasks_security_group_id` - ECS security group ID

### ECR Outputs
- `backend_ecr_repository_url` - Backend repo URL
- `frontend_ecr_repository_url` - Frontend repo URL
- `backend_ecr_repository_arn` - Backend repo ARN
- `frontend_ecr_repository_arn` - Frontend repo ARN

### ALB Outputs
- `alb_arn` - Load balancer ARN
- `alb_dns_name` - Load balancer DNS name
- `alb_zone_id` - Load balancer zone ID

### DNS Outputs (if configured)
- `route53_zone_id` - Hosted zone ID
- `acm_certificate_arn` - Certificate ARN

## Deployment Commands

### Initialize Workspace
```bash
# Initialize the base workspace for an environment
./infra/scripts/workspace-init.sh base dev
```

### Deploy Infrastructure
```bash
# Deploy base infrastructure with confirmation
./infra/scripts/workspace-deploy-base.sh dev

# Or manually with Terraform
cd infra/terraform/workspaces/base
terraform plan -var-file="../../environments/dev.tfvars"
terraform apply -var-file="../../environments/dev.tfvars"
```

### Check Status
```bash
# View workspace status and outputs
./infra/scripts/workspace-status.sh dev
```

### View Outputs
```bash
cd infra/terraform/workspaces/base
terraform output -json
```

### Destroy Infrastructure (DANGEROUS)
```bash
# Only destroy base infrastructure when absolutely necessary
# This will break the runtime workspace!
cd infra/terraform/workspaces/base
terraform destroy -var-file="../../environments/dev.tfvars"
```

## Cost Optimization Strategies

1. **NAT Gateway Management**
   - Disable in dev environments to save ~$45/month
   - Use VPC endpoints instead (Interface endpoints cost less)
   - Set `enable_nat_gateway = false` in tfvars

2. **Resource Sizing**
   - Use minimum AZ count (2) for dev
   - Larger CIDR blocks to avoid IP exhaustion

3. **Lifecycle Policies**
   - Aggressive ECR image cleanup
   - ALB logs only in production
   - 30-day log retention

## Tagging Strategy

All resources are tagged with:
- `Environment` - dev/staging/prod
- `Workspace` - base-{env}
- `Scope` - base
- `ManagedBy` - Terraform
- `Project` - Project name

These tags enable:
- Cost tracking and allocation
- Resource filtering in AWS console
- Data source lookups from runtime workspace
- Compliance and governance

## Configuration Files

### Required Files
- `infra/terraform/backend-config/base-{env}.hcl` - Backend configuration
- `infra/terraform/environments/{env}.tfvars` - Environment variables

### Example terraform.tfvars
```hcl
environment     = "dev"
aws_region      = "us-west-2"
product_domain  = "durableai"
project_name    = "durable-code"

# Networking
vpc_cidr           = "10.0.0.0/16"
az_count           = 2
enable_nat_gateway = false  # Cost savings

# Domain (optional)
domain_name         = ""
create_route53_zone = false

# Security
enable_waf = false

# Tags
additional_tags = {
  Owner      = "Infrastructure Team"
  CostCenter = "Engineering"
}
```

## Troubleshooting

### Issue: Terraform init fails
- Check AWS credentials are configured
- Verify backend bucket exists
- Ensure backend-config file path is correct

### Issue: Plan shows destroy/recreate
- Check for changes in resource naming
- Verify workspace selection is correct
- Review state file for drift

### Issue: NAT Gateway costs too high
- Disable NAT Gateway in dev/staging
- Implement VPC endpoints for AWS services
- Consider single NAT for dev (less HA)

### Issue: ECR images filling up
- Review lifecycle policies
- Check image tagging strategy
- Manual cleanup if needed

## Best Practices

1. **Always Plan First**
   - Review plan output carefully
   - Check for unintended destructions
   - Verify resource counts

2. **Workspace Hygiene**
   - Keep workspaces synchronized
   - Don't mix resources between workspaces
   - Regular state backups

3. **Change Management**
   - Test changes in dev first
   - Document significant modifications
   - Use PR process for reviews

4. **Security**
   - Never commit sensitive values
   - Use AWS Secrets Manager for secrets
   - Regular security group audits
   - Enable GuardDuty in production

## Dependencies and Interactions

### No Dependencies
The base workspace has no dependencies on other workspaces or external resources.

### Depended Upon By
- **Runtime Workspace** - Uses data sources to reference base resources
- **Application Deployments** - Require ECR repositories and ALB

### State Management
- State stored in S3 with DynamoDB locking
- Separate state file per environment
- Backend encryption enabled

## Migration Notes

When migrating from monolithic to workspace architecture:
1. Take backup of existing state
2. Import existing base resources
3. Verify no resource recreation
4. Test data source references
5. Update documentation

## Related Documentation
- [Terraform Workspaces Overview](terraform-workspaces.md)
- [Runtime Workspace Guide](terraform-runtime-workspace.md)
- [Workspace Migration Guide](terraform-workspace-migration.md)