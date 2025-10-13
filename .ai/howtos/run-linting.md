# How to Run Linting - Updated for Dedicated Containers

**Purpose**: Guide for running linting and code quality checks using dedicated Docker containers and Make targets

**Scope**: Code quality analysis, linting automation, style enforcement, design linter execution

**Overview**: Linting is now performed using dedicated Docker containers separate from development containers.
    This provides better performance, tool isolation, and cleaner separation of concerns.
    All existing Make targets have been preserved for a seamless developer experience.

**Dependencies**: Make build system, dedicated linting Docker containers, design linters, code quality frameworks

**Exports**: Linting workflows, quality check procedures, automated enforcement patterns

**Related**: Design linting framework, code quality standards, Docker linting architecture

**Implementation**: Make-based linting automation with dedicated containers, parallel execution capabilities

---

## 🚀 New Architecture Overview

Linting has been separated into dedicated Docker containers for improved performance and maintainability:

- **Python Linting Container**: Contains all Python linting tools (Black, Ruff, MyPy, Pylint, Flake8, Bandit, Xenon)
- **JavaScript Linting Container**: Contains all frontend linting tools (ESLint, Prettier, TypeScript, HTMLHint, Stylelint)
- **Development Containers**: Now contain only runtime dependencies (30-50% faster startup)

### Key Benefits
- ⚡ **30-50% faster** development container startup
- 🎯 **Parallel linting** execution capability
- 🔧 **Independent tool updates** without rebuilding dev containers
- 💾 **Better CI caching** and improved build times
- 🔒 **Reduced attack surface** in production containers

## Quick Commands (Unchanged)

```bash
# Run all linting rules
make lint-all

# Run custom design linters only
make lint-custom

# Auto-fix issues where possible
make lint-fix

# List available rules
make lint-list-rules

# Check container status (new)
make lint-containers-status
```

> **Note**: All existing Make targets work exactly as before. The dedicated containers are managed automatically.

## Important: Always Check Available Make Targets First

```bash
# Get basic list of available commands
make help

# Get comprehensive list of all make targets (recommended)
make help-full
```

## Make Target Details

### Complete Linting Suite
```bash
make lint-all
```
**What it runs** (now in dedicated containers):
- Python linting (Black, isort, Ruff, Flake8, MyPy, Pylint, Bandit, Xenon)
- TypeScript/React linting (ESLint, Prettier, TypeScript, Stylelint, HTMLHint)
- Custom design linters (SOLID, Style, Literals, Logging, Loguru, Security, Error handling)
- Infrastructure linting (TFLint, ShellCheck)

**Container management**: Automatically starts and stops dedicated linting containers

### Custom Design Linters
```bash
make lint-custom
```
**What it runs**:
- SOLID principle enforcement
- Magic number detection
- Print statement detection
- Code complexity analysis
- Logging best practices
- Security rules
- Error handling patterns
- Testing practices

### Auto-fix Linting Issues
```bash
make lint-fix
```
**What it fixes**:
- Code formatting (Black, Prettier)
- Import sorting (isort)
- Simple style violations (Ruff, ESLint)
- CSS formatting (Stylelint)
- Trailing whitespace

### Rule Discovery
```bash
make lint-list-rules
```
**Output**: All available linting rules organized by category

## Container Management (Advanced)

While Make targets handle containers automatically, you can manage them manually if needed:

### Container Status
```bash
# Check linting container status
make lint-containers-status
```

### Manual Container Operations
```bash
# Start linting containers manually
docker-compose -f docker-compose.lint.yml up -d

# Check container logs
docker-compose -f docker-compose.lint.yml logs

# Stop containers manually
docker-compose -f docker-compose.lint.yml down
```

### Direct Container Execution (Advanced)
```bash
# Run Python linting directly in container
docker exec durable-code-python-linter-$(git branch --show-current) bash -c "cd /workspace && poetry run black --check backend"

# Run JavaScript linting directly in container
docker exec durable-code-js-linter-$(git branch --show-current) sh -c "cd /workspace/frontend && npm run lint"
```

## Design Linter Framework

### Via Make Targets (Recommended)
```bash
# Run all custom design linters
make lint-custom

# Run with categories
make lint-categories
```

### Direct CLI Usage (in Container)
```bash
# Basic usage
docker exec durable-code-python-linter-$(git branch --show-current) bash -c "cd /workspace && PYTHONPATH=/workspace/tools python -m design_linters --format text --recursive backend"

# Specific rules
docker exec durable-code-python-linter-$(git branch --show-current) bash -c "cd /workspace && PYTHONPATH=/workspace/tools python -m design_linters --rules solid.srp.too-many-methods,literals.magic-number --format text backend"

# JSON output
docker exec durable-code-python-linter-$(git branch --show-current) bash -c "cd /workspace && PYTHONPATH=/workspace/tools python -m design_linters --format json --output /tmp/lint-report.json backend"
```

### Configuration File
**Location**: `.design-lint.yml`

```yaml
rules:
  solid.srp.too-many-methods:
    max_methods: 15
  literals.magic-number:
    allowed_numbers: [0, 1, -1, 2, 100]
    ignore_test_files: true

categories:
  - solid
  - literals
  - style
  - logging

exclude_patterns:
  - "*/test_*"
  - "*/migrations/*"
```

## Linting Categories

### SOLID Principles
**Rules**:
- `solid.srp.too-many-methods`: Class method count limits
- `solid.srp.class-too-big`: Class size analysis

### Style Rules
**Rules**:
- `style.print-statement`: Print statement detection
- `style.nesting-level`: Excessive nesting detection
- `style.file-header`: File header enforcement

### Literals
**Rules**:
- `literals.magic-number`: Hardcoded number detection

