# GitHub Merge Workflow with Make Targets

## Purpose
This guide provides AI agents and developers with comprehensive instructions for using Make targets to interact with GitHub during PR creation, monitoring, and merging workflows.

## Quick Reference

### Essential Commands
```bash
make gh-watch-checks    # Dashboard monitor for CI/CD checks
make gh-pr-status       # Quick PR status overview
make gh-pr-create       # Create PR with template
make gh-pr-merge        # Auto-merge after checks pass
make gh-check-details   # Show detailed failure logs
```

## Dashboard Monitor (`gh-watch-checks`)

### Overview
The `gh-watch-checks` target provides a non-scrolling, dashboard-style monitor for GitHub CI/CD checks. It automatically refreshes every 5 seconds and provides color-coded status indicators.

### Features
- **Real-time Updates**: Refreshes every 5 seconds
- **Color-Coded Status**:
  - 🟢 Green: Passed checks
  - 🔴 Red: Failed checks
  - 🔵 Blue: Running checks
  - 🟡 Yellow: Queued/Cancelled checks
- **Summary Statistics**: Shows total, passed, failed, and running counts
- **Non-Scrolling Display**: Fixed dashboard that updates in place

### Usage
```bash
# Start monitoring current PR
make gh-watch-checks

# Dashboard will show:
# - PR information (number, title, branch, author)
# - Individual check status with icons
# - Summary statistics
# - Auto-refresh countdown
```

### When to Use
- After creating a PR to monitor CI/CD progress
- During code review to ensure checks pass
- Before merging to verify all checks are green
- When debugging CI/CD failures

## Complete PR Workflow

### Step 1: Create Feature Branch
```bash
git checkout -b feature/my-feature
# Make your changes
git add .
git commit -m "feat: Add new feature"
```

### Step 2: Run Local Quality Checks
```bash
# Run comprehensive linting
make lint-all

# Run all tests
make test

# Fix any issues before creating PR
```

### Step 3: Create Pull Request
```bash
# Push branch and create PR with template
make gh-pr-create

# This will:
# 1. Push current branch to origin
# 2. Create PR with comprehensive template
# 3. Set up for monitoring
```

### Step 4: Monitor CI/CD Checks
```bash
# Start the dashboard monitor
make gh-watch-checks

# Dashboard shows:
╔════════════════════════════════════════════════════════════════╗
║                   GitHub CI/CD Check Dashboard                  ║
╚════════════════════════════════════════════════════════════════╝

📋 PR Information:
  PR: #42 - feat: Add user authentication
  Branch: feature/auth-system
  Author: developer
  State: OPEN

🔄 Check Status: (Updated: 14:23:45)
────────────────────────────────────────────────────────────────
✅ Linting - PASSED
✅ Testing - PASSED
🔄 Build - RUNNING
⏳ Security Scan - QUEUED

📊 Summary:
  Total: 4 | Passed: 2 | Failed: 0 | Running: 1

🔄 Checks in progress...
────────────────────────────────────────────────────────────────
🔄 Auto-refresh: 5s | Press Ctrl+C to exit
```

### Step 5: Handle Check Failures
```bash
# If any checks fail, get detailed logs
make gh-check-details

# This shows:
# - List of failed checks
# - Detailed error logs for each failure
# - Specific line numbers and error messages

# Fix issues locally, then push fixes
git add .
git commit -m "fix: Resolve CI failures"
git push

# Resume monitoring
make gh-watch-checks
```

### Step 6: Merge PR
```bash
# Once all checks pass, merge the PR
make gh-pr-merge

# This will:
# 1. Verify all checks passed
# 2. Squash and merge the PR
# 3. Delete the feature branch
# 4. Update local main branch
```

## Integration with `/done` Command

### How `/done` Uses GitHub Targets

The `/done` command now integrates with the GitHub dashboard monitor for better CI/CD visibility:

#### Previous Workflow (Manual)
```bash
# Old method using direct gh commands
gh pr checks $(gh pr view --json number -q .number)
gh run list --branch $(git branch --show-current)
gh run watch <run-id>
```

#### New Workflow (Dashboard)
```bash
# New method using Make targets
make gh-watch-checks  # Real-time dashboard monitoring
make gh-check-details # Detailed failure analysis
make gh-pr-merge      # Automated merge when ready
```

### Updated `/done` Command Flow

1. **Pre-commit checks**: `make lint-all` and `make test`
2. **Create commit**: Standard git commit with Claude signature
3. **Push changes**: `git push -u origin <branch>`
4. **Create PR**: `make gh-pr-create` (if no PR exists)
5. **Monitor checks**: `make gh-watch-checks` (dashboard mode)
6. **Handle failures**: `make gh-check-details` for debugging
7. **Auto-merge**: `make gh-pr-merge` when all checks pass

