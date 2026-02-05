# CI/CD Pipeline Setup

**Purpose**: Comprehensive guide for GitHub Actions CI/CD pipeline setup for automated building and deployment to AWS ECS

**Scope**: GitHub Actions workflows, OIDC authentication, AWS infrastructure integration, and deployment procedures

**Overview**: This document provides complete instructions for implementing a secure CI/CD pipeline using GitHub Actions with AWS OIDC authentication for passwordless deployment to ECS. It covers the entire deployment workflow from code push to production deployment, including infrastructure prerequisites, secret configuration, workflow triggers, and monitoring procedures. The pipeline supports multiple environments (dev, staging, prod) with environment-specific deployment strategies. Key features include Docker image building, ECR registry management, ECS service updates, and automated rollback capabilities. The configuration eliminates long-lived AWS credentials by using OpenID Connect for secure, temporary authentication.

**Dependencies**: AWS infrastructure (OIDC provider, IAM roles, ECR repositories, ECS cluster), GitHub repository with Actions enabled, and properly configured AWS credentials

**Exports**: GitHub Actions workflows, deployment procedures, monitoring commands, and troubleshooting guides

**Related**: Links to AWS ECS documentation, GitHub Actions documentation, and infrastructure Terraform configurations

**Implementation**: Uses GitHub Actions with AWS OIDC for secure authentication, multi-stage workflows for build and deploy, and comprehensive error handling and rollback procedures

---

## Overview

The CI/CD pipeline uses GitHub Actions with AWS OIDC (OpenID Connect) for secure, passwordless authentication. This eliminates the need for long-lived AWS credentials in GitHub secrets.

## Architecture

```
GitHub Actions → OIDC Provider → AWS IAM Role → ECR/ECS
```

### Components

1. **GitHub OIDC Provider**: Configured in AWS to trust GitHub Actions
2. **IAM Role**: `durable-code-dev-github-actions` with permissions for ECR and ECS
3. **Workflows**:
   - `up.yml`: Brings infrastructure up (scheduled daily at 3 AM UTC / 8 PM MST, or manual)
   - `down.yml`: Tears infrastructure down (scheduled daily at 8 AM UTC / midnight PST, or manual)
   - `deploy.yml`: Builds Docker images and deploys to ECS (triggered after up, or manual)
   - `terraform-test.yml`: Validates Terraform configs, scripts, and just targets on PRs

### Daily Up/Down Cycle

```
8 PM MST (3 AM UTC)  → up.yml   → Terraform apply + app deploy
Midnight PST (8 AM UTC) → down.yml → Terraform destroy (runtime)
```

This cycle saves ~$63/month by tearing down expensive runtime resources (NAT Gateway, ALB, ECS) outside business hours while preserving persistent base infrastructure (VPC, ECR, certificates).

## Prerequisites

### AWS Infrastructure (Already Deployed)
- OIDC Provider: Configured for GitHub Actions
- IAM Role: `durable-code-dev-github-actions`
- ECR Repositories: `durableai-dev-frontend` and `durableai-dev-backend`
- ECS Cluster: `durable-code-dev-cluster`
- ECS Services: `durable-code-dev-frontend` and `durable-code-dev-backend`

### GitHub Secrets Required

You need to configure the following secrets in your GitHub repository:

```bash
# Required secret - IAM Role ARN for OIDC authentication
AWS_ROLE_ARN=<your-iam-role-arn>  # Get this from terraform output: github_actions_role_arn

# Optional - API URL for frontend builds
API_URL=https://api.dev.durableaicoding.net
```

## Setting Up GitHub Secrets

### Option 1: Using GitHub CLI

```bash
# Set the AWS Role ARN (required)
# First, get the role ARN from Terraform output:
terraform output github_actions_role_arn

# Then set it as a secret:
gh secret set AWS_ROLE_ARN --body "<your-role-arn>"

# Set the API URL (optional)
gh secret set API_URL --body "https://api.dev.durableaicoding.net"
```

### Option 2: Using GitHub Web UI

1. Go to your repository on GitHub
2. Navigate to Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Add the following secrets:
   - Name: `AWS_ROLE_ARN`
   - Value: Get from `terraform output github_actions_role_arn`

## Workflows

### Infrastructure Up (`up.yml`)

**Trigger**:
- Scheduled daily at 3 AM UTC (8 PM MST)
- Manual dispatch with environment, scope, deploy-app, and dry-run options

**Actions**:
1. Sets up Just and Terraform
2. Authenticates with AWS using OIDC
3. Initializes and applies Terraform (base and/or runtime)
4. Waits for ALB readiness
5. Optionally deploys the application
6. Verifies health

