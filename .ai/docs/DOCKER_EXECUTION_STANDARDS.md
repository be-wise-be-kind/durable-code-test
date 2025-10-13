# Docker Execution Standards

**Purpose**: Establish mandatory Docker execution requirements for all development tools, scripts, and testing utilities

**Scope**: All development workflows, testing procedures, script execution, and tooling across the project

**Overview**: Enforces containerized execution for all development activities to ensure consistent
    environments, dependency management, and reproducible results across different developer systems.
    Eliminates environment-specific issues by requiring all tools, scripts, and tests to run within
    controlled Docker containers. Provides standardized execution patterns and prevents local system
    configuration dependencies that can cause inconsistent behavior.

**Dependencies**: Docker engine, docker-compose, container images, justfile targets

**Exports**: Docker execution patterns, container-based development workflows, environment standards

**Related**: Makefile, docker-compose.yml, development tooling, testing framework

**Implementation**: Just targets with docker exec commands, containerized script execution, no local tool dependencies

---

## Core Principle
All development tools, scripts, and testing utilities execute within Docker containers to ensure consistent environments and eliminate local system dependencies. **Never assume local system configuration** - all development workflows must be containerized.

## Script Organization Standards

### Directory Structure
```
scripts/                           # All scripts in this directory
├── check-page-content.js          # Advanced page verification
├── simple-check.js               # Basic page verification
├── test-rendered-content.js       # Direct content verification
├── ci-cd-parity-check.sh          # CI/CD verification
├── gh-watch-checks.sh             # GitHub checks monitoring
├── lint-and-request-fix.sh        # Linting automation
└── lint-watch-dashboard.sh        # Linting dashboard
```

### Forbidden Locations
- ❌ Root directory (`/home/user/project/script.js`)
- ❌ Frontend scripts directory (`durable-code-app/frontend/scripts/`)
- ❌ Any location requiring local execution

## Execution Patterns

### JavaScript/Node.js Scripts
**Pattern**: `docker exec durable-code-frontend-dev node /app/scripts/[script-name].js`

**Examples**:
```bash
# Page content verification
docker exec durable-code-frontend-dev node /app/scripts/check-page-content.js

# Simple page check
docker exec durable-code-frontend-dev node /app/scripts/simple-check.js

# Direct content verification
docker exec durable-code-frontend-dev node /app/scripts/test-rendered-content.js
```

### Python Scripts
**Pattern**: `docker exec durable-code-backend-dev python /app/scripts/[script-name].py`

**Examples**:
```bash
# Backend utilities
docker exec durable-code-backend-dev python /app/scripts/data-processor.py

# Database migrations
docker exec durable-code-backend-dev python /app/scripts/migrate.py
```

### Shell Scripts
**Pattern**: `docker exec [container] /app/scripts/[script-name].sh`

**Examples**:
```bash
# CI/CD checks
docker exec durable-code-frontend-dev /app/scripts/ci-cd-parity-check.sh

# Lint monitoring
docker exec durable-code-frontend-dev /app/scripts/lint-watch-dashboard.sh
```

## Make Target Integration

### Make Target Pattern
All scripts should be accessible via Just targets for consistency:

```justfile
# Basic pattern
script-name: ## Description of what the script does
	@docker exec container-name command /app/scripts/script-name.ext

# Example implementations
check-page: ## Check if the frontend page renders content properly
	@docker exec durable-code-frontend-dev node /app/scripts/simple-check.js

check-page-full: ## Full page check with Playwright (requires setup)
	@docker exec durable-code-frontend-dev node /app/scripts/check-page-content.js

test-content: ## Verify page content using direct HTTP check
	@docker exec durable-code-frontend-dev node /app/scripts/test-rendered-content.js
```

## Documentation Standards

### Command Documentation
All documentation MUST show Docker execution, never local execution.

**Correct Documentation**:
```markdown
## Usage
```bash
# Direct script execution via Docker
docker exec durable-code-frontend-dev node /app/scripts/check-page-content.js
docker exec durable-code-frontend-dev node /app/scripts/test-rendered-content.js
```

**Incorrect Documentation**:
```markdown
## Usage
```bash
# DON'T: Shows local execution
node scripts/test-rendered-content.js
node test-rendered-content.js
```