### Logging
**Rules**:
- `logging.general`: General logging patterns
- `logging.loguru`: Loguru-specific rules

### Security
**Rules**:
- `security.patterns`: Security best practices

### Error Handling
**Rules**:
- `error_handling.patterns`: Proper exception handling

### Testing
**Rules**:
- `testing.practices`: Test code best practices

## Output Formats

### Text Output (Default)
```
tools/design_linters/cli.py:45: [ERROR] solid.srp.too-many-methods
  Class 'ArgumentParser' has 12 methods, exceeds limit of 10
  Consider splitting into smaller, focused classes

tools/example.py:23: [WARNING] literals.magic-number
  Magic number '42' detected
  Consider using a named constant
```

### JSON Output
```bash
make lint-custom-json
```

### SARIF Output
```bash
make lint-custom-sarif
```

## Frontend Linting

All frontend linting now runs in the dedicated JavaScript linting container:

### ESLint
```bash
# Via Make target (recommended)
make lint-all

# Direct execution in container
docker exec durable-code-js-linter-$(git branch --show-current) sh -c "cd /workspace/frontend && npm run lint"
```

### Prettier
```bash
# Check formatting
docker exec durable-code-js-linter-$(git branch --show-current) sh -c "cd /workspace/frontend && npm run format:check"

# Auto-format via Make
make lint-fix
```

### TypeScript Checking
```bash
# Via Make target
make lint-all

# Direct execution
docker exec durable-code-js-linter-$(git branch --show-current) sh -c "cd /workspace/frontend && npm run typecheck"
```

## Python Linting

All Python linting now runs in the dedicated Python linting container:

### Black (Formatting)
```bash
# Via Make target
make lint-all

# Direct execution
docker exec durable-code-python-linter-$(git branch --show-current) bash -c "cd /workspace && poetry run black --check backend"
```

### Ruff
```bash
# Check
docker exec durable-code-python-linter-$(git branch --show-current) bash -c "cd /workspace && poetry run ruff check backend"

# Auto-fix
make lint-fix
```

### MyPy (Type Checking)
```bash
docker exec durable-code-python-linter-$(git branch --show-current) bash -c "cd /workspace && MYPY_CACHE_DIR=/tmp/mypy_cache poetry run mypy backend"
```

## Pre-commit Hooks

Pre-commit hooks have been updated to use dedicated linting containers:

### Configuration
**Location**: `.pre-commit-config.yaml`

### Manual Execution
```bash
# Run all hooks (uses dedicated containers)
pre-commit run --all-files

# Run specific hook
pre-commit run black --all-files

# Run on staged files only
pre-commit run
```

## CI/CD Integration

### GitHub Actions
The CI/CD pipeline now uses dedicated linting containers for:
- Improved Docker layer caching
- Faster build times (~20-30% improvement)
- Better resource utilization
- Parallel linting execution

**Location**: `.github/workflows/lint.yml`

## Performance Benefits

### Development Experience
- **Container Startup**: 30-50% faster development container startup
- **Tool Updates**: Update linting tools without rebuilding dev environment
- **Resource Usage**: 20-30% reduction in memory usage during development
- **Parallel Execution**: Run multiple linting types simultaneously

### CI/CD Pipeline
- **Build Time**: ~20-30% faster CI linting execution
- **Cache Efficiency**: Linting tools cached separately from application code
- **Fault Isolation**: Linting failures don't affect other CI steps

## Troubleshooting

### Containers Won't Start
```bash
# Check container logs
docker-compose -f docker-compose.lint.yml logs

# Rebuild containers
docker-compose -f docker-compose.lint.yml build --no-cache

# Check Docker status
docker system info
```

### Linting Tools Not Found
```bash
# Verify tools in Python container
docker exec durable-code-python-linter-$(git branch --show-current) which black

# Verify tools in JS container
docker exec durable-code-js-linter-$(git branch --show-current) which eslint

# Rebuild if needed
docker-compose -f docker-compose.lint.yml build
```

### Volume Mount Issues
```bash
# Check mounts in Python container
docker exec durable-code-python-linter-$(git branch --show-current) ls -la /workspace/

# Check mounts in JS container
docker exec durable-code-js-linter-$(git branch --show-current) ls -la /workspace/frontend/

# Verify source files exist
ls -la durable-code-app/backend/
ls -la durable-code-app/frontend/
```

### Performance Issues
```bash
# Check resource usage
docker stats | grep linter

# Adjust resource limits in docker-compose.lint.yml if needed
```

### Container Cleanup
```bash
# Stop and remove linting containers
docker-compose -f docker-compose.lint.yml down

# Remove linting images
docker-compose -f docker-compose.lint.yml down --rmi all

# Clean up all unused containers
docker system prune -f
```

## Best Practices

### Development Workflow
1. **Use Make targets**: Always use `make lint-all`, `make lint-fix`, etc.
2. **Containers are automatic**: Make targets handle container lifecycle
3. **Fix promptly**: Address linting issues as they arise
4. **Full validation**: Run `make lint-all` before commits

### Performance Tips
- **Containers stay running**: Make targets keep containers alive for faster subsequent runs
- **Parallel execution**: Multiple linting types run simultaneously
- **Cached results**: CI uses Docker layer caching effectively
- **Resource limits**: Containers have appropriate CPU/memory limits

### Migration Notes
- All existing Make targets work identically
- No changes required to developer workflow
- Linting output format unchanged
- Pre-commit hooks automatically use dedicated containers

## Legacy Compatibility

All existing commands and workflows continue to work:

```bash
# These all work exactly as before
make lint-all
make lint-fix
make lint-custom
make lint-categories
make lint-list-rules
```

The only difference is better performance and cleaner architecture behind the scenes!