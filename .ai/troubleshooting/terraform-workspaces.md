<!--
Purpose: Comprehensive troubleshooting guide for Terraform workspace infrastructure operations
Scope: Problem diagnosis, resolution procedures, and preventive measures for workspace-separated infrastructure
Overview: This guide provides systematic troubleshooting procedures for the workspace-separated infrastructure
    system. It covers common issues, error patterns, diagnostic commands, resolution steps, and preventive
    measures. The guide is organized by problem category with specific symptoms, root causes, and step-by-step
    solutions. It includes emergency recovery procedures, state management issues, cross-workspace dependency
    problems, and automation failures. Each section provides both immediate fixes and long-term prevention.
Dependencies: Terraform CLI, AWS CLI, just targets, workspace scripts, GitHub Actions access
Exports: Diagnostic procedures, resolution commands, recovery workflows
Environment: Covers dev, staging, and production troubleshooting scenarios
Implementation: Production-tested troubleshooting procedures with detailed command sequences
-->

# Terraform Workspaces Troubleshooting Guide

## Overview

This guide provides comprehensive troubleshooting procedures for the workspace-separated infrastructure system. Issues are organized by category with systematic diagnostic and resolution steps.

## Quick Diagnostic Commands

### Essential Status Checks
```bash
# Check infrastructure status
just infra-status ENV=dev

# Check Terraform state
just infra-state-list SCOPE=base ENV=dev
just infra-state-list SCOPE=runtime ENV=dev

# Check AWS resources directly
aws ec2 describe-vpcs --filters "Name=tag:Environment,Values=dev"
aws ecs list-clusters --query 'clusterArns[?contains(@, `dev`)]'

# Check workspace selection
cd infra/terraform/workspaces/base && terraform workspace show
cd infra/terraform/workspaces/runtime && terraform workspace show
```

### Emergency Recovery Commands
```bash
# Stop all operations
pkill -f terraform

# Unlock state (if locked)
terraform force-unlock <LOCK_ID> -force

# Refresh state
just infra-refresh SCOPE=base ENV=dev
just infra-refresh SCOPE=runtime ENV=dev

# Emergency shutdown
just infra-down SCOPE=runtime ENV=dev
```

## Problem Categories

## 1. Runtime Deployment Failures

### Symptom: "No matching VPC found"
```
Error: No matching VPC found
data.aws_vpc.main: Refreshing state...
```

**Root Cause**: Runtime workspace cannot find base infrastructure resources.

**Diagnostic Steps**:
```bash
# 1. Check if base infrastructure is deployed
just infra-status ENV=dev

# 2. Verify base workspace state
cd infra/terraform/workspaces/base
terraform workspace show
terraform state list

# 3. Check VPC tags
aws ec2 describe-vpcs --filters "Name=tag:Environment,Values=dev" "Name=tag:Scope,Values=base"
```

**Resolution**:
```bash
# If base infrastructure missing:
just infra-up SCOPE=base ENV=dev

# If base exists but tags are wrong, re-apply base:
cd infra/terraform/workspaces/base
terraform apply -var-file="../../environments/dev.tfvars"

# Then retry runtime deployment:
just infra-up SCOPE=runtime ENV=dev
```

### Symptom: "Resource already exists"
```
Error: ALB target group already exists
aws_lb_target_group.frontend: Error creating target group
```

**Root Cause**: Resources exist outside Terraform management or workspace isolation issues.

**Resolution**:
```bash
# 1. Check existing resources
aws elbv2 describe-target-groups --names "*dev*"

# 2. Import existing resource (if appropriate)
cd infra/terraform/workspaces/runtime
terraform import aws_lb_target_group.frontend arn:aws:elasticloadbalancing:...

# 3. Or manually delete conflicting resource
aws elbv2 delete-target-group --target-group-arn arn:aws:elasticloadbalancing:...

# 4. Retry deployment
just infra-up SCOPE=runtime ENV=dev
```

### Symptom: "ECS service startup timeout"
```
Error: timeout while waiting for ECS service to reach stable state
```

**Diagnostic Steps**:
```bash
# 1. Check ECS service status
aws ecs describe-services --cluster durableai-dev-cluster --services durableai-dev-frontend

# 2. Check task definition
aws ecs describe-task-definition --task-definition durableai-dev-frontend

# 3. Check running tasks
aws ecs list-tasks --cluster durableai-dev-cluster --service-name durableai-dev-frontend

# 4. Check task logs
aws logs tail /aws/ecs/durableai-dev-frontend
```

