<!--
Purpose: Operational runbook for infrastructure cost optimization using workspace separation
Scope: Cost management procedures, automated scheduling, and manual optimization workflows
Overview: This runbook provides comprehensive cost optimization strategies leveraging the workspace-separated
    infrastructure architecture. It covers automated scheduling via GitHub Actions, manual optimization
    procedures, cost monitoring techniques, and emergency cost reduction measures. The guide includes
    specific cost breakdowns, savings calculations, and operational procedures for maximizing cost
    efficiency while maintaining service availability and development productivity.
Dependencies: Terraform workspaces, GitHub Actions, AWS cost monitoring, just targets
Exports: Cost optimization procedures, monitoring commands, emergency protocols
Environment: Applies to dev, staging, and production environments with different strategies
Implementation: Automated and manual cost optimization workflows
-->

# Infrastructure Cost Optimization Runbook

## Executive Summary

The workspace-separated infrastructure enables significant cost optimization by separating persistent (base) and ephemeral (runtime) resources. This runbook provides operational procedures for maximizing cost efficiency while maintaining development productivity.

## Cost Breakdown Analysis

### Monthly Cost Structure (24/7 Operation)

| Resource Category | Monthly Cost | Can Shutdown? | Shutdown Savings |
|------------------|--------------|---------------|------------------|
| **NAT Gateways (2)** | ~$32 | No* | N/A |
| **Application Load Balancer** | ~$22 | No* | N/A |
| **ECS Fargate (2 services)** | ~$45 | Yes | ~$45 |
| **ECR Repositories** | ~$1 | No | N/A |
| **Route53 Hosted Zone** | ~$0.50 | No | N/A |
| **CloudWatch Logs** | ~$5 | Yes | ~$5 |
| **Total Infrastructure** | **~$105.50** | | **~$50 (47%)** |

*Base resources preserved for quick restoration

### Cost Optimization Potential

| Strategy | Development | Staging | Production | Annual Savings |
|----------|-------------|---------|------------|----------------|
| **Nightly Runtime Shutdown** | 50% | 25% | 0% | ~$1,800 |
| **Weekend Full Shutdown** | 75% | 50% | 0% | ~$3,600 |
| **Extended Holiday Shutdown** | 90% | 75% | 0% | ~$5,400 |

## Automated Cost Optimization

### GitHub Actions Scheduling

The infrastructure includes automated workflows for cost optimization:

#### Nightly Runtime Teardown
- **Schedule**: 8 PM PST (weekdays only)
- **Action**: `just infra-down SCOPE=runtime ENV=dev`
- **Savings**: ~$1.50/day (~$30/month)
- **Restoration**: Automatic at 8 AM PST

#### Weekend Extended Shutdown
- **Schedule**: Friday 8 PM PST
- **Action**: `just infra-down SCOPE=all ENV=dev` (with confirmation)
- **Savings**: ~$3.50/day (~$7/weekend)
- **Restoration**: Monday 8 AM PST

#### Automation Commands
```bash
# Check automation status
gh workflow list --repo your-org/durable-code-test

# View recent automation runs
gh run list --workflow=nightly-teardown

# Manual trigger automation
gh workflow run nightly-teardown --field environment=dev
gh workflow run morning-startup --field environment=dev
```

## Manual Cost Optimization Procedures

### Daily Optimization Workflow

#### End-of-Day Shutdown (Manual)
```bash
# Step 1: Verify no active development
echo "Checking for active sessions..."
just infra-status ENV=dev

# Step 2: Safe runtime shutdown
echo "Shutting down runtime infrastructure..."
just infra-down SCOPE=runtime ENV=dev

# Step 3: Verify shutdown success
echo "Verifying shutdown..."
just infra-status ENV=dev
# Should show: Base=UP, Runtime=DOWN
```

#### Start-of-Day Restoration (Manual)
```bash
# Step 1: Restore runtime infrastructure
echo "Restoring runtime infrastructure..."
just infra-up SCOPE=runtime ENV=dev

# Step 2: Deploy latest application version
echo "Deploying application..."
just deploy ENV=dev

# Step 3: Verify service health
echo "Verifying deployment..."
just infra-status ENV=dev
curl -f http://your-app-url/health || echo "Application not ready yet"
```

