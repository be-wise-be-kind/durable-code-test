# Complete Debugging Guide

A comprehensive guide for debugging both repository and code issues in the durable-code-test project.

## Overview

This guide covers two main debugging scenarios:

1. **Repository Debugging**: Docker containers, services, networking, and environment issues
2. **Code Debugging**: Design linter rules, test failures, and development workflow issues

---

## Part I: Repository Debugging

### Quick Debugging Commands

```bash
# Check service status
make status

# View all logs
make logs

# View specific service logs
docker logs durable-code-test-frontend-1
docker logs durable-code-test-backend-1

# Interactive debugging
docker exec -it durable-code-test-backend-1 python
docker exec -it durable-code-test-frontend-1 npm run dev
```

### Container Issues

#### Services Not Starting
```bash
# Check container status
make status
docker ps -a

# View startup logs
docker logs durable-code-test-frontend-1 --tail=50
docker logs durable-code-test-backend-1 --tail=50

# Check resource usage
docker stats --no-stream
```

**Common Causes**:
- Port conflicts (8000, 3000, 5173 already in use)
- Insufficient memory/disk space
- Missing environment variables
- Docker daemon not running

**Solutions**:
```bash
# Kill conflicting processes
sudo fuser -k 8000/tcp
sudo fuser -k 3000/tcp

# Free up disk space
docker system prune -a

# Restart Docker daemon
sudo systemctl restart docker
```

#### Container Crashes
```bash
# Check exit codes
docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# View crash logs
docker logs durable-code-test-backend-1 --since=1h

# Restart crashed containers
docker restart durable-code-test-backend-1
```

### Frontend Issues

#### Build Failures
```bash
# Check build logs
docker exec -it durable-code-test-frontend-1 npm run build

# View detailed npm logs
docker exec -it durable-code-test-frontend-1 npm run build -- --verbose

# Check for missing dependencies
docker exec -it durable-code-test-frontend-1 npm ls
```

**Common Issues**:
- TypeScript compilation errors
- Missing dependencies
- Memory issues during build
- Linting failures blocking build

**Debug Steps**:
```bash
# TypeScript errors
docker exec -it durable-code-test-frontend-1 npm run type-check

# Linting issues
docker exec -it durable-code-test-frontend-1 npm run lint

# Memory issues
docker stats durable-code-test-frontend-1

# Dependency issues
docker exec -it durable-code-test-frontend-1 npm audit
```

### Backend Issues

#### API Errors
```bash
# Test API endpoints
curl -v http://localhost:8000/health
curl -v http://localhost:8000/docs

# Check FastAPI logs
docker logs durable-code-test-backend-1 --follow

# View error details
docker exec -it durable-code-test-backend-1 python -c "
import requests
try:
    response = requests.get('http://localhost:8000/health')
    print(f'Status: {response.status_code}')
    print(f'Response: {response.text}')
except Exception as e:
    print(f'Error: {e}')
"
```

#### Database Connection Issues
```bash
# Check database status
docker exec -it durable-code-test-db-1 pg_isready

# Test connection from backend
docker exec -it durable-code-test-backend-1 python -c "
import psycopg2
try:
    conn = psycopg2.connect('postgresql://postgres:password@db:5432/durable_code')
    print('Database connection successful')
    conn.close()
except Exception as e:
    print(f'Database connection failed: {e}')
"

# View database logs
docker logs durable-code-test-db-1 --tail=50
```

---

## Part II: Code Debugging with Tests and Logging

### Core Debugging Philosophy

**NEVER create temporary test files or debugging scripts.** All debugging must be done through:

1. **Unit Tests**: Write tests to reproduce and verify fixes
2. **Loguru Logging**: Use structured logging for investigation
3. **Existing Test Repository**: Leverage the comprehensive test suite

### Code Debugging Workflow

#### 1. Reproduce the Issue with a Unit Test

**First Step**: Write a failing test that demonstrates the bug

```python
# test/unit_test/tools/design_linters/test_bug_reproduction.py
import pytest
from pathlib import Path
from tools.design_linters.rules.solid.srp_rules import TooManyMethodsRule

class TestBugReproduction:
    """Test suite for reproducing and verifying bug fixes."""

    def test_reproduce_method_count_bug(self):
        """Reproduce the method counting bug with specific code pattern."""
        # Arrange - Create the exact code that causes the issue
        source_code = '''
class ExampleClass:
    def method_one(self): pass
    def method_two(self): pass
    @property
    def not_a_method(self): pass  # This might be counted incorrectly
    @staticmethod
    def static_method(): pass
        '''

        # Act - Run the rule that's failing
        rule = TooManyMethodsRule({"max_methods": 5})
        violations = rule.check_code(source_code, Path("test_file.py"))

        # Assert - Document the expected vs actual behavior
        # This should fail initially, proving the bug exists
        assert len(violations) == 0, "Property and static methods should not count as regular methods"
```