**Resolution**:
```bash
# 1. Check container image exists
aws ecr describe-images --repository-name durableai-dev-frontend

# 2. If image missing, build and push
just build-and-push ENV=dev

# 3. Force new deployment
aws ecs update-service --cluster durableai-dev-cluster --service durableai-dev-frontend --force-new-deployment

# 4. If still failing, check resource limits
aws ecs describe-tasks --cluster durableai-dev-cluster --tasks <task-arn>
```

## 2. State Management Issues

### Symptom: "State lock timeout"
```
Error: Error acquiring the state lock
Lock Info:
  ID:        12345678-1234-1234-1234-123456789012
  Path:      durableai-terraform-state/base/dev/terraform.tfstate
```

**Resolution**:
```bash
# 1. Wait for lock to release naturally (up to 20 minutes)
# 2. If urgent, force unlock (DANGEROUS in production)
cd infra/terraform/workspaces/base
terraform force-unlock 12345678-1234-1234-1234-123456789012 -force

# 3. Verify state integrity after unlock
terraform plan -var-file="../../environments/dev.tfvars"
```

### Symptom: "Backend configuration changed"
```
Error: Backend configuration changed
A previous run of Terraform initialized this directory with a backend that has different configuration
```

**Resolution**:
```bash
# 1. Backup current state
terraform state pull > terraform.tfstate.backup

# 2. Reconfigure backend
terraform init -reconfigure -backend-config="../../backend-config/base-dev.hcl"

# 3. Verify state is intact
terraform plan -var-file="../../environments/dev.tfvars"
```

### Symptom: "Resource drift detected"
```
Error: Resource drift detected
AWS resources have been modified outside of Terraform
```

**Diagnostic Steps**:
```bash
# 1. Generate detailed plan to see drift
just infra-plan SCOPE=base ENV=dev

# 2. Check AWS console for manual changes
# 3. Review CloudTrail for modification events
aws logs filter-log-events --log-group-name CloudTrail/DurableAI --filter-pattern "{ $.eventName = ModifyVpc || $.eventName = DeleteSubnet }"
```

**Resolution**:
```bash
# Option 1: Refresh state to import changes
just infra-refresh SCOPE=base ENV=dev

# Option 2: Apply to restore Terraform configuration
just infra-up SCOPE=base ENV=dev

# Option 3: Import manually modified resources
terraform import aws_vpc.main vpc-12345678
```

## 3. Cross-Workspace Dependency Issues

### Symptom: "Data source returns empty results"
```
Error: Invalid index
data.aws_subnets.private.ids[0] is out of range for empty tuple
```

**Root Cause**: Base resources not tagged correctly or don't exist.

**Diagnostic Steps**:
```bash
# 1. Check base resource tags
aws ec2 describe-subnets --filters "Name=tag:Environment,Values=dev" "Name=tag:Type,Values=private"

# 2. Verify base workspace outputs
cd infra/terraform/workspaces/base
terraform output

# 3. Test data source query manually
cd infra/terraform/workspaces/runtime
terraform console
> data.aws_subnets.private.ids
```

**Resolution**:
```bash
# 1. Re-apply base infrastructure with correct tags
just infra-up SCOPE=base ENV=dev

# 2. Verify tags are applied
aws ec2 describe-subnets --subnet-ids $(terraform output -raw private_subnet_ids)

# 3. Retry runtime deployment
just infra-up SCOPE=runtime ENV=dev
```

### Symptom: "Security group not found"
```
Error: InvalidGroup.NotFound
The security group 'sg-12345678' does not exist
```

**Resolution**:
```bash
# 1. Check security group exists in base workspace
cd infra/terraform/workspaces/base
terraform state show aws_security_group.ecs_tasks

# 2. Verify runtime data source
cd infra/terraform/workspaces/runtime
terraform plan -var-file="../../environments/dev.tfvars" | grep security_group

# 3. Re-apply base if security group missing
just infra-up SCOPE=base ENV=dev
```

## 4. GitHub Actions Automation Issues

### Symptom: "Nightly teardown failed"
```
Error: AWS authentication failed
Unable to locate credentials
```

