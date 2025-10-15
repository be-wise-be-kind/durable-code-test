# How to Run Linting

**Purpose**: Guide for running linting and code quality checks using poetry and npm via Just targets

**Scope**: Code quality analysis, linting automation, style enforcement

**Overview**: Linting is performed using native tooling (poetry for Python, npm for frontend) via Just task runner.
    This provides fast execution with dependency caching and parallel execution capabilities.

**Dependencies**: Poetry, Node.js, Just task runner, linting tools (Ruff, ESLint, MyPy, etc.)

**Exports**: Linting workflows, quality check procedures, automated enforcement patterns

**Related**: Code quality standards, justfile targets, pre-commit hooks

**Implementation**: Just-based linting automation with poetry run and npm run

---

## Quick Commands

```bash
# Run all linting (Python + frontend + infrastructure)
just lint

# Run specific scope
just lint python      # Python only (Ruff, MyPy, Pylint, Bandit, Xenon)
just lint frontend    # Frontend only (TypeScript, ESLint, Stylelint, Prettier)
just lint security    # Security tools only (Bandit)
just lint infra       # Infrastructure only (Terraform fmt, Shellcheck)

# Auto-fix issues where possible
just lint-fix

# Install linting dependencies
just install
```

## Getting Started

### First Time Setup
```bash
# Install all dependencies (poetry, npm, pre-commit)
just install
```

This installs:
- Python linting tools via Poetry
- Frontend linting tools via npm
- Pre-commit hooks

## Linting Targets

### Complete Linting Suite
```bash
just lint
# or
just lint all
```

**What it runs**:
- **Python linting**: Ruff (format + lint), Flake8, MyPy, Pylint, Bandit, Xenon
- **Frontend linting**: TypeScript compiler, ESLint, Stylelint, Prettier
- **Infrastructure linting**: Terraform fmt, Shellcheck

**Execution**: Python and frontend linting run in parallel for faster execution.

### Python-Only Linting
```bash
just lint python
```

**Tools run**:
- **Ruff format**: Python code formatting
- **Ruff lint**: Fast Python linting
- **Flake8**: Style guide enforcement
- **MyPy**: Static type checking
- **Pylint**: Code analysis and patterns
- **Bandit**: Security issue detection
- **Xenon**: Complexity analysis

### Frontend-Only Linting
```bash
just lint frontend
```

**Tools run**:
- **TypeScript**: Type checking
- **ESLint**: JavaScript/TypeScript linting
- **Stylelint**: CSS linting
- **Prettier**: Code formatting check

### Security Linting
```bash
just lint security
```

**Tools run**:
- **Bandit**: Python security scanner

### Infrastructure Linting
```bash
just lint infra
```

**Tools run**:
- **Terraform fmt**: Terraform file formatting
- **Shellcheck**: Shell script analysis (if installed)

### Auto-fix Linting Issues
```bash
just lint-fix
```

**What it fixes**:
- Python code formatting (Ruff)
- Python simple violations (Ruff with --fix)
- Frontend formatting (Prettier)
- Frontend auto-fixable issues (ESLint with --fix)
- CSS formatting (Stylelint with --fix)

## Direct Tool Usage

If you need to run tools directly:

### Python Tools (via Poetry)
```bash
# From backend directory
cd durable-code-app/backend

# Ruff
poetry run ruff format app  # Format code
poetry run ruff check app   # Lint code

# MyPy
poetry run mypy .

# Pylint
poetry run pylint app

# Bandit
poetry run bandit -r app
```

### Frontend Tools (via npm)
```bash
# From frontend directory
cd durable-code-app/frontend

# TypeScript
npm run typecheck

# ESLint
npm run lint
npm run lint:fix  # Auto-fix

# Prettier
npm run format:check
npm run format  # Auto-fix

# Stylelint
npm run lint:css
npm run lint:css:fix  # Auto-fix
```

