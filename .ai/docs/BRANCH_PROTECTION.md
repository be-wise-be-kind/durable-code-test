# Branch Protection Rules Configuration

**Purpose**: Configure GitHub branch protection rules to enforce code quality standards and durability requirements

**Scope**: Git repository settings, CI/CD pipeline requirements, code review processes

**Overview**: Establishes comprehensive branch protection rules that enforce code quality, security,
    and collaboration standards through automated validation and mandatory review processes. Defines
    protection policies for main and development branches, required status checks, review requirements,
    and merge restrictions that ensure all code changes meet project standards before integration.

**Dependencies**: GitHub repository settings, CI/CD pipeline, automated testing, linting tools

**Exports**: Branch protection configurations, review policies, merge requirements, quality gates

**Related**: CI/CD pipeline configuration, testing framework, code review guidelines, quality standards

**Implementation**: GitHub branch protection API configuration, automated enforcement rules, quality gate integration

---

## Overview
This document outlines the required GitHub branch protection rules to enforce code quality standards and ensure all code meets our durability requirements.

## Required Settings for `main` Branch

### 1. Navigate to Settings
1. Go to your repository on GitHub
2. Click on **Settings** → **Branches**
3. Click **Add rule** or edit existing rule for `main`

### 2. Branch Protection Rules

#### Basic Settings
- ✅ **Require a pull request before merging**
  - ✅ Require approvals: 1 (minimum)
  - ✅ Dismiss stale pull request approvals when new commits are pushed
  - ✅ Require review from CODEOWNERS (if applicable)

#### Status Checks
- ✅ **Require status checks to pass before merging**
  - ✅ Require branches to be up to date before merging

  **Required status checks (must pass):**
  - `Python Code Quality`
  - `TypeScript/React Code Quality`
  - `Quality Gate Check`
  - `Code Coverage Analysis` (optional but recommended)

#### Conversation Resolution
- ✅ **Require conversation resolution before merging**

#### Additional Settings
- ✅ **Require signed commits** (optional but recommended)
- ✅ **Include administrators** (enforce rules for admins too)
- ✅ **Restrict who can push to matching branches** (optional)

### 3. Quality Gate Enforcement

The following checks MUST pass before any PR can be merged:

#### Python Requirements
- **Black**: Code formatting compliance
- **isort**: Import sorting compliance
- **Ruff**: Fast linting checks
- **Flake8**: Style guide adherence (max complexity: 5)
- **MyPy**: Type checking with strict mode
- **Bandit**: Security vulnerability scanning
- **Radon**: Complexity must be Grade A
- **Xenon**: All modules must maintain Grade A complexity

#### TypeScript/React Requirements
- **TypeScript**: Full compilation without errors
- **ESLint**: All rules must pass with 0 warnings
- **Prettier**: Code formatting compliance
- **Security**: No high or critical vulnerabilities

### 4. Manual Configuration Steps

After this PR is merged, please configure the branch protection rules:

```bash
# Using GitHub CLI (if you have appropriate permissions)
gh api repos/:owner/:repo/branches/main/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["Python Code Quality","TypeScript/React Code Quality","Quality Gate Check"]}' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{"required_approving_review_count":1,"dismiss_stale_reviews":true}' \
  --field restrictions=null \
  --field allow_force_pushes=false \
  --field allow_deletions=false
```

### 5. Bypass Guidelines

**Emergency Bypass** (use sparingly):
- Only repository administrators can bypass
- Must document reason in PR description
- Should create follow-up issue to fix any bypassed checks

### 6. Local Pre-commit Checks

Developers should run these commands before pushing:

```bash
# Run all linting checks locally
just lint-all

# Auto-fix issues where possible
just lint-fix

# Check complexity ratings
just lint-complexity

# Run security checks
just lint-security
```

### 7. Monitoring and Metrics

Track these metrics monthly:
- Number of PRs blocked by quality gates
- Average complexity scores
- Security vulnerabilities found and fixed
- Code coverage trends

## Benefits of These Rules

1. **Code Durability**: Enforces complexity limit of A grade
2. **Consistency**: Automated formatting ensures uniform code style
3. **Type Safety**: Strict type checking prevents runtime errors
4. **Security**: Automated vulnerability scanning
5. **Maintainability**: Low complexity ensures code is easy to understand
6. **Quality Gates**: Prevents low-quality code from entering main branch

## Troubleshooting

### If checks are failing:

1. **Run locally first**: `just lint-all`
2. **Auto-fix when possible**: `just lint-fix`
3. **Check complexity**: `just lint-complexity`
4. **Review specific tool output** in GitHub Actions logs

### Common issues:

- **Complexity too high**: Refactor into smaller functions
- **Type errors**: Add proper type annotations
- **Security issues**: Review Bandit output and fix vulnerabilities
- **Import order**: Run `poetry run isort .` or `npm run lint:fix`

## Contact

For questions about these rules or requesting exceptions, please:
1. Open an issue with the `quality-gate` label
2. Include justification for any exception requests
3. Tag the repository maintainers
