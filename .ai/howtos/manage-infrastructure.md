# How to Manage Infrastructure

**Purpose**: Provide step-by-step instructions for managing AWS infrastructure using Docker-based Terraform Just targets
**Scope**: Infrastructure deployment, state management, cost control, and troubleshooting procedures

---

## Prerequisites

Before starting, ensure you have:

1. **Docker installed and running**
   ```bash
   docker --version
   docker ps  # Should not error
   ```

2. **AWS credentials configured**
   ```bash
   # Create ~/.aws/credentials if it doesn't exist
   mkdir -p ~/.aws
   cat > ~/.aws/credentials << EOF
   [default]
   aws_access_key_id = YOUR_ACCESS_KEY
   aws_secret_access_key = YOUR_SECRET_KEY

   [production]
   aws_access_key_id = PROD_ACCESS_KEY
   aws_secret_access_key = PROD_SECRET_KEY
   EOF
   ```

3. **AWS account with appropriate permissions**
   - S3 access for state storage
   - DynamoDB access for state locking
   - IAM, EC2, ECS, Route53 permissions for resources

## First-Time Setup

### Step 1: Verify AWS Credentials

```bash
# Check default profile
just infra-check-aws

# Check specific profile
AWS_PROFILE=production just infra-check-aws
```

Expected output:
```
✓ AWS credentials are valid!
-----------------------------------------------
|            GetCallerIdentity                |
+--------------+------------------------------+
| UserId       | AIDAI23456789EXAMPLE        |
| Account      | 123456789012                 |
| Arn          | arn:aws:iam::123456789012:...|
+--------------+------------------------------+
```

### Step 2: Set Up Terraform Backend

Create S3 bucket and DynamoDB table for state management:

```bash
just infra-backend-setup
```

This creates:
- S3 bucket: `durable-code-terraform-state`
- DynamoDB table: `durable-code-terraform-locks`

### Step 3: Initialize Terraform

```bash
just infra-init
```

Note: This happens automatically on first use of any command, but can be run explicitly.

## Daily Workflow

### Planning Changes

Always preview changes before applying:

```bash
# See what will change
just infra-plan

# With specific profile
AWS_PROFILE=staging just infra-plan
```

### Applying Changes

```bash
# Interactive - will ask for confirmation
just infra-up

# Non-interactive - for CI/CD
AUTO=true just infra-up

# With specific profile
AWS_PROFILE=production just infra-up
```

### Checking Current State

```bash
# List all resources
just infra-state-list

# Show specific resource
RESOURCE=aws_instance.web just infra-state-show

# Show outputs
just infra-output

# Show outputs as JSON (for scripts)
FORMAT=json just infra-output
```

## Environment Management

### Using Different Environments

```bash
# Development
AWS_PROFILE=dev just infra-plan

# Staging
AWS_PROFILE=staging just infra-plan

# Production
AWS_PROFILE=production just infra-plan
```

### Using Workspaces

```bash
# List workspaces
just infra-workspace-list

# Create new workspace
WORKSPACE=staging just infra-workspace-new

# Switch workspace
WORKSPACE=production just infra-workspace-select

# Apply in current workspace
just infra-up
```

## Cost Management

### Destroy Infrastructure When Not Needed

```bash
# Interactive destroy
just infra-down

# Non-interactive (careful!)
AUTO=true just infra-down
```

### Check Costs Before Applying

```bash
# Requires Infracost API key
INFRACOST_API_KEY=your_key just infra-cost
```

## Maintenance Tasks

### Format Terraform Code

```bash
# Auto-format all .tf files
just infra-fmt

# Validate configuration
just infra-validate

# Both format and validate
just infra-check
```

### Refresh State

Sync state with actual infrastructure:

```bash
just infra-refresh
```

### Import Existing Resources

```bash
# Import an existing AWS resource
RESOURCE=aws_instance.web ID=i-1234567890 just infra-import
```

## Troubleshooting

### Backend Configuration Changed

If you see "Backend initialization required":

```bash
# Option 1: Reinitialize (keeps state)
just infra-reinit

# Option 2: Clean everything and start fresh
just infra-clean-cache
just infra-init
```

### AWS Credentials Not Working

```bash
# Check which profile is being used
just infra-check-aws

# Try a different profile
AWS_PROFILE=another-profile just infra-check-aws

# Check credentials file
cat ~/.aws/credentials
```

### State Lock Error

Someone else might be running Terraform:

```bash
# Check who has the lock
just infra-state-list

# Wait and retry
sleep 30
just infra-plan
```

### Docker Volume Issues

```bash
# Remove cached .terraform directory
just infra-clean-cache

# Reinitialize
just infra-init
```

## Advanced Usage

### Running Terraform Console

Test expressions and explore state:

```bash
just infra-console

# In console:
> var.environment
> aws_instance.web.public_ip
> exit
```

### Generate Infrastructure Graph

Visualize resource dependencies:

```bash
just infra-graph
# Creates infrastructure-graph.png
```

### Quick Deploy

Initialize and apply in one command:

```bash
just infra-up
```

### Using Environment Variables

```bash
# Set defaults
export AWS_PROFILE=staging
export AWS_REGION=eu-west-1

# Now commands use these defaults
just infra-plan
just infra-up
```

## CI/CD Integration

### GitHub Actions Example

```yaml
- name: Deploy Infrastructure
  run: |
    AWS_PROFILE=production AUTO=true just infra-up
```

### Jenkins Example

```groovy
sh 'AWS_PROFILE=production AUTO=true just infra-up'
```

## Best Practices

1. **Always plan before applying**
   ```bash
   just infra-plan
   # Review changes
   just infra-up
   ```

2. **Use workspaces for environments**
   ```bash
   WORKSPACE=staging just infra-workspace-select
   just infra-up
   ```

3. **Tag resources appropriately**
   - Environment tags
   - Cost center tags
   - Owner tags

4. **Destroy unused infrastructure**
   ```bash
   # Dev environment after work
   AWS_PROFILE=dev just infra-down
   ```

5. **Keep state secure**
   - Never commit state files
   - Use encrypted S3 backend
   - Enable versioning

## Common Patterns

### Morning Startup

```bash
# Check credentials
just infra-check-aws

# See current state
just infra-state-list

# Plan any pending changes
just infra-plan
```

### End of Day Cleanup

```bash
# Destroy dev environment to save costs
AWS_PROFILE=dev AUTO=true just infra-down
```

### Deploy New Feature

```bash
# Switch to feature branch
git checkout feature/new-service

# Plan changes
just infra-plan

# Apply if looks good
just infra-up

# Check outputs
just infra-output
```

### Emergency Rollback

```bash
# Quick destroy if something goes wrong
AUTO=true just infra-down

# Or revert to previous state
git checkout main
just infra-up
```

## Domain Registration

### Check Domain Availability

```bash
cd infra/scripts
./check-domain-availability.sh codewithai.dev
```

### Recommended Domains

**Top .dev domains (~$12-15/year):**
- `codewithai.dev`
- `buildwithai.dev`
- `durablecode.dev`
- `aicodecraft.dev`
- `devwithai.dev`

### Register Through Route53

```bash
# Check availability
aws route53domains check-domain-availability \
  --domain-name codewithai.dev

# Register via AWS Console
# Route53 > Registered domains > Register domain
```

## Security Notes

- Never commit AWS credentials
- Use IAM roles when possible
- Enable MFA on AWS accounts
- Rotate access keys regularly
- Use separate AWS accounts for prod/dev
- Enable CloudTrail for auditing