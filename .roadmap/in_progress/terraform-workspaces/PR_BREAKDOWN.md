# Terraform Workspaces Implementation - PR Breakdown

## PR1: Terraform Workspace Foundation

### Branch: `feat/terraform-workspaces-pr1-foundation`

### Files to Create/Modify:
1. `infra/terraform/workspaces/README.md`
2. `infra/terraform/backend-config/base-dev.hcl`
3. `infra/terraform/backend-config/runtime-dev.hcl`
4. `infra/scripts/workspace-init.sh`
5. `infra/terraform/.gitignore` (update)

### Implementation Steps:

#### 1. Create workspace directory structure
```bash
mkdir -p infra/terraform/workspaces/{base,runtime}
mkdir -p infra/terraform/backend-config
mkdir -p infra/terraform/modules
mkdir -p infra/terraform/shared
```

#### 2. Create backend configurations for workspaces
```hcl
# infra/terraform/backend-config/base-dev.hcl
bucket         = "durable-code-terraform-state"
key            = "base/dev/terraform.tfstate"
region         = "us-west-2"
encrypt        = true
dynamodb_table = "terraform-state-lock"

# infra/terraform/backend-config/runtime-dev.hcl
bucket         = "durable-code-terraform-state"
key            = "runtime/dev/terraform.tfstate"
region         = "us-west-2"
encrypt        = true
dynamodb_table = "terraform-state-lock"
```

#### 3. Create workspace initialization script
```bash
#!/bin/bash
# infra/scripts/workspace-init.sh

WORKSPACE=$1
ENV=$2

if [[ -z "$WORKSPACE" || -z "$ENV" ]]; then
  echo "Usage: ./workspace-init.sh [base|runtime] [dev|staging|prod]"
  exit 1
fi

cd infra/terraform/workspaces/$WORKSPACE
terraform init -backend-config="../../backend-config/${WORKSPACE}-${ENV}.hcl"
terraform workspace new ${WORKSPACE}-${ENV} 2>/dev/null || terraform workspace select ${WORKSPACE}-${ENV}
```

#### 4. Update .gitignore
```
# Terraform workspaces
*.tfstate
*.tfstate.backup
.terraform/
infra/terraform/workspaces/*/.terraform/
infra/terraform/workspaces/*/terraform.tfstate*
```

### Testing:
```bash
# Initialize base workspace
./infra/scripts/workspace-init.sh base dev

# Initialize runtime workspace
./infra/scripts/workspace-init.sh runtime dev

# Verify workspaces created
terraform workspace list
```

---

## PR2: Base Infrastructure Workspace

### Branch: `feat/terraform-workspaces-pr2-base`

### Files to Create/Modify:
1. `infra/terraform/workspaces/base/main.tf`
2. `infra/terraform/workspaces/base/variables.tf`
3. `infra/terraform/workspaces/base/outputs.tf`
4. `infra/terraform/workspaces/base/providers.tf`
5. Move files: `networking.tf`, `ecr.tf`, `route53.tf`, `acm.tf`

### Implementation Steps:

#### 1. Create base workspace main configuration
```hcl
# infra/terraform/workspaces/base/main.tf

terraform {
  required_version = ">= 1.0"

  backend "s3" {
    # Configured via backend-config file
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

locals {
  workspace_name = terraform.workspace
  environment    = split("-", terraform.workspace)[1]

  common_tags = {
    Environment = local.environment
    Workspace   = local.workspace_name
    ManagedBy   = "Terraform"
    Scope       = "base"
  }
}
```

#### 2. Move base resources from existing files
```hcl
# Move these resources to base/main.tf:
# - aws_vpc
# - aws_subnet (public and private)
# - aws_internet_gateway
# - aws_nat_gateway
# - aws_eip
# - aws_route_table
# - aws_security_group (ALB and ECS)
# - aws_ecr_repository
# - aws_route53_zone
# - aws_acm_certificate
# - aws_lb (just the ALB itself, not targets/listeners)
```