#### 2. Add Loguru Logging for Investigation

**Use Loguru for structured debugging**:

```python
from loguru import logger

class TooManyMethodsRule(BaseRule):
    def check_node(self, node: ast.ClassDef, file_path: Path, source_lines: list[str]) -> list[LintViolation]:
        """Check class for too many methods."""
        logger.debug("Checking class: {class_name} in {file}",
                    class_name=node.name, file=file_path)

        methods = self._count_methods(node)
        logger.debug("Found {count} methods in class {class_name}: {method_names}",
                    count=len(methods),
                    class_name=node.name,
                    method_names=[m.name for m in methods])

        if len(methods) > self.max_methods:
            logger.warning("Class {class_name} exceeds method limit: {count} > {limit}",
                          class_name=node.name, count=len(methods), limit=self.max_methods)
            return [self._create_violation(node, file_path, source_lines, len(methods))]

        return []
```

#### 3. Run Tests to Observe Logging

```bash
# Run specific test with debug logging
PYTHONPATH=/home/stevejackson/Projects/durable-code-test/tools python -m pytest test/unit_test/tools/design_linters/test_bug_reproduction.py::TestBugReproduction::test_reproduce_method_count_bug -v -s --log-cli-level=DEBUG

# Run with Loguru configuration
PYTHONPATH=/home/stevejackson/Projects/durable-code-test/tools python -m pytest test/unit_test/tools/design_linters/test_bug_reproduction.py -v -s --capture=no
```

### Linting and Testing Issues

#### Linting Failures
```bash
# Run specific linter
make lint-custom

# Check design linter logs
docker exec -it durable-code-test-tools-1 design-linter tools/ --verbose

# Debug specific rule
docker exec -it durable-code-test-tools-1 design-linter tools/design_linters/cli.py --rules solid.srp.too-many-methods --verbose
```

**Common Linting Issues**:
```bash
# Module not found
export PYTHONPATH=/home/stevejackson/Projects/durable-code-test/tools
docker exec -it durable-code-test-tools-1 design-linter tools/

# Configuration issues
docker exec -it durable-code-test-tools-1 cat .design-lint.yml

# Rule discovery problems
docker exec -it durable-code-test-tools-1 design-linter --list-rules
```

#### Test Failures
```bash
# Run tests with verbose output
make test-unit

# Run specific test file
PYTHONPATH=/home/stevejackson/Projects/durable-code-test/tools python -m pytest test/unit_test/tools/design_linters/test_basic.py -v -s

# Debug test with pdb
PYTHONPATH=/home/stevejackson/Projects/durable-code-test/tools python -m pytest test/unit_test/tools/design_linters/test_basic.py::TestIgnoreFunctionality::test_line_level_ignore --pdb
```

### Test-Driven Debugging

**Always follow this pattern**:

1. **Red**: Write a failing test that reproduces the bug
2. **Green**: Implement minimal fix to make test pass
3. **Refactor**: Clean up code while keeping tests passing
4. **Verify**: Run full test suite to ensure no regressions

```python
class TestDebugExample:
    """Example of proper debugging with tests."""

    def test_bug_reproduction_step_1_failing(self):
        """Step 1: Reproduce the exact failure condition."""
        # This test should fail initially
        result = buggy_function("problematic_input")
        assert result == "expected_output"  # Will fail, proving bug exists

    def test_bug_fix_verification_step_2(self):
        """Step 2: Verify the fix works correctly."""
        # After implementing fix, this should pass
        result = fixed_function("problematic_input")
        assert result == "expected_output"

    def test_edge_cases_step_3(self):
        """Step 3: Test edge cases to prevent regressions."""
        # Test boundary conditions
        assert fixed_function("") == ""
        assert fixed_function(None) is None
```

---

## Part III: Network and Performance Issues

### Port Conflicts
```bash
# Check what's using ports
netstat -tulpn | grep :8000
lsof -i :8000

# Kill conflicting processes
sudo fuser -k 8000/tcp

# Change ports in docker-compose
# Edit .docker/compose/dev.yml to use different ports
```

### Performance Debugging

