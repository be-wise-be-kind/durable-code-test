# How to Manage Infrastructure

**Purpose**: Provide step-by-step instructions for managing AWS infrastructure using Docker-based Terraform Make targets
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
make infra-check-aws

# Check specific profile
AWS_PROFILE=production make infra-check-aws
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
make infra-backend-setup
```

This creates:
- S3 bucket: `durable-code-terraform-state`
- DynamoDB table: `durable-code-terraform-locks`

### Step 3: Initialize Terraform

```bash
make infra-init
```

Note: This happens automatically on first use of any command, but can be run explicitly.

## Daily Workflow

### Planning Changes

Always preview changes before applying:

```bash
# See what will change
make infra-plan

# With specific profile
AWS_PROFILE=staging make infra-plan
```

### Applying Changes

```bash
# Interactive - will ask for confirmation
make infra-up

# Non-interactive - for CI/CD
AUTO=true make infra-up

# With specific profile
AWS_PROFILE=production make infra-up
```

### Checking Current State

```bash
# List all resources
make infra-state-list

# Show specific resource
RESOURCE=aws_instance.web make infra-state-show

# Show outputs
make infra-output

# Show outputs as JSON (for scripts)
FORMAT=json make infra-output
```

## Environment Management

### Using Different Environments

```bash
# Development
AWS_PROFILE=dev make infra-plan

# Staging
AWS_PROFILE=staging make infra-plan

# Production
AWS_PROFILE=production make infra-plan
```

### Using Workspaces

```bash
# List workspaces
make infra-workspace-list

# Create new workspace
WORKSPACE=staging make infra-workspace-new

# Switch workspace
WORKSPACE=production make infra-workspace-select

# Apply in current workspace
make infra-up
```

## Cost Management

### Destroy Infrastructure When Not Needed

```bash
# Interactive destroy
make infra-down

# Non-interactive (careful!)
AUTO=true make infra-down
```

### Check Costs Before Applying

```bash
# Requires Infracost API key
INFRACOST_API_KEY=your_key make infra-cost
```

## Maintenance Tasks

### Format Terraform Code

```bash
# Auto-format all .tf files
make infra-fmt

# Validate configuration
make infra-validate

# Both format and validate
make infra-check
```

### Refresh State

Sync state with actual infrastructure:

```bash
make infra-refresh
```

### Import Existing Resources

```bash
# Import an existing AWS resource
RESOURCE=aws_instance.web ID=i-1234567890 make infra-import
```

## Troubleshooting

### Backend Configuration Changed

If you see "Backend initialization required":

```bash
# Option 1: Reinitialize (keeps state)
make infra-reinit

# Option 2: Clean everything and start fresh
make infra-clean-cache
make infra-init
```

### AWS Credentials Not Working

```bash
# Check which profile is being used
make infra-check-aws

# Try a different profile
AWS_PROFILE=another-profile make infra-check-aws

# Check credentials file
cat ~/.aws/credentials
```

### State Lock Error

Someone else might be running Terraform:

```bash
# Check who has the lock
make infra-state-list

# Wait and retry
sleep 30
make infra-plan
```

### Docker Volume Issues

```bash
# Remove cached .terraform directory
make infra-clean-cache

# Reinitialize
make infra-init
```

## Advanced Usage

### Running Terraform Console

Test expressions and explore state:

```bash
make infra-console

# In console:
> var.environment
> aws_instance.web.public_ip
> exit
```

### Generate Infrastructure Graph

Visualize resource dependencies:

```bash
make infra-graph
# Creates infrastructure-graph.png
```

### Quick Deploy

Initialize and apply in one command:

```bash
make infra-up
```

### Using Environment Variables

```bash
# Set defaults
export AWS_PROFILE=staging
export AWS_REGION=eu-west-1

# Now commands use these defaults
make infra-plan
make infra-up
```

## CI/CD Integration

### GitHub Actions Example

```yaml
- name: Deploy Infrastructure
  run: |
    AWS_PROFILE=production AUTO=true make infra-up
```

### Jenkins Example

```groovy
sh 'AWS_PROFILE=production AUTO=true make infra-up'
```

## Best Practices

1. **Always plan before applying**
   ```bash
   make infra-plan
   # Review changes
   make infra-up
   ```

2. **Use workspaces for environments**
   ```bash
   WORKSPACE=staging make infra-workspace-select
   make infra-up
   ```

3. **Tag resources appropriately**
   - Environment tags
   - Cost center tags
   - Owner tags

4. **Destroy unused infrastructure**
   ```bash
   # Dev environment after work
   AWS_PROFILE=dev make infra-down
   ```

5. **Keep state secure**
   - Never commit state files
   - Use encrypted S3 backend
   - Enable versioning

## Common Patterns

### Morning Startup

```bash
# Check credentials
make infra-check-aws

# See current state
make infra-state-list

# Plan any pending changes
make infra-plan
```

### End of Day Cleanup

```bash
# Destroy dev environment to save costs
AWS_PROFILE=dev AUTO=true make infra-down
```

### Deploy New Feature

```bash
# Switch to feature branch
git checkout feature/new-service

# Plan changes
make infra-plan

# Apply if looks good
make infra-up

# Check outputs
make infra-output
```

### Emergency Rollback

```bash
# Quick destroy if something goes wrong
AUTO=true make infra-down

# Or revert to previous state
git checkout main
make infra-up
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