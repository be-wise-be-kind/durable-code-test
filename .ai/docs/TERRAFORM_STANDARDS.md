# Terraform Standards and Best Practices

**Purpose**: Define coding standards, naming conventions, and best practices for Terraform infrastructure code

**Scope**: All Terraform configurations in the infra/ directory across all environments

**Overview**: Establishes comprehensive standards for Terraform infrastructure code that ensure
    consistency, maintainability, and cost-effectiveness across all deployment environments. Covers
    resource naming conventions, module organization, state management, security practices, and
    deployment patterns that support reliable infrastructure automation and collaborative development.

**Dependencies**: Terraform CLI, AWS provider, state management backend, deployment automation tools

**Exports**: Terraform coding standards, naming conventions, module patterns, deployment best practices

**Related**: INFRASTRUCTURE_PRINCIPLES.md, AWS deployment guides, state management documentation

**Implementation**: Terraform modules, naming conventions, validation rules, automated deployment patterns

---

## Standards Overview

These standards ensure consistent, maintainable, and cost-effective infrastructure as code across all environments and deployment scenarios.

## Core Principles

1. **Cost Optimization First**: Every resource must consider cost implications
2. **Consistent Naming**: All resources follow predictable naming patterns
3. **Product Domain Visibility**: Every resource tagged and named with product domain
4. **Environment Isolation**: Clear separation between dev, staging, and production
5. **Destroy/Recreate Friendly**: Infrastructure designed for easy teardown and recreation

## Naming Conventions

### Resource Names

All AWS resources must include the product domain in their name:

```hcl
# Pattern: {product-domain}-{environment}-{resource-type}-{specific-name}

# Examples:
resource "aws_s3_bucket" "main" {
  bucket = "durableai-${var.environment}-assets"
}

resource "aws_ecs_cluster" "main" {
  name = "durableai-${var.environment}-cluster"
}

resource "aws_lb" "main" {
  name = "durableai-${var.environment}-alb"
}
```

### Variable Names

- Use snake_case for variables: `enable_deletion_protection`
- Boolean variables start with verbs: `enable_`, `use_`, `create_`
- Group related variables with common prefixes

### Resource Labels in Terraform

- Use descriptive labels that indicate purpose
- Avoid generic names like `main` when multiple resources exist

```hcl
# Good
resource "aws_security_group" "alb_ingress" { ... }
resource "aws_security_group" "ecs_tasks" { ... }

# Avoid
resource "aws_security_group" "sg1" { ... }
resource "aws_security_group" "sg2" { ... }
```

## Tagging Strategy

### Required Tags for ALL Resources

Every resource MUST have these tags at minimum:

```hcl
tags = {
  # Product identification
  ProductDomain = "durableai"           # Fixed for all resources
  Product       = "durable-code-test"   # Project name

  # Environment and management
  Environment   = var.environment       # dev/staging/prod
  ManagedBy     = "terraform"          # IaC tool

  # Cost tracking
  CostCenter    = "engineering"        # For cost allocation

  # Lifecycle management
  CanDestroy    = var.environment == "dev" ? "true" : "false"
  AutoShutdown  = var.enable_auto_shutdown ? "true" : "false"
}
```

### Additional Recommended Tags

```hcl
tags = merge(
  local.common_tags,
  {
    # Component identification
    Component     = "backend"            # frontend/backend/database/etc
    Service       = "api"                # Specific service name

    # Operational
    Owner         = "platform-team"      # Team responsible
    Repository    = "github.com/be-wise-be-kind/durable-code-test"

    # Scheduling (for Lambda automation)
    Schedule      = "business-hours"     # For start/stop automation
    ScheduleOverride = "false"           # Manual override flag
  }
)
```

## File Organization

### Directory Structure

```
infra/
├── terraform/
│   ├── main.tf           # Provider and terraform configuration
│   ├── backend.tf        # Backend configuration (S3)
│   ├── variables.tf      # All variable definitions
│   ├── outputs.tf        # All outputs
│   ├── locals.tf         # Local values and computations
│   ├── data.tf           # Data sources
│   │
│   ├── network.tf        # VPC, subnets, IGW, NAT
│   ├── security.tf       # Security groups, NACLs
│   ├── compute.tf        # ECS, Fargate, EC2
│   ├── storage.tf        # S3, EFS, ECR
│   ├── database.tf       # RDS, DynamoDB
│   ├── loadbalancer.tf   # ALB, target groups
│   ├── dns.tf            # Route53 zones and records
│   ├── monitoring.tf     # CloudWatch, alarms
│   ├── iam.tf            # Roles and policies
│   └── automation.tf     # Lambda for start/stop scheduling
│
├── modules/             # Reusable modules
│   └── scheduled-infra/ # Module for scheduled infrastructure
│
├── environments/        # Environment-specific variables
│   ├── dev.tfvars
│   ├── staging.tfvars
│   └── prod.tfvars
│
└── scripts/            # Helper scripts
    ├── start-infra.sh  # Start infrastructure
    ├── stop-infra.sh   # Stop infrastructure
    └── cost-check.sh   # Check current costs
```

