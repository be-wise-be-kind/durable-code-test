# How to Run Unit Tests

**Purpose**: Guide for executing unit tests using Make targets and Docker-based testing workflows

**Scope**: Unit test execution, coverage analysis, test automation, Docker-based testing requirements

**Overview**: Comprehensive testing guide that enforces Docker/Make usage requirements for consistent
    test execution across development environments. Covers test execution patterns, coverage analysis,
    debugging approaches, and automated testing workflows that ensure reliable test results and
    maintain testing standards across all development scenarios.

**Dependencies**: Docker containers, Make build system, testing frameworks, coverage tools

**Exports**: Test execution workflows, coverage analysis procedures, debugging approaches

**Related**: Testing framework documentation, development tooling, quality assurance standards

**Implementation**: Make-based test automation, Docker-containerized test execution, coverage reporting

---

## Primary Method: Make Targets (Required)

The project enforces Docker/Make usage requirements for consistent testing. **Always use make targets first.**

```bash
# See all available test commands
make help

# Run all unit tests (recommended)
make test-backend-quick

# Run with coverage
make test-backend-coverage

# Run specific test categories
make test-framework    # Design linter framework tests
make test-rules       # All linting rule tests
make test-component COMPONENT=test/path  # Specific component
```

## Available Make Targets

### Core Unit Test Commands

**Backend Unit Tests (Fastest):**
```bash
make test-backend-quick
```
- Runs all backend unit tests without coverage
- Fast feedback for development cycles
- Located in `test/unit_test/tools/design_linters/`

**Backend with Coverage:**
```bash
make test-backend-coverage
```
- Includes coverage reporting
- Identifies untested code paths
- Generates coverage reports

**All Tests (Complete Suite):**
```bash
make test-all
```
- Backend + frontend tests with coverage
- Full validation before commits

### Specialized Test Categories

**Framework Tests:**
```bash
make test-framework
```
- Core linting framework functionality
- Base classes and utilities

**Rule Tests:**
```bash
make test-rules
```
- All individual linting rules
- Magic numbers, SRP, logging, etc.

**Specific Components:**
```bash
make test-component COMPONENT=test/unit_test/tools/design_linters/test_basic.py
```

## Specific Test Execution

### Design Linter Framework Tests
```bash
# All design linter tests
PYTHONPATH=/home/stevejackson/Projects/durable-code-test/tools python -m pytest test/unit_test/tools/design_linters/ -v

# Specific test files
PYTHONPATH=/home/stevejackson/Projects/durable-code-test/tools python -m pytest test/unit_test/tools/design_linters/test_basic.py -v

# Specific test classes/methods
PYTHONPATH=/home/stevejackson/Projects/durable-code-test/tools python -m pytest test/unit_test/tools/design_linters/test_basic.py::TestIgnoreFunctionality -v
```

### Individual Rule Testing
```bash
# Magic number rules
PYTHONPATH=/home/stevejackson/Projects/durable-code-test/tools python -m pytest test/unit_test/tools/design_linters/test_magic_number_rules.py -v

# SRP rules
PYTHONPATH=/home/stevejackson/Projects/durable-code-test/tools python -m pytest test/unit_test/tools/design_linters/test_srp_rules.py -v

# Loguru rules
PYTHONPATH=/home/stevejackson/Projects/durable-code-test/tools python -m pytest test/unit_test/tools/design_linters/test_loguru_rules.py -v
```

## Test Output Interpretation

### Success Output
```
===== test session starts =====
collected X items

test_file.py::test_function PASSED [100%]

===== X passed in Y.YYs =====
```

### Failure Output
```
===== FAILURES =====
____________ test_function ____________

    def test_function():
>       assert False
E       assert False

test_file.py:10: AssertionError
```

### Coverage Output
```
Name                    Stmts   Miss  Cover
-------------------------------------------
module.py                 20      2    90%
-------------------------------------------
TOTAL                     20      2    90%
```