#### Resource Usage
```bash
# Monitor container resources
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"

# Check disk usage
docker system df
df -h

# Memory usage by service
docker exec -it durable-code-test-backend-1 python -c "
import psutil
print(f'Memory usage: {psutil.virtual_memory().percent}%')
print(f'CPU usage: {psutil.cpu_percent()}%')
"
```

#### Database Performance
```bash
# Check active connections
docker exec -it durable-code-test-db-1 psql -U postgres -c "
SELECT count(*) as active_connections
FROM pg_stat_activity
WHERE state = 'active';
"

# Check slow queries
docker exec -it durable-code-test-db-1 psql -U postgres -c "
SELECT query, mean_time, calls
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
"
```

---

## Part IV: Advanced Debugging Techniques

### Interactive Debugging Sessions
```bash
# Python debugging session
docker exec -it durable-code-test-backend-1 python

# Node.js debugging
docker exec -it durable-code-test-frontend-1 node

# Shell access for investigation
docker exec -it durable-code-test-backend-1 bash
docker exec -it durable-code-test-frontend-1 sh
```

### Structured Logging with Loguru

**Use contextual logging**:

```python
from loguru import logger

class DesignLinterRule:
    def __init__(self, config: dict):
        self.config = config
        # Log configuration at initialization
        logger.debug("Initializing rule {rule_name} with config: {config}",
                    rule_name=self.__class__.__name__, config=config)

    def check_file(self, file_path: Path) -> list[LintViolation]:
        """Check file for violations."""
        logger.info("Analyzing file: {file}", file=file_path)

        try:
            with open(file_path, 'r') as f:
                source = f.read()

            violations = self._analyze_source(source, file_path)

            logger.info("Analysis complete for {file}: {count} violations found",
                       file=file_path, count=len(violations))

            return violations

        except Exception as e:
            logger.error("Failed to analyze {file}: {error}",
                        file=file_path, error=str(e))
            raise
```

### Logging Configuration for Debugging

```python
# In test files or debugging context
import sys
from loguru import logger

# Configure detailed logging for debugging
logger.remove()  # Remove default handler
logger.add(
    sys.stderr,
    level="DEBUG",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>",
    colorize=True
)

# For specific debugging sessions, add file logging
logger.add(
    "debug.log",
    level="DEBUG",
    rotation="1 MB",
    retention="1 day",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}"
)
```

---

## Part V: Systematic Debugging Approach

### 1. Gather Information
```bash
# System overview
make status
docker ps -a
docker images
docker network ls

# Recent logs
docker logs durable-code-test-backend-1 --since=10m
docker logs durable-code-test-frontend-1 --since=10m
```

### 2. Isolate the Problem
```bash
# Test individual components
curl http://localhost:8000/health  # Backend health
curl http://localhost:5173         # Frontend accessibility

# Test dependencies
docker exec -it durable-code-test-db-1 pg_isready
```

### 3. Check Recent Changes
```bash
# Git history
git log --oneline -10

# File changes
git diff HEAD~1

# Environment changes
diff .env.example .env
```

### 4. Reproduce the Issue
```bash
# Clean environment
make clean
make init

# Step-by-step recreation
make dev
# Test after each step
```

---

## Best Practices Summary

### ✅ DO
1. **Write unit tests** to reproduce issues
2. **Use Loguru logging** for investigation
3. **Follow TDD cycle**: Red → Green → Refactor
4. **Run tests through proper repository** (make targets, docker)
5. **Document findings in test names and comments**
6. **Use systematic debugging approach**
7. **Check repository before diving into code**

### ❌ DON'T
- Create temporary files for debugging
- Use print statements instead of logging
- Skip the test framework
- Debug without tests to verify fixes
- Run tests locally (always use docker or make)
- Call linting directly (use make targets)

## Emergency Quick Fixes

```bash
# Reset everything
make clean && make init && make dev

# Restart specific service
docker restart durable-code-test-backend-1

# Clear Docker cache
docker system prune -a

# Reset database
docker volume rm durable-code-test_postgres_data
make dev
```

## Error Pattern Recognition

**"Module not found"**: Check PYTHONPATH, verify file locations, check import statements
**"Connection refused"**: Verify service is running, check port configuration, test network connectivity
**"Permission denied"**: Check file permissions, verify user/group ownership, check Docker socket access
**"Out of memory"**: Check available memory, monitor container limits, analyze memory leaks

This comprehensive guide ensures that debugging efforts contribute to the project's test coverage and leave behind valuable regression tests for future development.