### File Headers

All Terraform files must include comprehensive headers:

```hcl
# Purpose: Define network infrastructure including VPC, subnets, and routing
# Scope: Network layer for all application components
# Overview: Creates a VPC with public and private subnets across availability zones,
#     internet gateway for public access, and NAT gateway for private subnet egress.
#     Designed for easy destruction and recreation with consistent CIDR blocks.
# Dependencies: AWS provider, variables from variables.tf
# Cost Impact: ~$45/month for NAT Gateway (can be destroyed when not in use)
```

## Resource-Specific Standards

### VPC and Networking

```hcl
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(
    local.common_tags,
    {
      Name          = "durableai-${var.environment}-vpc"
      ProductDomain = "durableai"
    }
  )
}
```

### ECS Resources

```hcl
resource "aws_ecs_cluster" "main" {
  name = "durableai-${var.environment}-cluster"

  setting {
    name  = "containerInsights"
    value = var.enable_container_insights ? "enabled" : "disabled"
  }

  tags = merge(
    local.common_tags,
    {
      ProductDomain = "durableai"
      Component     = "container-orchestration"
    }
  )
}
```

### S3 Buckets

```hcl
resource "aws_s3_bucket" "assets" {
  # Include account ID for global uniqueness
  bucket = "durableai-${var.environment}-assets-${data.aws_caller_identity.current.account_id}"

  tags = merge(
    local.common_tags,
    {
      ProductDomain = "durableai"
      Component     = "storage"
      DataClass     = "internal"  # internal/public/sensitive
    }
  )
}
```

## Scheduled Infrastructure Pattern

### Design Principles

1. **All non-production infrastructure should support scheduled start/stop**
2. **Resources must handle graceful shutdown and startup**
3. **State must persist across destroy/create cycles**

### Implementation

```hcl
# Lambda function for scheduled operations
resource "aws_lambda_function" "infra_scheduler" {
  filename      = "lambda_scheduler.zip"
  function_name = "durableai-${var.environment}-infra-scheduler"
  role          = aws_iam_role.lambda_scheduler.arn
  handler       = "scheduler.handler"
  runtime       = "python3.9"
  timeout       = 900  # 15 minutes for Terraform operations

  environment {
    variables = {
      ENVIRONMENT    = var.environment
      PRODUCT_DOMAIN = "durableai"
      TF_STATE_BUCKET = var.tf_state_bucket
      ACTION         = "apply"  # or "destroy"
    }
  }

  tags = merge(
    local.common_tags,
    {
      ProductDomain = "durableai"
      Component     = "automation"
      Purpose       = "cost-optimization"
    }
  )
}

# EventBridge rules for scheduling
resource "aws_cloudwatch_event_rule" "start_infra" {
  name                = "durableai-${var.environment}-start-infra"
  description         = "Start infrastructure at beginning of business day"
  schedule_expression = "cron(0 13 ? * MON-FRI *)"  # 8 AM EST (1 PM UTC)

  tags = merge(
    local.common_tags,
    {
      ProductDomain = "durableai"
      Action        = "start"
    }
  )
}

resource "aws_cloudwatch_event_rule" "stop_infra" {
  name                = "durableai-${var.environment}-stop-infra"
  description         = "Stop infrastructure at end of business day"
  schedule_expression = "cron(0 1 ? * MON-FRI *)"   # 8 PM EST (1 AM UTC)

  tags = merge(
    local.common_tags,
    {
      ProductDomain = "durableai"
      Action        = "stop"
    }
  )
}
```

## Cost Optimization Standards

### Resource Sizing

```hcl
# Use variables for all resource sizes
variable "ecs_task_cpu" {
  description = "CPU units for ECS tasks"
  type        = number
  default     = 256  # Minimum for dev, increase for prod
}

variable "ecs_task_memory" {
  description = "Memory in MB for ECS tasks"
  type        = number
  default     = 512  # Minimum for dev, increase for prod
}
```

### Conditional Resource Creation

```hcl
# Only create expensive resources when needed
resource "aws_nat_gateway" "main" {
  count = var.create_nat_gateway ? 1 : 0

  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[0].id

  tags = merge(
    local.common_tags,
    {
      ProductDomain = "durableai"
      CostImpact    = "high"  # Flag expensive resources
    }
  )
}
```

