#!/bin/bash
# Purpose: Validates local environment matches CI/CD pipeline requirements
# Scope: Pre-push validation for all automated checks that run in GitHub Actions
# Overview: Comprehensive validation script that runs the same checks locally as configured in CI/CD pipelines.
#           Includes breadcrumb navigation checks, Single Responsibility Principle analysis, print statement detection,
#           magic number detection, file placement validation, header standards compliance, and backend tests.
#           Provides detailed pass/fail reporting to ensure code readiness before pushing to remote repositories.
# Dependencies: python3, docker, design linter tools (breadcrumb_linter.py, srp_analyzer.py, print_statement_linter.py, magic_number_detector.py, file_placement_linter.py, header_linter.py), pytest
# Usage: ./scripts/ci-cd-parity-check.sh (runs all CI/CD checks locally)
# Interfaces: Python design linter tools, Docker container execution, and file system validation
# Implementation: Sequential check execution with colored output, summary reporting, and exit code handling for CI integration

# CI/CD Parity Check Script
# Ensures local checks match what will run in CI/CD

set -e

echo "=== CI/CD Parity Check ==="
echo "Running the same checks that will run in GitHub Actions..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

FAILED_CHECKS=()
PASSED_CHECKS=()

# Function to run a check
run_check() {
    local name="$1"
    local command="$2"

    echo -n "Running: $name ... "
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        PASSED_CHECKS+=("$name")
    else
        echo -e "${RED}✗${NC}"
        FAILED_CHECKS+=("$name")
    fi
}

# Check 1: Breadcrumb Linter (from breadcrumb-check.yml)
if [ -f "tools/design_linters/breadcrumb_linter.py" ]; then
    run_check "Breadcrumb Navigation Check" "python tools/design_linters/breadcrumb_linter.py"
else
    echo -e "${RED}✗ Breadcrumb linter not found at tools/design_linters/breadcrumb_linter.py${NC}"
    FAILED_CHECKS+=("Breadcrumb Navigation Check")
fi

# Check 2: SRP Analyzer (from design-check.yml)
if [ -f "tools/design_linters/srp_analyzer.py" ]; then
    run_check "Single Responsibility Principle" "python tools/design_linters/srp_analyzer.py durable-code-app --threshold normal"
else
    echo -e "${RED}✗ SRP analyzer not found at tools/design_linters/srp_analyzer.py${NC}"
    FAILED_CHECKS+=("Single Responsibility Principle")
fi

# Check 3: Print Statement Linter (from justfile)
if [ -f "tools/design_linters/print_statement_linter.py" ]; then
    run_check "Print Statement Check" "python tools/design_linters/print_statement_linter.py --path . --recursive --no-skip-tests"
else
    echo -e "${RED}✗ Print statement linter not found at tools/design_linters/print_statement_linter.py${NC}"
    FAILED_CHECKS+=("Print Statement Check")
fi

# Check 4: Magic Number Detector (from design-check.yml)
if [ -f "tools/design_linters/magic_number_detector.py" ]; then
    run_check "Magic Number Detection" "python tools/design_linters/magic_number_detector.py durable-code-app --threshold normal"
else
    echo -e "${RED}✗ Magic number detector not found at tools/design_linters/magic_number_detector.py${NC}"
    FAILED_CHECKS+=("Magic Number Detection")
fi

# Check 5: File Placement Linter (from justfile.design)
if [ -f "tools/design_linters/file_placement_linter.py" ]; then
    run_check "File Placement Check" "python tools/design_linters/file_placement_linter.py"
else
    echo -e "${RED}✗ File placement linter not found at tools/design_linters/file_placement_linter.py${NC}"
    FAILED_CHECKS+=("File Placement Check")
fi

# Check 6: Header Linter (from justfile.design)
if [ -f "tools/design_linters/header_linter.py" ]; then
    run_check "Header Standards Check" "python tools/design_linters/header_linter.py"
else
    echo -e "${RED}✗ Header linter not found at tools/design_linters/header_linter.py${NC}"
    FAILED_CHECKS+=("Header Standards Check")
fi

# Check 7: Backend tests (should pass)
echo -n "Running: Backend Tests ... "
if docker exec -u appuser durable-code-backend-dev bash -c "cd /tmp && PYTHONPATH=/app/tools/design_linters:/app/tools pytest /app/test -q" > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
    PASSED_CHECKS+=("Backend Tests")
else
    echo -e "${RED}✗${NC}"
    FAILED_CHECKS+=("Backend Tests")
fi

echo ""
echo "=== Summary ==="
echo -e "${GREEN}Passed: ${#PASSED_CHECKS[@]} checks${NC}"
if [ ${#PASSED_CHECKS[@]} -gt 0 ]; then
    for check in "${PASSED_CHECKS[@]}"; do
        echo "  ✓ $check"
    done
fi

echo ""
if [ ${#FAILED_CHECKS[@]} -gt 0 ]; then
    echo -e "${RED}Failed: ${#FAILED_CHECKS[@]} checks${NC}"
    for check in "${FAILED_CHECKS[@]}"; do
        echo "  ✗ $check"
    done
    echo ""
    echo -e "${YELLOW}These checks will fail in CI/CD!${NC}"
    echo "Please fix them before pushing."
    exit 1
else
    echo -e "${GREEN}All checks pass! Safe to push.${NC}"
fi