### Infrastructure Down (`down.yml`)

**Trigger**:
- Scheduled daily at 8 AM UTC (midnight PST)
- Manual dispatch with environment, scope, and dry-run options

**Actions**:
1. Authenticates with AWS using OIDC
2. Checks infrastructure status
3. Destroys runtime (and optionally base) resources
4. Reports cost savings (~$2.10/day for runtime)

### Application Deploy (`deploy.yml`)

**Trigger**:
- After Infrastructure Up workflow completes
- Manual dispatch with environment selection

**Actions**:
1. Authenticates with AWS using OIDC
2. Builds and pushes Docker images to ECR
3. Updates ECS task definitions with new images
4. Deploys frontend and backend services
5. Waits for service stability (10 min timeout)
6. Verifies deployment success

### Terraform Tests (`terraform-test.yml`)

**Trigger**:
- PRs/pushes affecting `infra/**`, `justfile`, or the workflow itself

**Jobs**:
1. `validate-terraform`: Format check, init, validate, tfsec scan (matrix: base, runtime)
2. `validate-scripts`: ShellCheck and bash syntax checking
3. `test-just-targets`: Just target syntax and subcommand validation
4. `integration-test`: Complete workflow dry run

## Usage

### Manual Deployment

1. Go to Actions tab in GitHub
2. Select "Deploy Application" workflow
3. Click "Run workflow"
4. Select environment (dev/staging/prod)
5. Click "Run workflow" button

### Automatic Deployment

The `up.yml` workflow runs nightly at 8 PM MST, bringing infrastructure up and deploying the application automatically.

## Monitoring Deployments

### GitHub Actions UI
- View real-time logs in the Actions tab
- Check deployment status and history

### AWS Console
- ECS Console: View service status and task health
- CloudWatch Logs: View application logs

### CLI Commands

```bash
# Check ECS service status
aws ecs describe-services \
  --cluster durableai-dev-cluster \
  --services durable-code-dev-frontend durable-code-dev-backend \
  --query "services[*].{Service:serviceName,Status:status,Running:runningCount,Desired:desiredCount}"

# View recent deployments
aws ecs describe-services \
  --cluster durableai-dev-cluster \
  --services durable-code-dev-frontend \
  --query "services[0].deployments"

# Get application URLs
terraform output application_urls
```

## Rollback Procedure

If a deployment fails or causes issues:

1. **Quick Rollback**:
   ```bash
   # Update service to use previous task definition
   aws ecs update-service \
     --cluster durableai-dev-cluster \
     --service durable-code-dev-frontend \
     --task-definition durable-code-dev-frontend:PREVIOUS_VERSION
   ```

2. **GitHub Revert**:
   - Create a revert PR for the problematic commit
   - Merge to trigger new deployment with reverted code

## Troubleshooting

### Common Issues

1. **OIDC Authentication Fails**
   - Verify `AWS_ROLE_ARN` secret is set correctly
   - Check IAM role trust relationship includes your repository

2. **ECR Push Fails**
   - Verify IAM role has ECR permissions
   - Check ECR repository exists

3. **ECS Deployment Fails**
   - Check task definition is valid
   - Verify container health checks
   - Review CloudWatch logs for application errors

### Debug Commands

```bash
# Test OIDC authentication locally
ROLE_ARN=$(terraform output -raw github_actions_role_arn)
aws sts assume-role-with-web-identity \
  --role-arn $ROLE_ARN \
  --role-session-name test-session \
  --web-identity-token $GITHUB_TOKEN

# Check ECR repository policy
aws ecr get-repository-policy \
  --repository-name durableai-dev-frontend

# View ECS task definition
aws ecs describe-task-definition \
  --task-definition durable-code-dev-frontend
```

## Security Best Practices

1. **No Long-Lived Credentials**: Uses OIDC for temporary credentials
2. **Least Privilege**: IAM role has minimal required permissions
3. **Branch Protection**: Restrict deployments to protected branches
4. **Manual Approval**: Add environment protection rules for production

## Cost Optimization

- **Multi-architecture builds**: Supports both x86 and ARM for cost-effective Fargate Spot
- **Caching**: Uses GitHub Actions cache to speed up builds
- **Conditional pushes**: Only pushes images on non-PR builds
- **Daily up/down cycle**: Saves ~$63/month by destroying runtime resources outside business hours

## Support

For issues or questions:
- Check GitHub Actions logs
- Review AWS CloudWatch logs
- Consult the AWS ECS documentation
- See [Operations documentation](../docs/terraform-operations.html) for just commands and workflow details