**Diagnostic Steps**:
```bash
# 1. Check GitHub secrets
gh secret list --repo your-org/durable-code-test

# 2. Test credentials locally
aws sts get-caller-identity

# 3. Check workflow run logs
gh run list --workflow=nightly-teardown --limit=5
gh run view <run-id> --log
```

**Resolution**:
```bash
# 1. Update GitHub secrets if expired
gh secret set AWS_ACCESS_KEY_ID --body "your-new-key"
gh secret set AWS_SECRET_ACCESS_KEY --body "your-new-secret"

# 2. Manual teardown if automation fails
just infra-down SCOPE=runtime ENV=dev

# 3. Test automation manually
gh workflow run nightly-teardown --field environment=dev
```

### Symptom: "Morning startup timeout"
```
Error: Infrastructure readiness timeout after 10 minutes
```

**Resolution**:
```bash
# 1. Check infrastructure status
just infra-status ENV=dev

# 2. Manual startup with detailed logging
just infra-up SCOPE=runtime ENV=dev

# 3. Check for resource limits or capacity issues
aws ecs describe-services --cluster durableai-dev-cluster --services durableai-dev-frontend
aws ec2 describe-availability-zones --zone-names us-west-2a us-west-2b
```

## 5. Application Deployment Issues

### Symptom: "Application deployment fails after infrastructure restore"
```
Error: ECS service not found
Service 'durableai-dev-frontend' not found
```

**Root Cause**: Runtime infrastructure not fully restored before application deployment.

**Resolution**:
```bash
# 1. Ensure runtime infrastructure is complete
just infra-status ENV=dev

# 2. Wait for ECS services to be ready
just infra-check ENV=dev

# 3. Retry application deployment
just deploy ENV=dev

# 4. If still failing, force service recreation
just infra-up SCOPE=runtime ENV=dev
```

### Symptom: "Container image not found"
```
Error: Failed to pull image
repository does not exist or may require authentication
```

**Resolution**:
```bash
# 1. Check ECR repository exists
aws ecr describe-repositories --repository-names durableai-dev-frontend

# 2. Check image exists in repository
aws ecr describe-images --repository-name durableai-dev-frontend

# 3. If missing, build and push images
just build-and-push ENV=dev

# 4. Update ECS service
aws ecs update-service --cluster durableai-dev-cluster --service durableai-dev-frontend --force-new-deployment
```

## 6. Cost Optimization Issues

### Symptom: "Unexpected high AWS costs"
```
Cost Alert: AWS charges exceed expected baseline
```

**Diagnostic Steps**:
```bash
# 1. Check infrastructure status (should show some resources down)
just infra-status ENV=dev

# 2. Check for rogue resources
aws ec2 describe-instances --filters "Name=instance-state-name,Values=running"
aws ecs list-clusters
aws rds describe-db-instances

# 3. Check automation success
gh run list --workflow=nightly-teardown --status=success --limit=7
```

**Resolution**:
```bash
# 1. Emergency cost reduction
just infra-down SCOPE=runtime ENV=dev
just infra-down SCOPE=runtime ENV=staging

# 2. Check for manual resource creation
aws resourcegroupstaggingapi get-resources --tag-filters Key=Environment,Values=dev

# 3. If automation failed, fix and re-enable
gh workflow enable nightly-teardown
gh workflow run nightly-teardown --field environment=dev
```

## 7. Emergency Recovery Procedures

### Complete Infrastructure Recovery
```bash
echo "🚨 EMERGENCY RECOVERY PROCEDURE"

# Step 1: Stop all running operations
pkill -f terraform

# Step 2: Back up current state
mkdir -p /tmp/terraform-backup-$(date +%Y%m%d-%H%M%S)
cd infra/terraform/workspaces/base && terraform state pull > /tmp/terraform-backup-*/base-state.json
cd infra/terraform/workspaces/runtime && terraform state pull > /tmp/terraform-backup-*/runtime-state.json

# Step 3: Force unlock if needed
cd infra/terraform/workspaces/base && terraform force-unlock <ID> -force || true
cd infra/terraform/workspaces/runtime && terraform force-unlock <ID> -force || true

# Step 4: Refresh state
just infra-refresh SCOPE=base ENV=dev
just infra-refresh SCOPE=runtime ENV=dev

# Step 5: Plan to assess damage
just infra-plan SCOPE=base ENV=dev > /tmp/base-plan.txt
just infra-plan SCOPE=runtime ENV=dev > /tmp/runtime-plan.txt

# Step 6: Recovery decision point
echo "📋 Review plans in /tmp/*-plan.txt"
echo "Choose recovery option:"
echo "A) Apply plans to restore"
echo "B) Destroy and recreate"
echo "C) Manual intervention needed"
```