### Example `/done` Execution
```bash
/done

# System will:
1. Run quality checks locally
2. Commit and push changes
3. Create/update PR
4. Launch dashboard monitor with: make gh-watch-checks
5. Wait for all checks to pass
6. Optionally auto-merge with: make gh-pr-merge
```

## Troubleshooting CI/CD Failures

### Common Issues and Solutions

#### 1. Linting Failures
```bash
# Check specific linting errors
make gh-check-details

# Fix locally
make lint-fix
make lint-all

# Commit and push fixes
git add . && git commit -m "style: Fix linting issues" && git push
```

#### 2. Test Failures
```bash
# View failure details
make gh-check-details

# Run tests locally to reproduce
make test

# Fix tests and verify
make test-unit  # Just unit tests
make test-all   # All tests

# Push fixes
git add . && git commit -m "fix: Resolve test failures" && git push
```

#### 3. Build Failures
```bash
# Check build logs
make gh-check-details

# Test build locally
make build

# Fix and verify
# ... make necessary changes ...
make build

# Push fixes
git add . && git commit -m "fix: Resolve build issues" && git push
```

#### 4. Merge Conflicts
```bash
# Update branch with latest main
git fetch origin
git rebase origin/main

# Resolve conflicts
# ... fix conflicts ...
git add .
git rebase --continue

# Force push (carefully!)
git push --force-with-lease

# Resume monitoring
make gh-watch-checks
```

## Advanced Usage

### Custom Check Intervals
```bash
# Modify refresh rate (default: 5 seconds)
GH_CHECK_INTERVAL=10 make gh-watch-checks
```

### Specific Workflow Triggers
```bash
# Manually trigger a specific workflow
make gh-workflow-run WORKFLOW=test

# List recent runs
make gh-run-list
```

### PR Review Commands
```bash
# Approve PR
make gh-pr-approve

# Add review comment
make gh-pr-review COMMENT="Looks good, just one suggestion..."
```

### Scripting and Automation
```bash
# Get raw JSON for scripting
make gh-pr-checks-raw | jq '.[] | select(.conclusion == "failure")'

# Check if all tests passed
if make gh-pr-checks-raw | jq -e 'all(.conclusion == "success")'; then
    echo "All checks passed!"
    make gh-pr-merge
fi
```

## Best Practices

### 1. Always Monitor Checks
- Use `make gh-watch-checks` immediately after pushing changes
- Keep dashboard open during PR review process
- Watch for intermittent failures that may need retry

### 2. Fix Failures Promptly
- Use `make gh-check-details` to understand failures
- Fix issues locally before pushing
- Run relevant checks locally first (`make lint-all`, `make test`)

### 3. Clean Commit History
- Use squash merge (`make gh-pr-merge` does this automatically)
- Write clear commit messages
- Group related changes together

### 4. Automate When Possible
- Let `make gh-pr-merge` handle the merge process
- Use dashboard monitor instead of manual polling
- Integrate with `/done` command for full automation

## Dashboard Keyboard Shortcuts

While the dashboard is running:
- **Ctrl+C**: Exit dashboard
- **Auto-refresh**: Happens automatically every 5 seconds
- No manual refresh needed - it's fully automated

## Environment Requirements

### Required Tools
- `gh` (GitHub CLI) - version 2.0 or higher
- `jq` - for JSON parsing
- `git` - configured with proper credentials
- `make` - GNU Make 3.81 or higher

### Setup Verification
```bash
# Check gh CLI is installed and authenticated
gh auth status

# Verify you're on a feature branch
git branch --show-current

# Ensure you have push access
git remote -v
```

## Integration with CI/CD

### GitHub Actions Compatibility
The dashboard monitor works with standard GitHub Actions workflows:
- Reads check status from GitHub API
- Supports all standard check types
- Works with required status checks
- Respects branch protection rules

### Custom Workflows
If using custom workflows, ensure they:
- Report status correctly to GitHub
- Use standard check names
- Complete within reasonable timeouts
- Provide clear failure messages

## Summary

The GitHub merge workflow with Make targets provides:
1. **Simplified Commands**: Easy-to-remember Make targets
2. **Visual Monitoring**: Dashboard-style check monitoring
3. **Automated Workflows**: From PR creation to merge
4. **Better Debugging**: Detailed failure logs on demand
5. **Integration**: Seamless `/done` command support

Use `make gh-help` for quick reference of all available GitHub targets.