#### 3. Create comprehensive outputs for runtime workspace
```hcl
# infra/terraform/workspaces/base/outputs.tf

output "vpc_id" {
  value       = aws_vpc.main.id
  description = "VPC ID for runtime resources"
}

output "public_subnet_ids" {
  value       = aws_subnet.public[*].id
  description = "Public subnet IDs for ALB"
}

output "private_subnet_ids" {
  value       = aws_subnet.private[*].id
  description = "Private subnet IDs for ECS tasks"
}

output "alb_security_group_id" {
  value       = aws_security_group.alb.id
  description = "ALB security group ID"
}

output "ecs_tasks_security_group_id" {
  value       = aws_security_group.ecs_tasks.id
  description = "ECS tasks security group ID"
}

output "backend_ecr_repository_url" {
  value       = aws_ecr_repository.backend.repository_url
  description = "Backend ECR repository URL"
}

output "frontend_ecr_repository_url" {
  value       = aws_ecr_repository.frontend.repository_url
  description = "Frontend ECR repository URL"
}

output "alb_arn" {
  value       = aws_lb.main.arn
  description = "ALB ARN for target group attachment"
}

output "alb_dns_name" {
  value       = aws_lb.main.dns_name
  description = "ALB DNS name"
}

output "route53_zone_id" {
  value       = aws_route53_zone.main.zone_id
  description = "Route53 zone ID"
}
```

### Testing:
```bash
# Deploy base infrastructure
cd infra/terraform/workspaces/base
terraform plan -var-file="../../environments/dev.tfvars"
terraform apply -var-file="../../environments/dev.tfvars"
```

---

## PR3: Runtime Infrastructure Workspace

### Branch: `feat/terraform-workspaces-pr3-runtime`

### Files to Create/Modify:
1. `infra/terraform/workspaces/runtime/main.tf`
2. `infra/terraform/workspaces/runtime/variables.tf`
3. `infra/terraform/workspaces/runtime/outputs.tf`
4. `infra/terraform/workspaces/runtime/providers.tf`
5. Move files: Parts of `ecs.tf`, `alb.tf`

### Implementation Steps:

#### 1. Create runtime workspace main configuration
```hcl
# infra/terraform/workspaces/runtime/main.tf

terraform {
  required_version = ">= 1.0"

  backend "s3" {
    # Configured via backend-config file
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

locals {
  workspace_name = terraform.workspace
  environment    = split("-", terraform.workspace)[1]

  common_tags = {
    Environment = local.environment
    Workspace   = local.workspace_name
    ManagedBy   = "Terraform"
    Scope       = "runtime"
  }
}
```

#### 2. Move runtime resources
```hcl
# Move these resources to runtime/main.tf:
# - aws_ecs_cluster
# - aws_ecs_task_definition
# - aws_ecs_service
# - aws_lb_target_group
# - aws_lb_listener
# - aws_lb_listener_rule
# - aws_service_discovery_*
# - aws_cloudwatch_log_group
# - aws_iam_role (ECS specific)
```

### Testing:
```bash
# Deploy runtime infrastructure
cd infra/terraform/workspaces/runtime
terraform plan -var-file="../../environments/dev.tfvars"
terraform apply -var-file="../../environments/dev.tfvars"

# Test destroy
terraform destroy -var-file="../../environments/dev.tfvars"
```

---

## PR4: Data Sources and Cross-Workspace References

### Branch: `feat/terraform-workspaces-pr4-data-sources`

### Files to Create/Modify:
1. `infra/terraform/workspaces/runtime/data.tf`
2. `infra/terraform/workspaces/runtime/main.tf` (update references)
3. `infra/terraform/modules/base-lookup/main.tf` (optional module)

### Implementation Steps:

#### 1. Create comprehensive data sources
```hcl
# infra/terraform/workspaces/runtime/data.tf

# VPC lookup
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

# Subnet lookups
data "aws_subnets" "public" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.main.id]
  }

  filter {
    name   = "tag:Type"
    values = ["public"]
  }
}

data "aws_subnets" "private" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.main.id]
  }

  filter {
    name   = "tag:Type"
    values = ["private"]
  }
}

# Security group lookups
data "aws_security_group" "alb" {
  filter {
    name   = "tag:Name"
    values = ["${var.project_name}-${local.environment}-alb-sg"]
  }

  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.main.id]
  }
}

data "aws_security_group" "ecs_tasks" {
  filter {
    name   = "tag:Name"
    values = ["${var.project_name}-${local.environment}-ecs-tasks-sg"]
  }

  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.main.id]
  }
}

# ECR repository lookups
data "aws_ecr_repository" "backend" {
  name = "${var.product_domain}-${local.environment}-backend"
}

data "aws_ecr_repository" "frontend" {
  name = "${var.product_domain}-${local.environment}-frontend"
}

# ALB lookup
data "aws_lb" "main" {
  name = "${var.project_name}-${local.environment}-alb"
}

# Route53 zone lookup
data "aws_route53_zone" "main" {
  name = var.domain_name
}
```

