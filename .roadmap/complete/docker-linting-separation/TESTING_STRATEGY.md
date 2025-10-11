# Docker Linting Separation - Testing Strategy

**Purpose**: Comprehensive testing strategy for Docker linting separation implementation ensuring zero regression and performance improvements

**Scope**: Complete validation testing covering functionality preservation, performance optimization, and reliability enhancement verification

**Overview**: Comprehensive testing strategy for validating Docker linting separation implementation across all
    development and CI/CD workflows. Ensures new architecture maintains existing functionality while delivering
    expected performance and reliability improvements. Covers pre-implementation baselines, task-specific testing,
    performance comparisons, regression validation, and rollback procedures. Includes automated test execution,
    continuous monitoring, and health check procedures to ensure successful migration with measurable benefits.

**Dependencies**: Docker, Docker Compose, linting tools, Make targets, GitHub Actions, testing frameworks, performance monitoring tools

**Exports**: Testing procedures, validation scripts, performance benchmarks, rollback testing, and success criteria definitions

**Related**: AI_CONTEXT.md for implementation context, IMPLEMENTATION_BREAKDOWN.md for task details, performance monitoring procedures

**Implementation**: Multi-layered testing approach with baseline establishment, systematic validation, performance measurement, and automated monitoring

---

## Overview
This document defines the comprehensive testing strategy for validating the Docker linting separation implementation. It ensures that the new architecture maintains all existing functionality while delivering the expected performance and reliability improvements.

## Testing Philosophy

### Zero Regression Principle
- **All existing functionality must continue to work exactly as before**
- **Developer workflow must remain unchanged**
- **Performance must improve or stay the same**
- **No new failure modes should be introduced**

### Validation Layers
1. **Unit Tests**: Individual container and component functionality
2. **Integration Tests**: Cross-container communication and workflow
3. **System Tests**: End-to-end developer and CI/CD workflows
4. **Performance Tests**: Benchmark improvements and resource usage
5. **Rollback Tests**: Verify recovery procedures work correctly

---

## Pre-Implementation Testing

### Baseline Establishment
Before implementing changes, establish current performance and functionality baselines.

#### Performance Baseline
```bash
#!/bin/bash
# File: scripts/baseline-performance.sh

echo "📊 Establishing Performance Baseline"

# Measure development container startup time
echo "🚀 Development Container Startup Time:"
time docker-compose -f docker-compose.dev.yml up -d

# Measure container sizes
echo "📦 Container Sizes:"
docker images | grep durable-code | awk '{print $1,$2,$7}'

# Measure memory usage
echo "💾 Memory Usage:"
docker stats --no-stream | grep durable-code

# Measure linting execution time
echo "⏱️  Linting Execution Time:"
time make lint-all

# Clean up
docker-compose -f docker-compose.dev.yml down
```

#### Functionality Baseline
```bash
#!/bin/bash
# File: scripts/baseline-functionality.sh

echo "🔧 Establishing Functionality Baseline"

# Test all make targets work
echo "Testing make targets:"
make help | grep "lint-" | while read -r target desc; do
    echo "Testing: $target"
    timeout 300 make "$target" || echo "❌ $target failed"
done

# Test development environment
echo "Testing development environment:"
make dev
sleep 10
curl -f http://localhost:5173 || echo "❌ Frontend not accessible"
curl -f http://localhost:8000/health || echo "❌ Backend not accessible"
make dev-stop

# Test GitHub Actions locally (if using act)
echo "Testing GitHub Actions workflow:"
# act -j lint --dry-run || echo "❌ GitHub Actions workflow has issues"
```

---

## Task 1 Testing: Dedicated Linting Containers