### Weekly Optimization Workflow

#### Extended Weekend Shutdown
```bash
# Friday evening (after 5 PM)
echo "=== Weekend Shutdown Procedure ==="

# Step 1: Notify team
echo "📢 NOTICE: Starting weekend infrastructure shutdown"

# Step 2: Destroy all infrastructure
echo "Destroying all infrastructure..."
CONFIRM=destroy-base just infra-down SCOPE=all ENV=dev

# Step 3: Verify complete shutdown
just infra-status ENV=dev
# Should show: Base=DOWN, Runtime=DOWN

echo "✅ Weekend shutdown complete. Savings: ~$7"
```

#### Monday Morning Restoration
```bash
# Monday morning (before 9 AM)
echo "=== Weekend Restoration Procedure ==="

# Step 1: Restore all infrastructure
echo "Restoring complete infrastructure..."
just infra-up SCOPE=all ENV=dev

# Step 2: Deploy application
echo "Deploying application..."
just deploy ENV=dev

# Step 3: Verify full service
echo "Verifying complete restoration..."
just infra-status ENV=dev
curl -f http://your-app-url/health

echo "✅ Weekend restoration complete. Service ready."
```

## Emergency Cost Reduction

### Immediate Cost Reduction (Emergency)
```bash
# EMERGENCY: Immediate shutdown of all non-production environments
echo "🚨 EMERGENCY COST REDUCTION PROTOCOL"

# Shutdown development
CONFIRM=destroy-base just infra-down SCOPE=all ENV=dev

# Shutdown staging (if safe)
CONFIRM=destroy-base just infra-down SCOPE=all ENV=staging

# Production: Runtime only (if absolutely necessary)
# just infra-down SCOPE=runtime ENV=prod  # ⚠️ USE WITH EXTREME CAUTION

echo "✅ Emergency shutdown complete"
```

### Gradual Cost Reduction
```bash
# Step 1: Runtime only shutdown (preserves quick restoration)
just infra-down SCOPE=runtime ENV=dev
just infra-down SCOPE=runtime ENV=staging

# Step 2: If more savings needed, full shutdown
CONFIRM=destroy-base just infra-down SCOPE=all ENV=dev
CONFIRM=destroy-base just infra-down SCOPE=all ENV=staging

# Step 3: Monitor cost impact
echo "Monitor AWS Cost Explorer for 24-48 hours"
```

## Cost Monitoring Procedures

### Daily Cost Monitoring
```bash
# Check infrastructure status
just infra-status ENV=dev
just infra-status ENV=staging
just infra-status ENV=prod

# Verify automation working
gh run list --workflow=nightly-teardown --limit=5

# Quick cost estimate
echo "Expected daily costs:"
echo "- Dev (runtime down): ~$1.50/day"
echo "- Staging (runtime up): ~$3.50/day"
echo "- Prod (always up): ~$3.50/day"
```

### Weekly Cost Review
```bash
# Generate cost report (requires AWS CLI with Cost Explorer access)
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-08 \
  --granularity DAILY \
  --metrics BlendedCost \
  --group-by Type=DIMENSION,Key=SERVICE

# Manual verification via AWS Console
echo "📊 Review AWS Cost Explorer: https://console.aws.amazon.com/cost-reports/"
```

### Monthly Cost Analysis
```bash
# Infrastructure cost summary
echo "=== Monthly Infrastructure Cost Analysis ==="
echo "Target costs with optimization:"
echo "- Development: ~$15/month (75% savings)"
echo "- Staging: ~$50/month (50% savings)"
echo "- Production: ~$105/month (0% savings)"
echo "- Total Target: ~$170/month vs ~$315 without optimization"
echo "- Monthly Savings: ~$145 (46%)"
```

## Cost Optimization Strategies by Environment