## Pre-commit Hooks

Pre-commit hooks automatically run linting on changed files:

### Configuration
**Location**: `.pre-commit-config.yaml`

### Manual Execution
```bash
# Run all hooks on staged files
pre-commit run

# Run all hooks on all files
pre-commit run --all-files

# Run specific hook
pre-commit run python-ruff --all-files
```

### Hook Workflow
1. **Auto-fix**: `just lint-fix` runs first and auto-fixes issues
2. **Per-file checks**: Individual linters run on changed files only
3. **Parallel execution**: Multiple hooks run concurrently

## CI/CD Integration

### GitHub Actions
Linting runs in CI using the same `just lint` command:

**Location**: `.github/workflows/lint.yml`

**Features**:
- Poetry dependency caching
- npm dependency caching
- Parallel Python and frontend linting
- Fast execution (~2-3 minutes)

## Linting Output

### Success
```
╔════════════════════════════════════════════════════════════╗
║              Running Linting: all                          ║
╚════════════════════════════════════════════════════════════╝

Running all linters in parallel...
━━━ Python Linters ━━━
• Ruff format...
• Ruff lint...
• Flake8...
• MyPy...
• Pylint...
• Bandit...
• Xenon...
✓ Python linting passed

━━━ TypeScript/React Linters ━━━
• TypeScript...
• ESLint...
• Stylelint...
• Prettier...
✓ Frontend linting passed

━━━ Infrastructure Linters ━━━
• Terraform format             ✓
• Shellcheck                   ✓
✓ Infrastructure linting passed

✅ Linting checks passed!
```

### Failure
Linting will fail with detailed error messages showing:
- File and line number
- Rule that failed
- Description of the issue
- Suggestion for fixing (when available)

## Troubleshooting

### Tools Not Found
```bash
# Reinstall dependencies
just install

# Verify Poetry installation
cd durable-code-app/backend && poetry install

# Verify npm installation
cd durable-code-app/frontend && npm ci
```

### Linting Failures
```bash
# Try auto-fix first
just lint-fix

# Run specific scope to isolate issue
just lint python
just lint frontend

# Check specific tool directly
cd durable-code-app/backend && poetry run ruff check app
cd durable-code-app/frontend && npm run lint
```

### Pre-commit Hook Issues
```bash
# Reinstall hooks
pre-commit install
pre-commit install --hook-type pre-push

# Clear pre-commit cache
pre-commit clean

# Update hooks
pre-commit autoupdate
```

### Performance Issues
```bash
# Lint specific scope instead of all
just lint python  # Faster than 'just lint'

# Skip pre-push hooks temporarily (not recommended)
PRE_PUSH_SKIP=1 git push
```

## Best Practices

### Development Workflow
1. **Run lint-fix first**: `just lint-fix` before committing
2. **Commit incrementally**: Small commits = faster pre-commit hooks
3. **Fix promptly**: Address linting issues as they arise
4. **Full validation**: Run `just lint` before pushing

### Performance Tips
- Use scoped linting (`just lint python`) when working on specific code
- Pre-commit hooks only run on changed files for speed
- CI caches dependencies for fast subsequent runs

### Migration from Docker
If you previously used Docker for linting:
- Replace `docker exec ... poetry run ruff` with `cd durable-code-app/backend && poetry run ruff`
- Replace `docker exec ... npm run lint` with `cd durable-code-app/frontend && npm run lint`
- All `just lint*` targets now use poetry/npm directly

## Advanced Usage

### Custom Linting Scripts
You can add custom linting scripts to `justfile`:

```just
# Example: Lint only modified files
lint-changed:
    @git diff --name-only --cached | grep '\.py$' | xargs poetry run ruff check
```

### Linting in CI
The CI workflow uses the same commands:

```yaml
- name: Install dependencies
  run: just install

- name: Run linting
  run: just lint
```

This ensures parity between local and CI environments.