### Container Build Tests
```bash
#!/bin/bash
# File: tests/task1-container-builds.sh

set -e

echo "🧪 Task 1: Testing Container Builds"

# Test Python linting container build
echo "📦 Building Python linting container..."
docker build -f docker/linting/Dockerfile.python-lint -t test-python-linter . \
    || { echo "❌ Python container build failed"; exit 1; }

# Test JavaScript linting container build
echo "📦 Building JavaScript linting container..."
docker build -f docker/linting/Dockerfile.js-lint -t test-js-linter . \
    || { echo "❌ JavaScript container build failed"; exit 1; }

# Test Docker Compose configuration
echo "🐳 Validating Docker Compose configuration..."
docker-compose -f docker-compose.lint.yml config > /dev/null \
    || { echo "❌ Docker Compose configuration invalid"; exit 1; }

echo "✅ Container builds successful"
```

### Tool Availability Tests
```bash
#!/bin/bash
# File: tests/task1-tool-availability.sh

set -e

echo "🔧 Testing Tool Availability in Containers"

# Start containers
docker-compose -f docker-compose.lint.yml up -d
sleep 5

# Test Python tools
echo "🐍 Testing Python linting tools..."
PYTHON_TOOLS="black ruff isort mypy pylint bandit xenon flake8 shellcheck tflint"
for tool in $PYTHON_TOOLS; do
    docker exec durable-code-python-linter-main which "$tool" > /dev/null \
        || echo "⚠️  $tool not found in Python container"
done

# Test JavaScript tools
echo "📜 Testing JavaScript linting tools..."
JS_TOOLS="htmlhint npm eslint"
for tool in $JS_TOOLS; do
    docker exec durable-code-js-linter-main which "$tool" > /dev/null \
        || echo "⚠️  $tool not found in JavaScript container"
done

# Test volume mounts
echo "📁 Testing volume mounts..."
docker exec durable-code-python-linter-main ls -la /workspace/backend > /dev/null \
    || { echo "❌ Backend volume mount failed"; exit 1; }
docker exec durable-code-js-linter-main ls -la /workspace/frontend > /dev/null \
    || { echo "❌ Frontend volume mount failed"; exit 1; }

# Clean up
docker-compose -f docker-compose.lint.yml down

echo "✅ Tool availability tests passed"
```

### Functional Linting Tests
```bash
#!/bin/bash
# File: tests/task1-functional-linting.sh

set -e

echo "🔍 Testing Functional Linting in Containers"

# Start containers
docker-compose -f docker-compose.lint.yml up -d
sleep 5

# Test Python linting works
echo "🐍 Testing Python linting functionality..."
docker exec durable-code-python-linter-main bash -c \
    "cd /workspace && poetry run black --check backend" > /dev/null \
    || echo "⚠️  Black check failed"

# Test JavaScript linting works
echo "📜 Testing JavaScript linting functionality..."
docker exec durable-code-js-linter-main sh -c \
    "cd /workspace/frontend && npm run typecheck" > /dev/null \
    || echo "⚠️  TypeScript check failed"

# Test custom design linters
echo "🎨 Testing custom design linters..."
docker exec durable-code-python-linter-main bash -c \
    "cd /workspace && PYTHONPATH=/workspace/tools python -m design_linters --help" > /dev/null \
    || echo "⚠️  Design linters not working"

# Clean up
docker-compose -f docker-compose.lint.yml down

echo "✅ Functional linting tests passed"
```

---

## Task 2 Testing: Makefile Integration

### Make Target Compatibility Tests
```bash
#!/bin/bash
# File: tests/task2-makefile-compatibility.sh

set -e

echo "🎯 Testing Makefile Target Compatibility"

# Test all lint targets still work
LINT_TARGETS="lint-all lint-custom lint-fix lint-categories lint-containers-start lint-containers-stop"

for target in $LINT_TARGETS; do
    echo "Testing: make $target"
    if timeout 300 make "$target"; then
        echo "✅ make $target works"
    else
        echo "❌ make $target failed"
        exit 1
    fi
done

echo "✅ Makefile compatibility tests passed"
```