### Auto-Scaling Configuration

```hcl
resource "aws_appautoscaling_target" "ecs" {
  max_capacity       = var.environment == "prod" ? 10 : 2
  min_capacity       = var.environment == "dev" ? 0 : 1  # Allow scale to zero in dev
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.main.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}
```

## State Management

### Backend Configuration

```hcl
terraform {
  backend "s3" {
    bucket         = "durableai-terraform-state"
    key            = "infrastructure/terraform.tfstate"
    region         = "us-west-2"
    dynamodb_table = "durableai-terraform-locks"
    encrypt        = true
  }
}
```

### State Separation

- Use workspaces for environment separation
- Or use different state keys per environment:

```hcl
# backend-dev.conf
key = "dev/terraform.tfstate"

# backend-prod.conf
key = "prod/terraform.tfstate"
```

## Security Standards

### IAM Roles and Policies

```hcl
# Always use least privilege
resource "aws_iam_role_policy" "ecs_task" {
  name = "durableai-${var.environment}-ecs-task-policy"
  role = aws_iam_role.ecs_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject"
        ]
        Resource = "${aws_s3_bucket.assets.arn}/*"
      }
    ]
  })
}
```

### Security Groups

```hcl
resource "aws_security_group" "alb" {
  name_prefix = "durableai-${var.environment}-alb-"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "HTTPS from anywhere"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(
    local.common_tags,
    {
      ProductDomain = "durableai"
      Component     = "security"
    }
  )
}
```

## Outputs

### Naming Convention

```hcl
# Pattern: {component}_{attribute}
output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = aws_lb.main.dns_name
}

output "ecs_cluster_id" {
  description = "ID of the ECS cluster"
  value       = aws_ecs_cluster.main.id
}
```

## Validation and Testing

### Variable Validation

```hcl
variable "environment" {
  description = "Environment name"
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}
```

### Pre-commit Hooks

```yaml
- repo: https://github.com/antonbabenko/pre-commit-terraform
  hooks:
    - id: terraform_fmt
    - id: terraform_validate
    - id: terraform_tflint
```

## Common Patterns

### Local Values for Repeated Configuration

```hcl
locals {
  common_tags = {
    ProductDomain = "durableai"
    Product       = var.project_name
    Environment   = var.environment
    ManagedBy     = "terraform"
    CostCenter    = "engineering"
    Repository    = "github.com/be-wise-be-kind/durable-code-test"
  }

  name_prefix = "durableai-${var.environment}"

  # Computed values
  enable_production_resources = var.environment == "prod"
  enable_cost_optimization   = var.environment != "prod"
}
```

### Data Sources for Dynamic Values

```hcl
data "aws_caller_identity" "current" {}

data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_ami" "amazon_linux_2" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }
}
```

## Documentation Requirements

### README for Infrastructure

Each environment should have documentation:

```markdown
# Development Infrastructure

## Quick Start
```bash
# Start infrastructure (costs begin)
./scripts/start-infra.sh

# Stop infrastructure (costs stop)
./scripts/stop-infra.sh

# Check current costs
./scripts/cost-check.sh
```

## Resources Created
- VPC with 2 public and 2 private subnets
- ECS Cluster with Fargate
- Application Load Balancer
- RDS PostgreSQL (t3.micro)

## Estimated Costs
- Running 24/7: $150/month
- Business hours only (50 hrs/week): $45/month
- Destroyed when not in use: $0/month
```

## Compliance and Governance

### Cost Alerts

All environments must have cost alerts:

```hcl
resource "aws_budgets_budget" "monthly" {
  name         = "durableai-${var.environment}-monthly-budget"
  budget_type  = "COST"
  limit_amount = var.budget_amount
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 80
    threshold_type            = "PERCENTAGE"
    notification_type         = "ACTUAL"
    subscriber_email_addresses = var.alert_emails
  }
}
```

### Terraform Version Constraints

```hcl
terraform {
  required_version = ">= 1.0, < 2.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}
```

## Migration Strategy

When adopting these standards for existing infrastructure:

1. Tag all existing resources with ProductDomain
2. Update resource names in next major change
3. Implement scheduled start/stop for dev first
4. Gradually adopt naming conventions

## Review Checklist

Before submitting Terraform code for review:

- [ ] All resources have ProductDomain tag
- [ ] Resource names include product domain where applicable
- [ ] Cost impact documented in comments
- [ ] Expensive resources have enable/disable flags
- [ ] File has proper header documentation
- [ ] Variables have descriptions and types
- [ ] Outputs have descriptions
- [ ] README updated with cost estimates
- [ ] Scheduled start/stop supported for dev/staging