#### 2. Update all references in runtime resources
```hcl
# Example updates in runtime/main.tf

resource "aws_lb_target_group" "frontend" {
  vpc_id = data.aws_vpc.main.id  # Instead of aws_vpc.main[0].id
  # ...
}

resource "aws_ecs_service" "frontend" {
  network_configuration {
    subnets         = data.aws_subnets.private.ids
    security_groups = [data.aws_security_group.ecs_tasks.id]
  }
  # ...
}
```

### Testing:
```bash
# Verify data sources work
cd infra/terraform/workspaces/runtime
terraform plan -var-file="../../environments/dev.tfvars"

# Should show no errors about missing resources
```

---

## PR5: Makefile Integration and Commands

### Branch: `feat/terraform-workspaces-pr5-makefile`

### Files to Modify:
1. `Makefile.infra`
2. `infra/scripts/workspace-deploy.sh`
3. `infra/scripts/workspace-destroy.sh`
4. `infra/scripts/workspace-status.sh`
5. `infra/scripts/deploy-app.sh` (update for workspace model)

### Implementation Steps:

#### 1. Update Makefile.infra with parameter-driven workspace commands
```makefile
# Infrastructure management with SCOPE parameter
.PHONY: infra-up infra-down infra-status deploy

infra-up: ## Deploy infrastructure (SCOPE=base|runtime|all ENV=dev)
	@if [ -z "$(SCOPE)" ]; then \
		echo "$(RED)Error: SCOPE required (base|runtime|all)$(NC)"; \
		echo "Usage: make infra-up SCOPE=runtime ENV=dev"; \
		exit 1; \
	fi
	@./infra/scripts/workspace-deploy.sh $(ENV) $(SCOPE)

infra-down: ## Destroy infrastructure (SCOPE=runtime|all ENV=dev)
	@if [ -z "$(SCOPE)" ]; then \
		echo "$(RED)Error: SCOPE required (runtime|all)$(NC)"; \
		echo "Usage: make infra-down SCOPE=runtime ENV=dev"; \
		exit 1; \
	fi
	@if [ "$(SCOPE)" = "base" ] || [ "$(SCOPE)" = "all" ]; then \
		if [ "$(CONFIRM)" != "destroy-base" ]; then \
			echo "$(RED)Error: Base destruction requires CONFIRM=destroy-base$(NC)"; \
			exit 1; \
		fi; \
	fi
	@./infra/scripts/workspace-destroy.sh $(ENV) $(SCOPE)

infra-status: ## Show infrastructure status (ENV=dev)
	@./infra/scripts/workspace-status.sh $(ENV)

infra-check: ## Verify infrastructure is ready for deployment
	@./infra/scripts/check-infra-ready.sh $(ENV)

deploy: infra-check ## Deploy application to ECS (ENV=dev)
	@ENV=$(ENV) ./infra/scripts/deploy-app.sh
```

#### 2. Create unified workspace-deploy.sh script
```bash
#!/bin/bash
# infra/scripts/workspace-deploy.sh
# Handles deployment based on SCOPE parameter

ENV=$1
SCOPE=$2

if [[ -z "$ENV" || -z "$SCOPE" ]]; then
    echo "Usage: $0 <env> <scope>"
    echo "  env: dev|staging|prod"
    echo "  scope: base|runtime|all"
    exit 1
fi

case $SCOPE in
    base)
        echo "Deploying base infrastructure..."
        ./infra/scripts/workspace-deploy-base.sh $ENV
        ;;
    runtime)
        echo "Deploying runtime infrastructure..."
        ./infra/scripts/workspace-deploy-runtime.sh $ENV
        ;;
    all)
        echo "Deploying all infrastructure..."
        ./infra/scripts/workspace-deploy-base.sh $ENV
        if [ $? -eq 0 ]; then
            ./infra/scripts/workspace-deploy-runtime.sh $ENV
        fi
        ;;
    *)
        echo "Invalid SCOPE: $SCOPE (must be base|runtime|all)"
        exit 1
        ;;
esac
```