## Common Test Scenarios

### Running Tests for New Features
1. **Create feature code**
2. **Run affected tests**: `make test-unit`
3. **Check coverage**: `make test-coverage`
4. **Run full suite**: `make test`

### Debugging Test Failures
```bash
# Verbose output with detailed errors
PYTHONPATH=/home/stevejackson/Projects/durable-code-test/tools python -m pytest test/path/to/test.py -v -s

# Stop on first failure
PYTHONPATH=/home/stevejackson/Projects/durable-code-test/tools python -m pytest test/path/to/test.py -x

# Run specific failing test
PYTHONPATH=/home/stevejackson/Projects/durable-code-test/tools python -m pytest test/path/to/test.py::TestClass::test_method -v
```

### Performance Testing
```bash
# Run with timing information
PYTHONPATH=/home/stevejackson/Projects/durable-code-test/tools python -m pytest test/ --durations=10

# Memory profiling (if pytest-memprof installed)
PYTHONPATH=/home/stevejackson/Projects/durable-code-test/tools python -m pytest test/ --memprof
```

## Test Configuration

### pytest Configuration
**Location**: `pyproject.toml` or `pytest.ini`
**Key Settings**:
- Test discovery patterns
- Coverage configuration
- Output formatting
- Parallel execution settings

### Environment Variables
```bash
# Python path for module discovery
PYTHONPATH=/home/stevejackson/Projects/durable-code-test/tools

# Test environment configuration
TEST_ENV=true
```

## Continuous Integration

### Pre-commit Testing
**Location**: `.pre-commit-config.yaml`
- Automatic test execution on commit
- Fast subset of critical tests
- Quality gate enforcement

### GitHub Actions
**Location**: `.github/workflows/`
- Full test suite on PR
- Multi-environment testing
- Coverage reporting integration

## Test File Organization

### Structure
```
test/
├── unit_test/
│   └── tools/
│       └── design_linters/
│           ├── test_basic.py           # Core framework tests
│           ├── test_magic_number_rules.py  # Literal analysis
│           ├── test_loguru_rules.py    # Logging rules
│           ├── test_srp_rules.py       # SOLID principles
│           ├── test_nesting_rules.py   # Code complexity
│           └── test_print_statement_rules.py  # Style rules
```

### Test Categories
- **Framework Tests**: Core linting framework functionality
- **Rule Tests**: Individual rule behavior validation
- **Integration Tests**: End-to-end workflow testing
- **Performance Tests**: Execution speed and resource usage

## Troubleshooting

### Common Issues

**ModuleNotFoundError**:
```bash
# Ensure PYTHONPATH is set correctly
export PYTHONPATH=/home/stevejackson/Projects/durable-code-test/tools
```

**Docker Permission Issues**:
```bash
# Use make targets instead of direct Docker commands
make test  # Instead of docker-compose exec
```

**Test Database Issues**:
```bash
# Clean and rebuild test environment
make clean
make test
```

### Debug Mode
```bash
# Run with Python debugger
PYTHONPATH=/home/stevejackson/Projects/durable-code-test/tools python -m pytest test/path/to/test.py --pdb

# Capture output (disable capture)
PYTHONPATH=/home/stevejackson/Projects/durable-code-test/tools python -m pytest test/path/to/test.py -s
```

## Best Practices

### Before Committing
1. **Check available commands**: `make help`
2. **Run unit tests**: `make test-backend-quick`
3. **Check coverage**: `make test-backend-coverage`
4. **Run linting**: `make lint-all`
5. **Full validation**: `make test-all`

### Test Development
1. **Write tests first** (TDD approach)
2. **Use descriptive test names**
3. **Follow AAA pattern** (Arrange, Act, Assert)
4. **Test edge cases and error conditions**
5. **Mock external dependencies**

### Performance Considerations
- **Use Docker** for consistent environments
- **Run subset tests** during development
- **Full test suite** before commits
- **Parallel execution** for large test suites