### Template Standards
When documenting workflows, always include the Docker execution pattern:

```markdown
### Development Workflow
1. Start development environment: `just dev`
2. Basic verification: `docker exec durable-code-frontend-dev node /app/scripts/check-page-content.js`
3. Debug issues: `docker exec durable-code-frontend-dev node /app/scripts/test-rendered-content.js`
4. Continuous monitoring: `docker exec durable-code-frontend-dev node /app/scripts/simple-check.js --watch`
```

## Container Path Mapping

### Frontend Container Paths
- **Host**: `scripts/script.js`
- **Container**: `/app/scripts/script.js`
- **Execution**: `docker exec durable-code-frontend-dev node /app/scripts/script.js`

### Backend Container Paths
- **Host**: `scripts/script.py`
- **Container**: `/app/scripts/script.py`
- **Execution**: `docker exec durable-code-backend-dev python /app/scripts/script.py`

## Development Environment Requirements

### Container Dependencies
Containers MUST include all required dependencies:

**Frontend Container**:
- Node.js + npm/yarn
- Playwright (for advanced page testing)
- All npm dependencies from package.json

**Backend Container**:
- Python + pip/poetry
- All Python dependencies from requirements.txt/pyproject.toml

### No Local Dependencies
Scripts MUST NOT require:
- ❌ Local Node.js installation
- ❌ Local Python installation
- ❌ Local package managers (npm, pip, yarn)
- ❌ Local browser installations
- ❌ Local system libraries

## Error Handling

### Container Not Running
```bash
# Check container status
just status
docker ps

# Start containers if needed
just dev

# Then run script
docker exec durable-code-frontend-dev node /app/scripts/script.js
```

### Script Not Found
```bash
# Verify script exists in container
docker exec durable-code-frontend-dev ls -la /app/scripts/

# Check if file was copied correctly
docker exec durable-code-frontend-dev cat /app/scripts/script.js
```

## Migration Guide

### Moving Scripts to Docker Execution

1. **Identify Local Execution**:
   ```bash
   # Find references to local execution
   grep -r "node scripts/" .ai/
   grep -r "python scripts/" .ai/
   ```

2. **Update Documentation**:
   ```bash
   # Replace local patterns with Docker patterns
   node scripts/script.js → docker exec durable-code-frontend-dev node /app/scripts/script.js
   python scripts/script.py → docker exec durable-code-backend-dev python /app/scripts/script.py
   ```

3. **Verify Container Access**:
   ```bash
   # Test script execution in container
   docker exec durable-code-frontend-dev node /app/scripts/script.js
   ```

4. **Update Make Targets**:
   ```justfile
   # Update Makefile to use Docker execution
   target-name:
   	@docker exec container-name command /app/scripts/script.ext
   ```

## Quality Assurance

### Script Validation Checklist
- [ ] Script located in `scripts/` directory
- [ ] No scripts in root directory
- [ ] No scripts in frontend/scripts/
- [ ] All documentation shows Docker execution
- [ ] Just targets use Docker execution
- [ ] No references to local execution patterns

### Documentation Review Checklist
- [ ] All command examples use `docker exec`
- [ ] No examples show `node scripts/` (local execution)
- [ ] Container paths use `/app/scripts/` format
- [ ] Just targets documented as preferred method
- [ ] Error handling includes container status checks

## Container Best Practices

### Script Development
1. **Write scripts assuming container environment**
2. **Test scripts inside containers during development**
3. **Use container-specific paths (`/app/scripts/`)**
4. **Handle container-specific networking (localhost within container)**

### Container Networking
```javascript
// Scripts should use container-internal networking
const response = await fetch('http://localhost:5173'); // Works inside container
// Not: external host networking
```

### Container File System
```bash
# Scripts have access to container file system
/app/                          # Project root in container
/app/scripts/                  # Scripts directory
/app/durable-code-app/         # Application code
/app/node_modules/             # Dependencies
```

## Related Documentation
- `Makefile` - Make target definitions using Docker execution
- `.ai/howto/test-page-content.md` - Page testing using Docker
- `.ai/features/error-boundaries.md` - Error boundary testing with Docker
- `docker-compose.yml` - Container configuration
- `docker-compose.dev.yml` - Development container setup