### State Corruption Recovery
```bash
echo "🔧 STATE CORRUPTION RECOVERY"

# Step 1: Attempt state refresh
terraform refresh -var-file="../../environments/dev.tfvars"

# Step 2: If refresh fails, pull remote state
terraform state pull > current-state.json

# Step 3: Check state file integrity
jq empty current-state.json || echo "❌ State file corrupted"

# Step 4: Restore from backup (if available)
terraform state push backup-state.json

# Step 5: Re-import critical resources
terraform import aws_vpc.main vpc-12345678
terraform import aws_lb.main arn:aws:elasticloadbalancing:...
```

## Prevention and Best Practices

### Monitoring Setup
```bash
# Set up monitoring for state health
*/30 * * * * just infra-status ENV=dev | grep -q "healthy" || echo "Infrastructure unhealthy" | mail admin@company.com

# Monitor automation success
gh run list --workflow=nightly-teardown --status=failure --created=">=2024-01-01" | wc -l
```

### Regular Health Checks
```bash
# Weekly infrastructure health check
just infra-plan SCOPE=base ENV=dev | grep -q "No changes" || echo "Base infrastructure drift detected"
just infra-plan SCOPE=runtime ENV=dev | grep -q "No changes" || echo "Runtime infrastructure drift detected"

# Monthly cost review
aws ce get-cost-and-usage --time-period Start=2024-01-01,End=2024-02-01 --granularity MONTHLY --metrics BlendedCost
```

### Backup Procedures
```bash
# Daily state backup
mkdir -p backups/$(date +%Y-%m-%d)
cd infra/terraform/workspaces/base && terraform state pull > ../../../backups/$(date +%Y-%m-%d)/base-state.json
cd infra/terraform/workspaces/runtime && terraform state pull > ../../../backups/$(date +%Y-%m-%d)/runtime-state.json
```

## Escalation Matrix

### Issue Severity Levels

**P0 - Production Down**
- Immediate action: Emergency recovery procedures
- Escalation: On-call engineer → DevOps lead → Management
- Communication: Incident channel, status page

**P1 - Development Blocked**
- Response time: 2 hours
- Escalation: Developer → DevOps team → Engineering lead
- Communication: Team channel

**P2 - Automation Failure**
- Response time: 24 hours
- Escalation: DevOps team → Engineering lead
- Communication: Engineering channel

**P3 - Cost Optimization Issues**
- Response time: 72 hours
- Escalation: DevOps team → Finance team
- Communication: Operations channel

### Contact Information
- **DevOps On-Call**: [Contact details]
- **Engineering Lead**: [Contact details]
- **AWS Account Owner**: [Contact details]
- **Emergency Escalation**: [Contact details]

## Common Command Reference

### Quick Fixes
```bash
# Fix most common issues
just infra-refresh SCOPE=runtime ENV=dev && just infra-up SCOPE=runtime ENV=dev

# Reset runtime workspace
just infra-down SCOPE=runtime ENV=dev && just infra-up SCOPE=runtime ENV=dev

# Emergency shutdown
just infra-down SCOPE=runtime ENV=dev

# Check everything
just infra-status ENV=dev && just infra-check ENV=dev
```

### State Management
```bash
# List resources
terraform state list

# Show resource details
terraform state show aws_vpc.main

# Remove resource from state
terraform state rm aws_instance.example

# Import existing resource
terraform import aws_instance.example i-1234567890abcdef0
```

### Debugging
```bash
# Verbose logging
export TF_LOG=DEBUG
just infra-plan SCOPE=runtime ENV=dev

# Check provider versions
terraform version
terraform providers

# Validate configuration
terraform validate
terraform fmt -check
```

---

**Remember**: When in doubt, check the infrastructure status first, then consult this guide for systematic troubleshooting steps. Always backup state before making major changes.