### Development Environment
```bash
# Aggressive optimization strategy
# - Nightly shutdown: 8 PM - 8 AM (12 hours down)
# - Weekend shutdown: Friday 8 PM - Monday 8 AM (60 hours down)
# - Holiday shutdown: Complete teardown during holidays

# Commands for dev optimization
just infra-down SCOPE=runtime ENV=dev     # Nightly
CONFIRM=destroy-base just infra-down SCOPE=all ENV=dev  # Weekend/Holiday
```

### Staging Environment
```bash
# Moderate optimization strategy
# - Selective shutdown: Non-business hours
# - Preserve during active testing periods
# - Weekend runtime shutdown only

# Commands for staging optimization
just infra-down SCOPE=runtime ENV=staging  # Off-hours only
# Keep base infrastructure always up for quick testing
```

### Production Environment
```bash
# Minimal optimization strategy
# - No automated shutdowns
# - Manual optimization only during planned maintenance
# - Focus on right-sizing rather than shutdown

# Production cost optimization (rare)
# just infra-down SCOPE=runtime ENV=prod  # ONLY during planned maintenance
```

## Automation Configuration

### GitHub Actions Secrets Required
```bash
# Required secrets for automation
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-west-2

# Verify secrets configured
gh secret list --repo your-org/durable-code-test
```

### Automation Schedule Override
```bash
# Disable automation temporarily
gh workflow disable nightly-teardown
gh workflow disable morning-startup

# Re-enable automation
gh workflow enable nightly-teardown
gh workflow enable morning-startup

# Manual override during automation downtime
# Run manual procedures from sections above
```

## Cost Optimization Best Practices

### Operational Practices
1. **Monitor daily costs** through AWS Cost Explorer
2. **Verify automation success** each morning
3. **Communicate shutdowns** to development team
4. **Plan around holidays** for extended savings
5. **Right-size resources** based on actual usage

### Safety Practices
1. **Never shutdown production** without explicit planning
2. **Test restoration procedures** regularly
3. **Backup critical data** before major shutdowns
4. **Maintain emergency contact lists** for off-hours issues
5. **Document cost optimization schedules** for team awareness

### Financial Practices
1. **Track cost savings** monthly
2. **Report optimization metrics** to stakeholders
3. **Budget for infrastructure costs** with optimization assumptions
4. **Review cost alerts** and thresholds regularly
5. **Plan capacity** based on optimized costs

## Troubleshooting Cost Issues

### High Unexpected Costs
```bash
# Check if automation failed
gh run list --workflow=nightly-teardown --status=failure

# Verify infrastructure status
just infra-status ENV=dev
just infra-status ENV=staging

# Emergency shutdown if needed
just infra-down SCOPE=runtime ENV=dev
just infra-down SCOPE=runtime ENV=staging
```

### Automation Failures
```bash
# Check automation logs
gh run view --log [run-id]

# Manual recovery
just infra-down SCOPE=runtime ENV=dev  # If shutdown failed
just infra-up SCOPE=runtime ENV=dev    # If startup failed

# Verify AWS credentials
aws sts get-caller-identity
```

### Cost Optimization Not Working
```bash
# Verify workspace separation working
just infra-status ENV=dev

# Check AWS resource tags
aws ec2 describe-instances --filters "Name=tag:Environment,Values=dev"
aws ecs list-clusters --query 'clusterArns[?contains(@, `dev`)]'

# Validate cost allocation
aws ce get-cost-and-usage --time-period Start=2024-01-01,End=2024-01-02 --granularity DAILY --metrics BlendedCost --group-by Type=DIMENSION,Key=SERVICE
```

## Emergency Contacts and Escalation

### Cost Emergency Response
1. **Immediate Action**: Execute emergency cost reduction procedures
2. **Notification**: Alert team via communication channels
3. **Monitoring**: Watch AWS Cost Explorer for 24-48 hours
4. **Review**: Conduct post-incident review of cost spike

### Escalation Procedures
- **Level 1**: Development team (cost optimization procedures)
- **Level 2**: DevOps team (infrastructure investigation)
- **Level 3**: Management (budget variance reporting)
- **Level 4**: Finance team (cost containment measures)

---

**Cost Optimization Target**: 40-60% infrastructure cost reduction through intelligent workspace separation and automated scheduling.