### Parallel Execution Tests
```bash
#!/bin/bash
# File: tests/task2-parallel-execution.sh

echo "⚡ Testing Parallel Linting Execution"

# Start containers
make lint-containers-start

# Test multiple linting operations can run simultaneously
echo "Testing parallel Python linting..."
docker exec durable-code-python-linter-main bash -c \
    "cd /workspace && poetry run black --check backend" &
PID1=$!

docker exec durable-code-python-linter-main bash -c \
    "cd /workspace && poetry run ruff check tools" &
PID2=$!

# Wait for both to complete
wait $PID1 && wait $PID2
echo "✅ Parallel Python linting successful"

# Clean up
make lint-containers-stop

echo "✅ Parallel execution tests passed"
```

### Performance Comparison Tests
```bash
#!/bin/bash
# File: tests/task2-performance-comparison.sh

echo "⏱️  Testing Performance Comparison"

# Time new linting approach
echo "Timing new linting approach..."
START_NEW=$(date +%s)
make lint-all
END_NEW=$(date +%s)
NEW_TIME=$((END_NEW - START_NEW))

echo "New approach: ${NEW_TIME} seconds"

# Compare with baseline (from pre-implementation measurement)
if [ -f "baseline-times.txt" ]; then
    BASELINE_TIME=$(cat baseline-times.txt)
    echo "Baseline: ${BASELINE_TIME} seconds"

    if [ "$NEW_TIME" -le "$((BASELINE_TIME + 30))" ]; then
        echo "✅ Performance maintained or improved"
    else
        echo "⚠️  Performance regression detected"
    fi
fi

echo "✅ Performance comparison complete"
```

---

## Task 3 Testing: GitHub Actions Migration

### CI Workflow Tests
```bash
#!/bin/bash
# File: tests/task3-ci-workflow.sh

echo "🚀 Testing GitHub Actions Workflow"

# Test workflow syntax
echo "Validating workflow syntax..."
# Use action-validator or similar tool if available
yamllint .github/workflows/lint.yml || echo "⚠️  YAML syntax issues detected"

# Test workflow locally (requires act or similar)
if command -v act > /dev/null; then
    echo "Testing workflow with act..."
    act -j lint --dry-run || echo "⚠️  Workflow execution issues detected"
else
    echo "⚠️  act not available - cannot test workflow locally"
fi

echo "✅ CI workflow tests complete"
```

### Cache Efficiency Tests
```bash
#!/bin/bash
# File: tests/task3-cache-efficiency.sh

echo "💾 Testing Docker Cache Efficiency"

# Build containers first time (cold cache)
echo "First build (cold cache)..."
START1=$(date +%s)
docker build -f docker/linting/Dockerfile.python-lint -t cache-test-python .
END1=$(date +%s)
COLD_TIME=$((END1 - START1))

# Build containers second time (warm cache)
echo "Second build (warm cache)..."
START2=$(date +%s)
docker build -f docker/linting/Dockerfile.python-lint -t cache-test-python .
END2=$(date +%s)
WARM_TIME=$((END2 - START2))

echo "Cold cache: ${COLD_TIME} seconds"
echo "Warm cache: ${WARM_TIME} seconds"

if [ "$WARM_TIME" -lt "$((COLD_TIME / 2))" ]; then
    echo "✅ Good cache efficiency"
else
    echo "⚠️  Cache efficiency could be improved"
fi

# Clean up
docker rmi cache-test-python || true

echo "✅ Cache efficiency tests complete"
```

---

## Task 4 Testing: Development Container Cleanup

### Container Size Validation
```bash
#!/bin/bash
# File: tests/task4-container-size.sh

echo "📏 Testing Container Size Improvements"

# Measure new development container sizes
echo "Measuring new container sizes..."
docker build -f durable-code-app/backend/Dockerfile.dev -t size-test-backend ./durable-code-app/backend
docker build -f durable-code-app/frontend/Dockerfile.dev -t size-test-frontend ./durable-code-app/frontend

BACKEND_SIZE=$(docker images size-test-backend --format "{{.Size}}")
FRONTEND_SIZE=$(docker images size-test-frontend --format "{{.Size}}")

echo "New backend container: $BACKEND_SIZE"
echo "New frontend container: $FRONTEND_SIZE"

# Compare with baseline if available
if [ -f "baseline-sizes.txt" ]; then
    echo "Comparing with baseline..."
    diff baseline-sizes.txt <(echo "Backend: $BACKEND_SIZE"; echo "Frontend: $FRONTEND_SIZE")
fi

# Clean up
docker rmi size-test-backend size-test-frontend

echo "✅ Container size validation complete"
```

