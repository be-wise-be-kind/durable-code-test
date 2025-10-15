# How to Manage Infrastructure

**Purpose**: Provide step-by-step instructions for managing AWS infrastructure using Terraform Just targets
**Scope**: Infrastructure deployment, state management, cost control, and troubleshooting procedures

---

## Prerequisites

Before starting, ensure you have:

1. **Terraform installed** (handled automatically by `just init`)
   ```bash
   # Check Terraform installation
   terraform --version  # Should show v1.9.8
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

### Step 1: Install Tools

```bash
# Install Terraform, pre-commit, and build Docker images
just init
```

This command:
- Installs tfenv (Terraform version manager)
- Installs Terraform 1.9.8
- Installs pre-commit hooks
- Builds Docker containers for the application

### Step 2: Verify AWS Credentials

```bash
# Check default profile
just infra check-aws

# Check specific profile
AWS_PROFILE=production just infra check-aws
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

### Step 3: Initialize Terraform Workspaces

```bash
# Initialize for default scope (runtime)
just infra init

# Initialize specific scope
just infra init base
just infra init runtime

# Initialize all scopes
just infra init all
```

Note: Initialization happens automatically on first use of plan/up, but can be run explicitly.

## Daily Workflow

### Planning Changes

Always preview changes before applying:

```bash
# See what will change (default: runtime scope)
just infra plan

# Plan specific scope
just infra plan base
just infra plan runtime

# With specific profile
AWS_PROFILE=staging just infra plan
```

### Applying Changes

```bash
# Interactive - will ask for confirmation (default: runtime)
just infra up

# Non-interactive - for CI/CD
just infra up runtime true

# Deploy specific scope
just infra up base
just infra up runtime

# With specific profile
AWS_PROFILE=production just infra up
```

### Checking Current State

```bash
# Show infrastructure status
just infra status

# Show outputs (default: runtime)
just infra output

# Show outputs for specific scope
just infra output base
just infra output runtime

# Show outputs as JSON (for scripts)
just infra output runtime json
```

## Environment Management

### Using Different Environments

The environment is controlled via the `ENV` variable (default: dev):

```bash
# Development
ENV=dev just infra plan

# Staging
ENV=staging just infra plan

# Production
ENV=prod just infra plan
```

### Workspace Management

Workspaces are automatically managed in the format `{scope}-{env}` (e.g., `base-dev`, `runtime-prod`):

```bash
# Show current workspace status
just infra status

# Workspaces are selected automatically based on SCOPE and ENV
ENV=staging just infra plan base  # Uses base-staging workspace
ENV=prod just infra plan runtime  # Uses runtime-prod workspace
```

## Cost Management

### Destroy Infrastructure When Not Needed

```bash
# Interactive destroy (default: runtime)
just infra down

# Destroy specific scope (requires confirmation)
just infra down runtime destroy-runtime
just infra down base destroy-base
just infra down all destroy-all

# Example: destroy runtime to save costs overnight
just infra down runtime destroy-runtime
```

## Maintenance Tasks

### Format Terraform Code

```bash
# Auto-format all .tf files recursively
just infra fmt
```

### Validate Configuration

```bash
# Validate Terraform configuration (default: runtime)
just infra validate

# Validate specific scope
just infra validate base
just infra validate runtime
```

## Troubleshooting

### Backend Configuration Changed

If you see "Backend initialization required":

```bash
# Reinitialize with -reconfigure flag (automatic in init)
just infra init
```

### AWS Credentials Not Working

```bash
# Check which profile is being used
just infra check-aws

# Try a different profile
AWS_PROFILE=another-profile just infra check-aws

# Check credentials file
cat ~/.aws/credentials
```

### State Lock Error

Someone else might be running Terraform:

```bash
# Wait and retry
sleep 30
just infra plan

# Check DynamoDB lock table
aws dynamodb scan --table-name durable-code-terraform-locks
```

**IMPORTANT**: Never force-unlock Terraform state without explicit permission (per CLAUDE.md standards).

### Terraform Not Found

If Terraform is not in PATH:

```bash
# Add tfenv to PATH
echo 'export PATH="$HOME/.tfenv/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Or use absolute path
$HOME/.tfenv/bin/terraform --version
```

## Advanced Usage

### Quick Deploy

Initialize and apply in one command:

```bash
just infra up
```

### Using Environment Variables

```bash
# Set defaults
export AWS_PROFILE=staging
export AWS_REGION=eu-west-1
export ENV=staging

# Now commands use these defaults
just infra plan
just infra up
```

## CI/CD Integration

### GitHub Actions Example

```yaml
- name: Deploy Infrastructure
  run: |
    ENV=production just infra up runtime true
```

### Jenkins Example

```groovy
sh 'ENV=production just infra up runtime true'
```

## Best Practices

1. **Always plan before applying**
   ```bash
   just infra plan
   # Review changes
   just infra up
   ```

2. **Use ENV variable for environments**
   ```bash
   ENV=staging just infra plan
   ENV=staging just infra up
   ```

3. **Separate base and runtime scopes**
   ```bash
   # Deploy persistent infrastructure once
   just infra up base

   # Deploy/destroy runtime frequently for cost savings
   just infra up runtime
   just infra down runtime destroy-runtime
   ```

4. **Tag resources appropriately**
   - Environment tags (automatic via locals)
   - Workspace tags (automatic)
   - Cost center tags
   - Owner tags

5. **Destroy unused infrastructure**
   ```bash
   # Runtime environment after work (saves costs)
   just infra down runtime destroy-runtime
   ```

6. **Keep state secure**
   - Never commit state files
   - Use encrypted S3 backend
   - Enable versioning
   - Never force-unlock without permission

## Common Patterns

### Morning Startup

```bash
# Check credentials
just infra check-aws

# Check infrastructure status
just infra status

# Plan any pending changes
just infra plan
```

### End of Day Cleanup

```bash
# Destroy runtime to save costs (keeps base infrastructure)
just infra down runtime destroy-runtime
```

### Deploy New Feature

```bash
# Switch to feature branch
git checkout feature/new-service

# Plan changes
just infra plan

# Apply if looks good
just infra up

# Check outputs
just infra output
```

### Emergency Rollback

```bash
# Quick destroy runtime if something goes wrong
just infra down runtime destroy-runtime

# Or revert to previous state
git checkout main
just infra up
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