#### 3. Create unified workspace-destroy.sh script
```bash
#!/bin/bash
# infra/scripts/workspace-destroy.sh
# Handles destruction based on SCOPE parameter

ENV=$1
SCOPE=$2

if [[ -z "$ENV" || -z "$SCOPE" ]]; then
    echo "Usage: $0 <env> <scope>"
    echo "  env: dev|staging|prod"
    echo "  scope: runtime|all"
    exit 1
fi

case $SCOPE in
    runtime)
        echo "Destroying runtime infrastructure..."
        ./infra/scripts/workspace-destroy-runtime.sh $ENV
        ;;
    all)
        echo "Destroying all infrastructure..."
        ./infra/scripts/workspace-destroy-runtime.sh $ENV
        if [ $? -eq 0 ]; then
            ./infra/scripts/workspace-destroy-base.sh $ENV
        fi
        ;;
    base)
        echo "ERROR: Use SCOPE=all with CONFIRM=destroy-base to destroy base"
        exit 1
        ;;
    *)
        echo "Invalid SCOPE: $SCOPE (must be runtime|all)"
        exit 1
        ;;
esac
```

#### 4. Update deploy-app.sh for workspace model
```bash
# Key updates needed:
# - Use workspace outputs for resource names
# - Check if runtime workspace is deployed
# - Use consistent naming from workspace variables
```

### Testing:
```bash
# Test parameter-driven commands
make infra-up SCOPE=base ENV=dev
make infra-up SCOPE=runtime ENV=dev
make infra-status ENV=dev
make deploy ENV=dev

# Test teardown and restore
make infra-down SCOPE=runtime ENV=dev
make infra-status ENV=dev  # Should show base still exists
make infra-up SCOPE=runtime ENV=dev
make deploy ENV=dev

# Test all-in-one deployment
make infra-up SCOPE=all ENV=staging
```

---

## PR6: Documentation, Testing, and Scheduling

### Branch: `feat/terraform-workspaces-pr6-docs`

### Files to Create/Modify:
1. `.ai/howto/terraform-workspaces-operations.md`
2. `.ai/howto/infrastructure-deployment.md`
3. `.ai/runbooks/cost-optimization.md`
4. `.ai/troubleshooting/terraform-workspaces.md`
5. `.github/workflows/nightly-teardown.yml`
6. `.github/workflows/morning-startup.yml`
7. `.github/workflows/terraform-test.yml`

### Implementation Steps:

#### 1. Create GitHub Actions for scheduled operations
```yaml
# .github/workflows/nightly-teardown.yml
name: Nightly Infrastructure Teardown

on:
  schedule:
    - cron: '0 1 0 * * *'  # 8 PM PST
  workflow_dispatch:
    inputs:
      environment:
        description: 'Environment to teardown'
        required: true
        default: 'dev'
        type: choice
        options:
          - dev
          - staging

jobs:
  teardown:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v2

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-west-2

      - name: Teardown runtime infrastructure
        run: |
          make infra-down SCOPE=runtime ENV=${{ inputs.environment || 'dev' }}
```

```yaml
# .github/workflows/morning-startup.yml
name: Morning Infrastructure Startup

on:
  schedule:
    - cron: '0 15 * * 1-5'  # 8 AM PST, weekdays only
  workflow_dispatch:
    inputs:
      environment:
        description: 'Environment to startup'
        required: true
        default: 'dev'
        type: choice
        options:
          - dev
          - staging

jobs:
  startup:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v2

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-west-2

      - name: Startup runtime infrastructure
        run: |
          make infra-up SCOPE=runtime ENV=${{ inputs.environment || 'dev' }}

      - name: Deploy latest application
        run: |
          make deploy ENV=${{ inputs.environment || 'dev' }}
```