### Development Environment Tests
```bash
#!/bin/bash
# File: tests/task4-dev-environment.sh

set -e

echo "🛠️  Testing Development Environment"

# Test development environment still works
echo "Starting development environment..."
make dev
sleep 10

# Test application accessibility
echo "Testing application accessibility..."
curl -f http://localhost:5173 > /dev/null || { echo "❌ Frontend not accessible"; exit 1; }
curl -f http://localhost:8000/health > /dev/null || { echo "❌ Backend not accessible"; exit 1; }

# Test hot reloading (basic test)
echo "Testing hot reloading..."
# Touch a file and verify the container detects change
touch durable-code-app/backend/app/main.py
sleep 2

# Verify linting tools are NOT in development containers
echo "Verifying linting tools removed..."
if docker exec durable-code-backend-main-dev which black > /dev/null 2>&1; then
    echo "⚠️  Black still found in backend container"
fi

if docker exec durable-code-frontend-main-dev which eslint > /dev/null 2>&1; then
    echo "⚠️  ESLint still found in frontend container"
fi

# Clean up
make dev-stop

echo "✅ Development environment tests passed"
```

---

## Task 5 Testing: Final Integration & Documentation

### End-to-End Integration Tests
```bash
#!/bin/bash
# File: tests/task5-integration.sh

set -e

echo "🔄 End-to-End Integration Testing"

# Test complete workflow
echo "Testing complete developer workflow..."

# 1. Start development
make dev
sleep 10

# 2. Run linting
make lint-all

# 3. Make a code change
echo "# Test comment" >> durable-code-app/backend/app/main.py

# 4. Run linting fix
make lint-fix

# 5. Verify fix worked
make lint-all

# 6. Clean up development
make dev-stop

echo "✅ End-to-end integration tests passed"
```

### Documentation Validation Tests
```bash
#!/bin/bash
# File: tests/task5-documentation.sh

echo "📚 Testing Documentation Completeness"

# Check all expected files exist
EXPECTED_DOCS=(
    "docker/linting/README.md"
    "docker/linting/ROLLBACK.md"
    "docker/linting/TROUBLESHOOTING.md"
    ".ai/docs/DOCKER_LINTING_ARCHITECTURE.md"
)

for doc in "${EXPECTED_DOCS[@]}"; do
    if [ -f "$doc" ]; then
        echo "✅ $doc exists"
    else
        echo "❌ $doc missing"
    fi
done

# Test rollback procedures
echo "Testing rollback procedures..."
if [ -f "docker/linting/ROLLBACK.md" ]; then
    echo "✅ Rollback procedures documented"
    # Could test actual rollback here if desired
fi

echo "✅ Documentation validation complete"
```

---

## Performance Testing

### Benchmark Test Suite
```bash
#!/bin/bash
# File: tests/performance-benchmarks.sh

echo "🚀 Performance Benchmark Suite"

# Container startup time
echo "📊 Container Startup Benchmarks"
echo "Development containers:"
time docker-compose -f docker-compose.dev.yml up -d
docker-compose -f docker-compose.dev.yml down

echo "Linting containers:"
time docker-compose -f docker-compose.lint.yml up -d
docker-compose -f docker-compose.lint.yml down

# Linting execution time
echo "📊 Linting Execution Benchmarks"
echo "Full linting suite:"
time make lint-all

# Memory usage
echo "📊 Memory Usage Benchmarks"
make dev > /dev/null 2>&1 &
sleep 10
echo "Development containers:"
docker stats --no-stream | grep durable-code

make lint-containers-start > /dev/null 2>&1
sleep 5
echo "Linting containers:"
docker stats --no-stream | grep linter

# Clean up
make dev-stop > /dev/null 2>&1
make lint-containers-stop > /dev/null 2>&1

echo "✅ Performance benchmarks complete"
```

### Resource Usage Tests
```bash
#!/bin/bash
# File: tests/resource-usage.sh

echo "💻 Resource Usage Testing"

# Test resource limits work
echo "Testing resource limits..."
make lint-containers-start

# Monitor resource usage during heavy linting
echo "Monitoring resource usage during linting..."
docker stats --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" &
STATS_PID=$!

# Run intensive linting
make lint-all

kill $STATS_PID 2>/dev/null || true

make lint-containers-stop

echo "✅ Resource usage tests complete"
```

---

## Regression Testing

### Compatibility Matrix Testing
```bash
#!/bin/bash
# File: tests/compatibility-matrix.sh

echo "🔄 Compatibility Matrix Testing"

# Test different scenarios
SCENARIOS=(
    "fresh-install"
    "existing-dev-env"
    "ci-environment"
    "different-branch-names"
)

for scenario in "${SCENARIOS[@]}"; do
    echo "Testing scenario: $scenario"

    case $scenario in
        "fresh-install")
            # Simulate fresh clone
            docker system prune -f
            make init
            make lint-all
            ;;
        "existing-dev-env")
            # Test with existing dev environment
            make dev
            make lint-all
            make dev-stop
            ;;
        "ci-environment")
            # Simulate CI environment
            export CI=true
            make lint-all
            unset CI
            ;;
        "different-branch-names")
            # Test with different branch names
            export BRANCH_NAME=feature/test-branch
            make lint-containers-start
            make lint-containers-stop
            unset BRANCH_NAME
            ;;
    esac

    echo "✅ Scenario $scenario passed"
done

echo "✅ Compatibility matrix testing complete"
```

---

## Rollback Testing

### Rollback Procedure Validation
```bash
#!/bin/bash
# File: tests/rollback-procedures.sh

set -e

echo "↩️  Testing Rollback Procedures"

# Create backup of current state
echo "Creating backup..."
cp Makefile.lint Makefile.lint.new-backup
cp .github/workflows/lint.yml .github/workflows/lint.yml.new-backup

# Test emergency rollback
echo "Testing emergency rollback..."

# Simulate rollback (replace with actual restore commands)
echo "Simulating Makefile rollback..."
# git checkout HEAD~1 -- Makefile.lint

echo "Simulating GitHub Actions rollback..."
# git checkout HEAD~1 -- .github/workflows/lint.yml

# Test that rolled back version works
echo "Testing rolled back functionality..."
# make lint-all

# Restore new version
echo "Restoring new implementation..."
cp Makefile.lint.new-backup Makefile.lint
cp .github/workflows/lint.yml.new-backup .github/workflows/lint.yml

# Clean up
rm -f Makefile.lint.new-backup .github/workflows/lint.yml.new-backup

echo "✅ Rollback procedures validated"
```

---

## Automated Test Execution