#### 2. Create comprehensive documentation in AI folder
```markdown
# .ai/howto/terraform-workspaces-operations.md

## Terraform Workspace Operations

### Overview
Infrastructure is split into base (persistent) and runtime (ephemeral) workspaces.

### Common Commands
- `make infra-up SCOPE=all ENV=dev` - Deploy everything
- `make infra-up SCOPE=runtime ENV=dev` - Deploy runtime only
- `make infra-down SCOPE=runtime ENV=dev` - Teardown runtime
- `make deploy ENV=dev` - Deploy application

### Cost Optimization
GitHub Actions automatically:
- Tears down runtime infrastructure at 8 PM PST (weekdays)
- Restores runtime infrastructure at 8 AM PST (weekdays)
- Preserves base infrastructure (VPC, NAT, ECR)

### Manual Override
Workflows can be triggered manually from GitHub Actions tab.
```

```markdown
# .ai/runbooks/cost-optimization.md

## Cost Optimization Runbook

### Automated Schedule
- **Teardown**: 8 PM PST daily (saves ~$15/day)
- **Startup**: 8 AM PST weekdays
- **Weekend**: Infrastructure remains down

### Manual Cost Savings
```bash
# Immediate teardown
make infra-down SCOPE=runtime ENV=dev

# Restore when needed
make infra-up SCOPE=runtime ENV=dev
make deploy ENV=dev
```

### Cost Breakdown
- Runtime (ECS Fargate): ~$0.60/day
- Base (NAT Gateway): ~$1.08/day (persistent)
- Total savings: ~60% with scheduled teardowns
```

```markdown
# .ai/troubleshooting/terraform-workspaces.md

## Troubleshooting Terraform Workspaces

### Runtime won't deploy
```bash
# Check base is deployed
make infra-status ENV=dev

# If missing, deploy base first
make infra-up SCOPE=base ENV=dev
```

### Application deployment fails
```bash
# Verify runtime is up
make infra-status ENV=dev

# If runtime is down, restore it
make infra-up SCOPE=runtime ENV=dev
```

### GitHub Actions failing
1. Check AWS credentials in GitHub Secrets
2. Verify IAM permissions
3. Check CloudWatch logs for Terraform errors
```

#### 3. Add CI/CD tests
```yaml
# .github/workflows/terraform-test.yml
name: Terraform Workspace Tests

on:
  pull_request:
    paths:
      - 'infra/terraform/**'
      - 'infra/scripts/**'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v2

      - name: Validate Base Workspace
        run: |
          cd infra/terraform/workspaces/base
          terraform init -backend=false
          terraform validate

      - name: Validate Runtime Workspace
        run: |
          cd infra/terraform/workspaces/runtime
          terraform init -backend=false
          terraform validate

      - name: Test Scripts
        run: |
          bash -n infra/scripts/workspace-*.sh
          bash -n infra/scripts/deploy-app.sh
```

### Testing:
```bash
# Test complete deployment flow
make infra-up SCOPE=all ENV=dev
make deploy ENV=dev
make infra-status ENV=dev

# Test cost optimization flow
make infra-down SCOPE=runtime ENV=dev
make infra-up SCOPE=runtime ENV=dev

# Verify GitHub Actions
gh workflow run nightly-teardown --field environment=dev
gh workflow run morning-startup --field environment=dev
```

---

## Success Criteria Checklist

After all PRs are complete, verify:

- [ ] Base and runtime in separate workspaces
- [ ] Each workspace has independent state
- [ ] Runtime references base via data sources
- [ ] `make infra-down SCOPE=runtime ENV=dev` works without errors
- [ ] `make infra-up SCOPE=runtime ENV=dev` restores service
- [ ] `make infra-up SCOPE=all ENV=dev` deploys everything
- [ ] `make deploy ENV=dev` deploys application successfully
- [ ] Base resources unchanged during runtime operations
- [ ] Parameter-driven Makefile commands (SCOPE, ENV)
- [ ] GitHub Actions for scheduled teardown/startup
- [ ] Documentation in .ai/ folder structure
- [ ] CI/CD pipeline validates workspaces
- [ ] Cost optimization (~60% savings) achieved

## Rollback Plan

If issues arise during implementation:

1. **Stop all changes immediately**
2. **Restore from backup**: `terraform state push backup.tfstate`
3. **Revert code changes**: `git revert HEAD~n`
4. **Verify infrastructure intact**: `terraform plan`
5. **Document lessons learned**
6. **Re-plan approach**

---
**Remember**: Each PR should be atomic and leave the infrastructure in a working state. Test thoroughly in dev before proceeding to the next PR.