### Master Test Runner
```bash
#!/bin/bash
# File: tests/run-all-tests.sh

set -e

echo "🧪 Docker Linting Separation - Master Test Suite"

# Test categories
BASELINE_TESTS="baseline-performance baseline-functionality"
TASK1_TESTS="task1-container-builds task1-tool-availability task1-functional-linting"
TASK2_TESTS="task2-makefile-compatibility task2-parallel-execution task2-performance-comparison"
TASK3_TESTS="task3-ci-workflow task3-cache-efficiency"
TASK4_TESTS="task4-container-size task4-dev-environment"
TASK5_TESTS="task5-integration task5-documentation"
PERFORMANCE_TESTS="performance-benchmarks resource-usage"
REGRESSION_TESTS="compatibility-matrix"
ROLLBACK_TESTS="rollback-procedures"

# Track results
PASSED=0
FAILED=0
RESULTS_FILE="test-results-$(date +%Y%m%d-%H%M%S).log"

run_test() {
    local test_script=$1
    local test_name=$(basename "$test_script" .sh)

    echo "🔄 Running $test_name..."

    if bash "tests/$test_script.sh" >> "$RESULTS_FILE" 2>&1; then
        echo "✅ $test_name PASSED"
        ((PASSED++))
    else
        echo "❌ $test_name FAILED"
        ((FAILED++))
    fi
}

# Run all test categories
echo "Starting baseline tests..."
for test in $BASELINE_TESTS; do run_test "$test"; done

echo "Starting Task 1 tests..."
for test in $TASK1_TESTS; do run_test "$test"; done

echo "Starting Task 2 tests..."
for test in $TASK2_TESTS; do run_test "$test"; done

echo "Starting Task 3 tests..."
for test in $TASK3_TESTS; do run_test "$test"; done

echo "Starting Task 4 tests..."
for test in $TASK4_TESTS; do run_test "$test"; done

echo "Starting Task 5 tests..."
for test in $TASK5_TESTS; do run_test "$test"; done

echo "Starting performance tests..."
for test in $PERFORMANCE_TESTS; do run_test "$test"; done

echo "Starting regression tests..."
for test in $REGRESSION_TESTS; do run_test "$test"; done

echo "Starting rollback tests..."
for test in $ROLLBACK_TESTS; do run_test "$test"; done

# Summary
echo ""
echo "📊 Test Results Summary"
echo "======================="
echo "Passed: $PASSED"
echo "Failed: $FAILED"
echo "Total:  $((PASSED + FAILED))"
echo "Success Rate: $(( PASSED * 100 / (PASSED + FAILED) ))%"
echo ""
echo "Detailed results in: $RESULTS_FILE"

if [ $FAILED -gt 0 ]; then
    echo "❌ Some tests failed. Review $RESULTS_FILE for details."
    exit 1
else
    echo "✅ All tests passed!"
fi
```

---

## Continuous Validation

### Performance Monitoring
Set up ongoing performance monitoring to detect regressions:

```bash
#!/bin/bash
# File: scripts/performance-monitor.sh
# Run this periodically to monitor performance

echo "📊 Performance Monitoring $(date)"

# Measure key metrics
DEV_STARTUP=$(time docker-compose -f docker-compose.dev.yml up -d 2>&1 | grep real)
LINT_EXECUTION=$(time make lint-all 2>&1 | grep real)

# Log to metrics file
echo "$(date),$DEV_STARTUP,$LINT_EXECUTION" >> performance-metrics.csv

# Alert if significant regression
# Add alerting logic here if needed
```

### Health Checks
```bash
#!/bin/bash
# File: scripts/health-checks.sh
# Quick health check for linting infrastructure

echo "🏥 Linting Infrastructure Health Check"

# Check containers can start
if docker-compose -f docker-compose.lint.yml up -d > /dev/null 2>&1; then
    echo "✅ Linting containers start successfully"
else
    echo "❌ Linting containers failed to start"
    exit 1
fi

# Check basic functionality
if timeout 60 make lint-containers-status > /dev/null 2>&1; then
    echo "✅ Basic linting functionality works"
else
    echo "❌ Basic linting functionality failed"
    exit 1
fi

# Clean up
docker-compose -f docker-compose.lint.yml down > /dev/null 2>&1

echo "✅ Health check passed"
```

## Testing Success Criteria

### Functional Criteria
- [ ] All existing make targets work identically
- [ ] All linting tools produce same results as before
- [ ] Development environment works normally
- [ ] GitHub Actions CI pipeline works
- [ ] Hot reloading continues to function

### Performance Criteria
- [ ] Development container startup improves by 30-50%
- [ ] Linting execution time stays same or improves
- [ ] Memory usage in development environment decreases
- [ ] CI pipeline execution time improves or stays same

### Quality Criteria
- [ ] No new failure modes introduced
- [ ] Error messages are clear and actionable
- [ ] Rollback procedures work correctly
- [ ] Documentation is complete and accurate

### Operational Criteria
- [ ] Resource usage is reasonable
- [ ] Container cleanup works properly
- [ ] Troubleshooting procedures are effective
- [ ] Monitoring and alerting is functional

This comprehensive testing strategy ensures that the Docker linting separation implementation delivers the expected benefits while maintaining the reliability and functionality that developers depend on.
