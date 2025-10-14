# Purpose: Task automation for Durable Code Test project
# Scope: Development, testing, linting, deployment, and infrastructure management
# Overview: Consolidated task runner replacing 1,075 lines of Makefiles with ~450 lines of cleaner Just recipes.
#     Provides Docker-based development workflows with hot reload, comprehensive linting and testing,
#     and infrastructure-as-code management through Docker-containerized Terraform. All operations run
#     in isolated containers to eliminate local tool dependencies.
# Dependencies: Docker, Just, AWS credentials (for infra operations)
# Exports: Development, testing, linting, deployment, and infrastructure management commands
# Interfaces: CLI via `just <recipe>` - run `just` or `just --list` to see all commands
# Implementation: Uses Just's native features (parameters, conditionals) for cleaner syntax than Make

# Configuration
set shell := ["bash", "-c"]
set dotenv-load := true

# Variables
BRANCH_NAME := `git rev-parse --abbrev-ref HEAD 2>/dev/null | tr '/' '-' | tr '[:upper:]' '[:lower:]' || echo "main"`
FRONTEND_PORT := `./scripts/get-branch-ports.sh "$BRANCH_NAME" export 2>/dev/null | grep FRONTEND_PORT | cut -d= -f2 || echo "5173"`
BACKEND_PORT := `./scripts/get-branch-ports.sh "$BRANCH_NAME" export 2>/dev/null | grep BACKEND_PORT | cut -d= -f2 || echo "8000"`
COMPOSE_CMD := `which docker-compose 2>/dev/null || echo "docker compose"`
FRONTEND_URL := "http://localhost:" + FRONTEND_PORT
BACKEND_URL := "http://localhost:" + BACKEND_PORT

# Terraform configuration
TERRAFORM_VERSION := "1.9.8"
AWS_REGION := env_var_or_default("AWS_REGION", "us-west-2")
AWS_PROFILE := env_var_or_default("AWS_PROFILE", "terraform-deploy")
ENV := env_var_or_default("ENV", "dev")

# Colors for output
CYAN := '\033[0;36m'
GREEN := '\033[0;32m'
YELLOW := '\033[0;33m'
RED := '\033[0;31m'
NC := '\033[0m'

# Default recipe (shows help)
default:
    @just --list

# Help - show all commands with descriptions
help:
    @echo -e "{{CYAN}}╔════════════════════════════════════════════════════════════╗{{NC}}"
    @echo -e "{{CYAN}}║          Durable Code Test - Task Automation              ║{{NC}}"
    @echo -e "{{CYAN}}╚════════════════════════════════════════════════════════════╝{{NC}}"
    @echo ""
    @echo -e "{{GREEN}}Core Commands:{{NC}}"
    @echo -e "  {{YELLOW}}just dev{{NC}}              # Start development environment"
    @echo -e "  {{YELLOW}}just test{{NC}}             # Run all tests with coverage"
    @echo -e "  {{YELLOW}}just lint{{NC}}             # Run all linters"
    @echo -e "  {{YELLOW}}just deploy{{NC}}           # Deploy application to dev environment"
    @echo ""
    @echo -e "{{GREEN}}Run 'just --list' for all available commands{{NC}}"
    @echo ""

################################################################################
# Development Targets
################################################################################

# Initialize project (build images, install hooks)
init:
    @echo -e "{{CYAN}}Initializing project...{{NC}}"
    @echo -e "{{YELLOW}}Installing pre-commit framework...{{NC}}"
    @pip3 install pre-commit 2>/dev/null || pip install pre-commit 2>/dev/null || echo -e "{{YELLOW}}⚠ Pre-commit not installed{{NC}}"
    @pre-commit install 2>/dev/null || echo -e "{{YELLOW}}⚠ Pre-commit hooks not installed{{NC}}"
    @pre-commit install --hook-type pre-push 2>/dev/null || echo -e "{{YELLOW}}⚠ Pre-push hooks not installed{{NC}}"
    @echo -e "{{YELLOW}}Building Docker images...{{NC}}"
    @BRANCH_NAME={{BRANCH_NAME}} FRONTEND_PORT={{FRONTEND_PORT}} BACKEND_PORT={{BACKEND_PORT}} {{COMPOSE_CMD}} -f .docker/compose/app.yml build --no-cache
    @echo -e "{{GREEN}}✓ Initialization complete!{{NC}}"

# Start development environment
dev-start:
    @echo -e "{{CYAN}}Starting development environment...{{NC}}"
    @BRANCH_NAME={{BRANCH_NAME}} FRONTEND_PORT={{FRONTEND_PORT}} BACKEND_PORT={{BACKEND_PORT}} {{COMPOSE_CMD}} -f .docker/compose/app.yml up -d
    @echo -e "{{GREEN}}✓ Development environment started!{{NC}}"
    @echo -e "{{YELLOW}}Frontend: {{FRONTEND_URL}}{{NC}}"
    @echo -e "{{YELLOW}}Backend: {{BACKEND_URL}}{{NC}}"
    @echo -e "{{YELLOW}}API Docs: {{BACKEND_URL}}/docs{{NC}}"

# Stop development environment
dev-stop:
    @echo -e "{{CYAN}}Stopping development environment...{{NC}}"
    @BRANCH_NAME={{BRANCH_NAME}} FRONTEND_PORT={{FRONTEND_PORT}} BACKEND_PORT={{BACKEND_PORT}} {{COMPOSE_CMD}} -f .docker/compose/app.yml down
    @echo -e "{{GREEN}}✓ Development environment stopped!{{NC}}"

# Restart development environment
dev-restart: dev-stop dev-start

# Show development logs
dev-logs:
    @BRANCH_NAME={{BRANCH_NAME}} FRONTEND_PORT={{FRONTEND_PORT}} BACKEND_PORT={{BACKEND_PORT}} {{COMPOSE_CMD}} -f .docker/compose/app.yml logs -f

# Start dev environment and open browser
dev: dev-start
    #!/usr/bin/env bash
    echo -e "{{CYAN}}Launching browser...{{NC}}"
    sleep 3
    if command -v xdg-open > /dev/null; then
        xdg-open {{FRONTEND_URL}}
    elif command -v open > /dev/null; then
        open {{FRONTEND_URL}}
    elif command -v start > /dev/null; then
        start {{FRONTEND_URL}}
    else
        echo -e "{{YELLOW}}Please open: {{FRONTEND_URL}}{{NC}}"
    fi

# Show container status
status:
    @echo -e "{{CYAN}}Container Status:{{NC}}"
    @docker ps --format "table {{{{.Names}}\t{{{{.Status}}\t{{{{.Ports}}" | grep -E "durable-code|NAMES" || echo -e "{{YELLOW}}No containers running{{NC}}"

# Clean up containers, networks, and volumes
clean:
    @echo -e "{{RED}}⚠️  Warning: This will remove all containers, networks, and volumes!{{NC}}"
    @echo -e "{{YELLOW}}Press Ctrl+C to cancel, or wait 5 seconds...{{NC}}"
    @sleep 5
    @echo -e "{{CYAN}}Cleaning up...{{NC}}"
    @BRANCH_NAME={{BRANCH_NAME}} FRONTEND_PORT={{FRONTEND_PORT}} BACKEND_PORT={{BACKEND_PORT}} {{COMPOSE_CMD}} -f .docker/compose/app.yml down -v --remove-orphans
    @docker system prune -f
    @echo -e "{{GREEN}}✓ Cleanup complete!{{NC}}"

# Open shell in backend container
shell-backend:
    @docker exec -it durable-code-backend-{{BRANCH_NAME}}-dev /bin/bash

# Open shell in frontend container
shell-frontend:
    @docker exec -it durable-code-frontend-{{BRANCH_NAME}}-dev /bin/sh

################################################################################
# Linting Targets
################################################################################

# Ensure linting containers are running
@lint-ensure-containers:
    #!/usr/bin/env bash
    if ! docker ps | grep -q "durable-code-python-linter-{{BRANCH_NAME}}"; then
        echo -e "{{CYAN}}Starting Python linting container...{{NC}}"
        {{COMPOSE_CMD}} -f .docker/compose/lint.yml up -d python-linter
    fi
    if ! docker ps | grep -q "durable-code-js-linter-{{BRANCH_NAME}}"; then
        echo -e "{{CYAN}}Starting JS linting container...{{NC}}"
        {{COMPOSE_CMD}} -f .docker/compose/lint.yml up -d js-linter
    fi
    echo -e "{{GREEN}}✓ Linting containers ready{{NC}}"

# Start dedicated linting containers
lint-start:
    @echo -e "{{CYAN}}Starting linting containers...{{NC}}"
    @{{COMPOSE_CMD}} -f .docker/compose/lint.yml up -d --build
    @echo -e "{{GREEN}}✓ Linting containers started{{NC}}"

# Stop dedicated linting containers
lint-stop:
    @echo -e "{{CYAN}}Stopping linting containers...{{NC}}"
    @{{COMPOSE_CMD}} -f .docker/compose/lint.yml down
    @echo -e "{{GREEN}}✓ Linting containers stopped{{NC}}"

# Run all linters (Python + JS + custom + infra)
lint: lint-ensure-containers
    @echo -e "{{CYAN}}╔════════════════════════════════════════════════════════════╗{{NC}}"
    @echo -e "{{CYAN}}║        Running ALL Linters (Parallel Execution)           ║{{NC}}"
    @echo -e "{{CYAN}}╚════════════════════════════════════════════════════════════╝{{NC}}"
    @echo ""
    @just _lint-python &
    @just _lint-js &
    @just _lint-design &
    @wait
    @just _lint-infra
    @echo ""
    @echo -e "{{GREEN}}✅ ALL linting checks passed!{{NC}}"

# Internal: Python linting
@_lint-python:
    echo -e "{{YELLOW}}━━━ Python Linters ━━━{{NC}}"
    docker exec -u root durable-code-python-linter-{{BRANCH_NAME}} bash -c "cd /workspace/backend && \
        mkdir -p /tmp/.cache/ruff /tmp/.cache/mypy && \
        echo '• Ruff...' && RUFF_CACHE_DIR=/tmp/.cache/ruff ruff format --check app /workspace/tools && RUFF_CACHE_DIR=/tmp/.cache/ruff ruff check app /workspace/tools && \
        echo '• Flake8...' && flake8 app --count 2>/dev/null && flake8 /workspace/tools --config /workspace/tools/.flake8 --count 2>/dev/null && \
        echo '• MyPy...' && MYPY_CACHE_DIR=/tmp/.cache/mypy mypy . && \
        echo '• Pylint...' && pylint app /workspace/tools 2>&1 | tail -3 && \
        echo '• Bandit...' && bandit -r app /workspace/tools -q && \
        echo '• Xenon...' && xenon --max-absolute B --max-modules B --max-average A app"
    echo -e "{{GREEN}}✓ Python linting passed{{NC}}"

# Internal: JavaScript/TypeScript linting
@_lint-js:
    echo -e "{{YELLOW}}━━━ TypeScript/React Linters ━━━{{NC}}"
    docker exec durable-code-js-linter-{{BRANCH_NAME}} sh -c "cd /workspace/frontend && \
        echo '• TypeScript...' && npm run typecheck && \
        echo '• ESLint...' && npm run lint && \
        echo '• Stylelint...' && npm run lint:css && \
        echo '• Prettier...' && npm run format:check && \
        echo '• HTMLHint...' && htmlhint 'public/**/*.html' 'src/**/*.html' '*.html' --config /.htmlhintrc"
    echo -e "{{GREEN}}✓ Frontend linting passed{{NC}}"

# Internal: Custom design linters
@_lint-design:
    echo -e "{{YELLOW}}━━━ Custom Design Linters ━━━{{NC}}"
    docker exec durable-code-python-linter-{{BRANCH_NAME}} bash -c "cd /workspace && \
        echo '• File headers...' && PYTHONPATH=/workspace/tools python -m design_linters --rules style.file-header --format text --recursive --fail-on-error backend tools test && \
        echo '• SOLID principles...' && PYTHONPATH=/workspace/tools python -m design_linters --categories solid --format text --recursive --fail-on-error backend tools && \
        echo '• Style rules...' && PYTHONPATH=/workspace/tools python -m design_linters --categories style --format text --recursive --fail-on-error backend tools test && \
        echo '• Magic literals...' && PYTHONPATH=/workspace/tools python -m design_linters --categories literals --format text --recursive --fail-on-error backend tools test && \
        echo '• Logging practices...' && PYTHONPATH=/workspace/tools python -m design_linters --categories logging --format text --recursive --fail-on-error backend tools test && \
        echo '• Loguru usage...' && PYTHONPATH=/workspace/tools python -m design_linters --categories loguru --format text --recursive --fail-on-error backend tools test && \
        echo '• Security rules...' && PYTHONPATH=/workspace/tools python -m design_linters --categories security --format text --recursive --fail-on-error backend tools test && \
        echo '• Error handling...' && PYTHONPATH=/workspace/tools python -m design_linters --categories error_handling --format text --recursive --fail-on-error backend tools test && \
        echo '• Testing practices...' && PYTHONPATH=/workspace/tools python -m design_linters --categories testing --format text --recursive --fail-on-error test && \
        echo '• Enforcement...' && PYTHONPATH=/workspace/tools python -m design_linters --categories enforcement --format text --recursive --fail-on-error backend tools infra"
    echo -e "{{GREEN}}✓ Custom design linting passed{{NC}}"

# Internal: Infrastructure linting
@_lint-infra:
    echo -e "{{YELLOW}}━━━ Infrastructure Linters ━━━{{NC}}"
    printf '%-30s' "• Terraform format" && (just infra-fmt >/dev/null 2>&1 && echo -e "{{GREEN}}✓{{NC}}" || exit 1)
    printf '%-30s' "• Shellcheck" && docker exec durable-code-python-linter-{{BRANCH_NAME}} bash -c "\
        if command -v shellcheck >/dev/null 2>&1; then \
            for script in /workspace/infra/scripts/*.sh /workspace/scripts/*.sh; do \
                if [ -f \"\$script\" ]; then shellcheck --severity=warning \"\$script\" >/dev/null 2>&1 || exit 1; fi; \
            done; \
            echo -e '{{GREEN}}✓{{NC}}'; \
        fi"
    echo -e "{{GREEN}}✓ Infrastructure linting passed{{NC}}"

# Auto-fix formatting issues
lint-fix: lint-ensure-containers
    @echo -e "{{CYAN}}Auto-fixing code formatting...{{NC}}"
    @echo -e "{{YELLOW}}Fixing Python code...{{NC}}"
    @docker exec -u root durable-code-python-linter-{{BRANCH_NAME}} bash -c "cd /workspace/backend && \
        mkdir -p /tmp/.cache/ruff && \
        RUFF_CACHE_DIR=/tmp/.cache/ruff ruff format app /workspace/tools && \
        RUFF_CACHE_DIR=/tmp/.cache/ruff ruff check --fix app /workspace/tools"
    @echo -e "{{YELLOW}}Fixing TypeScript/React code...{{NC}}"
    @docker exec durable-code-js-linter-{{BRANCH_NAME}} sh -c "cd /workspace/frontend && \
        npm run lint:fix && npm run lint:css:fix && npm run format"
    @echo -e "{{GREEN}}✅ Auto-fix complete!{{NC}}"

# Run custom design linters only
lint-custom: lint-ensure-containers
    @echo -e "{{CYAN}}╔════════════════════════════════════════════════════════════╗{{NC}}"
    @echo -e "{{CYAN}}║                Custom Design Linters                      ║{{NC}}"
    @echo -e "{{CYAN}}╚════════════════════════════════════════════════════════════╝{{NC}}"
    @docker exec durable-code-python-linter-{{BRANCH_NAME}} bash -c "cd /workspace && PYTHONPATH=/workspace/tools python -m design_linters --format text --recursive backend tools test"
    @echo -e "{{GREEN}}✓ Custom linting complete{{NC}}"

# Run thailint only (magic numbers, nesting, SRP, file placement, DRY)
lint-thailint: lint-ensure-containers
    @echo -e "{{CYAN}}╔════════════════════════════════════════════════════════════╗{{NC}}"
    @echo -e "{{CYAN}}║                      Thailint                             ║{{NC}}"
    @echo -e "{{CYAN}}╚════════════════════════════════════════════════════════════╝{{NC}}"
    @docker exec durable-code-python-linter-{{BRANCH_NAME}} bash -c "cd /workspace && echo '• Magic numbers...' && thailint --config /workspace/root/.thailint.yaml magic-numbers backend/app tools && echo '• Nesting depth...' && thailint --config /workspace/root/.thailint.yaml nesting backend/app tools && echo '• Single Responsibility...' && thailint --config /workspace/root/.thailint.yaml srp backend/app tools && echo '• DRY violations...' && thailint --config /workspace/root/.thailint.yaml dry backend/app tools"
    @echo -e "{{GREEN}}✓ Thailint complete{{NC}}"

# Run enforcement linting on specific files
lint-enforcement FILES:
    @just lint-ensure-containers
    @docker exec durable-code-python-linter-{{BRANCH_NAME}} bash -c "cd /workspace && PYTHONPATH=/workspace/tools python -m design_linters --categories enforcement --format text --fail-on-error {{FILES}}"

# List all custom linter categories
lint-categories: lint-ensure-containers
    @echo -e "{{CYAN}}╔════════════════════════════════════════════════════════════╗{{NC}}"
    @echo -e "{{CYAN}}║                 Custom Rule Categories                    ║{{NC}}"
    @echo -e "{{CYAN}}╚════════════════════════════════════════════════════════════╝{{NC}}"
    @docker exec durable-code-python-linter-{{BRANCH_NAME}} bash -c "cd /workspace && PYTHONPATH=/workspace/tools python -m design_linters --list-categories"

################################################################################
# Testing Targets
################################################################################

# Ensure testing containers are running
test-ensure-containers: dev-start
    @echo -e "{{GREEN}}✓ Testing containers ready{{NC}}"

# Run all tests with coverage (REQUIRED BY CI)
test: test-ensure-containers
    @echo -e "{{CYAN}}╔════════════════════════════════════════════════════════════╗{{NC}}"
    @echo -e "{{CYAN}}║                    Running All Tests                      ║{{NC}}"
    @echo -e "{{CYAN}}╚════════════════════════════════════════════════════════════╝{{NC}}"
    @just test-backend-coverage
    @just test-frontend-coverage
    @just test-playwright
    @echo -e "{{GREEN}}✅ All tests completed!{{NC}}"

# Run backend tests with coverage
test-backend: test-ensure-containers
    @echo -e "{{CYAN}}Backend Tests with Coverage{{NC}}"
    @docker exec durable-code-backend-{{BRANCH_NAME}}-dev bash -c "cd /app && PYTHONPATH=/app:/app/tools poetry config virtualenvs.create false && poetry run pytest test/ --cov=app --cov=tools/design_linters --cov-report=term --cov-report=term:skip-covered --tb=short -v"
    @echo -e "{{GREEN}}✓ Backend tests complete{{NC}}"

# Backend coverage alias for CI
test-backend-coverage: test-backend

# Run frontend tests with coverage
test-frontend: test-ensure-containers
    @echo -e "{{CYAN}}Frontend Tests{{NC}}"
    @docker exec durable-code-frontend-{{BRANCH_NAME}}-dev npm run test:run
    @echo -e "{{GREEN}}✓ Frontend tests complete{{NC}}"

# Frontend coverage tests
test-frontend-coverage: test-ensure-containers
    @echo -e "{{CYAN}}Frontend Tests with Coverage{{NC}}"
    @docker exec durable-code-frontend-{{BRANCH_NAME}}-dev npm run test:coverage
    @echo -e "{{GREEN}}✓ Frontend coverage tests complete{{NC}}"

# Build Playwright container
test-playwright-build:
    @echo -e "{{CYAN}}Building Playwright test container...{{NC}}"
    @docker build -f .docker/dockerfiles/Dockerfile.playwright -t playwright-tests test/integration_test/
    @echo -e "{{GREEN}}✓ Playwright container built{{NC}}"

# Run Playwright integration tests
test-playwright: dev-start test-playwright-build
    #!/usr/bin/env bash
    echo -e "{{CYAN}}Running Playwright integration tests...{{NC}}"
    if [ "$CI" = "true" ]; then
        docker run --rm --network compose_durable-network-dev \
            -e PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
            -e BRANCH_NAME="{{BRANCH_NAME}}" \
            -e FRONTEND_PORT="{{FRONTEND_PORT}}" \
            -e BACKEND_PORT="{{BACKEND_PORT}}" \
            -e USE_HOST_NETWORK=false \
            playwright-tests
    else
        docker run --rm --network host \
            -e PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
            -e BRANCH_NAME="{{BRANCH_NAME}}" \
            -e FRONTEND_PORT="{{FRONTEND_PORT}}" \
            -e BACKEND_PORT="{{BACKEND_PORT}}" \
            -e USE_HOST_NETWORK=true \
            playwright-tests
    fi
    echo -e "{{GREEN}}✓ Playwright tests complete{{NC}}"

################################################################################
# Deployment Targets
################################################################################

# Deploy application to dev environment
deploy:
    #!/usr/bin/env bash
    echo -e "{{CYAN}}Deploying application to development environment...{{NC}}"
    echo -e "{{YELLOW}}Environment: {{ENV}}{{NC}}"
    if [ -n "$AWS_PROFILE" ]; then
        export AWS_PROFILE=$AWS_PROFILE && ENV={{ENV}} ./infra/scripts/deploy-app.sh
    else
        ENV={{ENV}} ./infra/scripts/deploy-app.sh
    fi
    echo ""
    echo -e "{{GREEN}}✓ Deployment complete!{{NC}}"

# Check if infrastructure is deployed
deploy-check:
    #!/usr/bin/env bash
    echo -e "{{CYAN}}Checking infrastructure status...{{NC}}"
    if [ -n "$AWS_PROFILE" ]; then export AWS_PROFILE=$AWS_PROFILE; fi
    if aws elbv2 describe-load-balancers --names durableai-{{ENV}}-alb >/dev/null 2>&1; then
        echo -e "{{GREEN}}✓ Infrastructure appears to be deployed{{NC}}"
        echo -e "{{YELLOW}}ALB DNS:{{NC}}"
        aws elbv2 describe-load-balancers --names durableai-{{ENV}}-alb --query 'LoadBalancers[0].DNSName' --output text | sed 's/^/  http:\/\//'
    else
        echo -e "{{RED}}❌ Infrastructure not found!{{NC}}"
        echo -e "{{YELLOW}}Please run: just infra up{{NC}}"
        exit 1
    fi

################################################################################
# Infrastructure Targets (Terraform via Docker)
################################################################################

# Check AWS credentials
infra-check-aws:
    #!/usr/bin/env bash
    echo -e "{{CYAN}}Checking AWS credentials...{{NC}}"
    echo -e "{{YELLOW}}AWS Profile: {{AWS_PROFILE}}{{NC}}"
    echo -e "{{YELLOW}}AWS Region: {{AWS_REGION}}{{NC}}"
    if docker run --rm \
        -v $HOME/.aws:/root/.aws:ro \
        -e AWS_PROFILE={{AWS_PROFILE}} \
        -e AWS_REGION={{AWS_REGION}} \
        amazon/aws-cli:latest sts get-caller-identity >/dev/null 2>&1; then
        echo -e "{{GREEN}}✓ AWS credentials are valid!{{NC}}"
        docker run --rm \
            -v $HOME/.aws:/root/.aws:ro \
            -e AWS_PROFILE={{AWS_PROFILE}} \
            -e AWS_REGION={{AWS_REGION}} \
            amazon/aws-cli:latest sts get-caller-identity --output table
    else
        echo -e "{{RED}}❌ AWS credentials check failed!{{NC}}"
        exit 1
    fi

# Initialize Terraform for a scope (bootstrap, base, runtime, or all)
infra-init SCOPE="runtime":
    @echo -e "{{CYAN}}Initializing Terraform for {{SCOPE}}...{{NC}}"
    @just _infra-init-scope {{SCOPE}}

# Plan infrastructure changes for a scope
infra-plan SCOPE="runtime":
    @echo -e "{{CYAN}}Planning infrastructure changes for {{SCOPE}}...{{NC}}"
    @just _infra-plan-scope {{SCOPE}}

# Apply infrastructure changes (deploy) for a scope
infra-up SCOPE="runtime" AUTO="false":
    @echo -e "{{CYAN}}Deploying infrastructure for {{SCOPE}}...{{NC}}"
    @just _infra-apply-scope {{SCOPE}} {{AUTO}}

# Destroy infrastructure for a scope
infra-down SCOPE="runtime" CONFIRM="":
    @just _infra-destroy-scope {{SCOPE}} {{CONFIRM}}

# Format Terraform files
infra-fmt:
    @docker run --rm \
        -v $(pwd)/infra/terraform:/terraform \
        hashicorp/terraform:{{TERRAFORM_VERSION}} fmt -recursive

# Validate Terraform configuration
infra-validate SCOPE="runtime":
    @just _infra-validate-scope {{SCOPE}}

# Show Terraform outputs
infra-output SCOPE="runtime" FORMAT="":
    @just _infra-output-scope {{SCOPE}} {{FORMAT}}

# Show infrastructure status
infra-status:
    @echo -e "{{CYAN}}Infrastructure Status - Environment: {{ENV}}{{NC}}"
    @echo ""
    @echo -e "{{CYAN}}=== Base Infrastructure ==={{NC}}"
    @just _check-workspace-status base
    @echo ""
    @echo -e "{{CYAN}}=== Runtime Infrastructure ==={{NC}}"
    @just _check-workspace-status runtime

# Internal: Initialize for specific scope
@_infra-init-scope SCOPE:
    #!/usr/bin/env bash
    if [ "{{SCOPE}}" = "all" ]; then
        just _infra-do-init base
        just _infra-do-init runtime
    else
        just _infra-do-init {{SCOPE}}
    fi

# Internal: Plan for specific scope
@_infra-plan-scope SCOPE:
    #!/usr/bin/env bash
    if [ "{{SCOPE}}" = "all" ]; then
        echo -e "{{CYAN}}--- Planning base ---{{NC}}"
        just _infra-do-plan base
        echo -e "{{CYAN}}--- Planning runtime ---{{NC}}"
        just _infra-do-plan runtime
    else
        just _infra-do-plan {{SCOPE}}
    fi

# Internal: Apply for specific scope
@_infra-apply-scope SCOPE AUTO:
    #!/usr/bin/env bash
    if [ "{{SCOPE}}" = "all" ]; then
        echo -e "{{CYAN}}--- Deploying base ---{{NC}}"
        just _infra-do-apply base {{AUTO}}
        echo -e "{{CYAN}}--- Deploying runtime ---{{NC}}"
        just _infra-do-apply runtime {{AUTO}}
    else
        just _infra-do-apply {{SCOPE}} {{AUTO}}
    fi

# Internal: Destroy for specific scope
@_infra-destroy-scope SCOPE CONFIRM:
    #!/usr/bin/env bash
    # Confirmation checks
    if [ "{{SCOPE}}" = "bootstrap" ] && [ "{{CONFIRM}}" != "destroy-bootstrap" ]; then
        echo -e "{{RED}}ERROR: Bootstrap destruction requires CONFIRM=destroy-bootstrap{{NC}}"
        exit 1
    elif [ "{{SCOPE}}" = "base" ] && [ "{{CONFIRM}}" != "destroy-base" ]; then
        echo -e "{{RED}}ERROR: Base destruction requires CONFIRM=destroy-base{{NC}}"
        exit 1
    elif [ "{{SCOPE}}" = "all" ] && [ "{{CONFIRM}}" != "destroy-all" ]; then
        echo -e "{{RED}}ERROR: Full destruction requires CONFIRM=destroy-all{{NC}}"
        exit 1
    fi

    if [ "{{SCOPE}}" = "all" ]; then
        just _infra-do-destroy runtime
        just _infra-do-destroy base
    else
        just _infra-do-destroy {{SCOPE}}
    fi

# Internal: Validate for specific scope
@_infra-validate-scope SCOPE:
    #!/usr/bin/env bash
    if [ "{{SCOPE}}" = "all" ]; then
        just _infra-do-validate base
        just _infra-do-validate runtime
    else
        just _infra-do-validate {{SCOPE}}
    fi

# Internal: Output for specific scope
@_infra-output-scope SCOPE FORMAT:
    #!/usr/bin/env bash
    if [ "{{SCOPE}}" = "all" ]; then
        echo -e "{{CYAN}}--- Base outputs ---{{NC}}"
        just _infra-do-output base "{{FORMAT}}"
        echo -e "{{CYAN}}--- Runtime outputs ---{{NC}}"
        just _infra-do-output runtime "{{FORMAT}}"
    else
        just _infra-do-output {{SCOPE}} "{{FORMAT}}"
    fi

# Internal: Actual Terraform init operation
@_infra-do-init SCOPE:
    #!/usr/bin/env bash
    TERRAFORM_DIR="infra/terraform/workspaces/{{SCOPE}}"
    VOLUME_NAME="terraform-cache-{{SCOPE}}-{{ENV}}-$(echo $(pwd) | md5sum | cut -d' ' -f1)"

    echo "Creating Docker volume: $VOLUME_NAME"
    docker volume create $VOLUME_NAME >/dev/null 2>&1 || true

    BACKEND_CONFIG="/backend-config/{{SCOPE}}-{{ENV}}.hcl"
    echo "Using backend config: $BACKEND_CONFIG"

    docker run --rm \
        -v $(pwd)/$TERRAFORM_DIR:/terraform \
        -v $(pwd)/infra/environments:/environments:ro \
        -v $(pwd)/infra/terraform/backend-config:/backend-config:ro \
        -v $VOLUME_NAME:/terraform/.terraform \
        -v $HOME/.aws:/root/.aws:ro \
        -w /terraform \
        -e AWS_PROFILE={{AWS_PROFILE}} \
        -e AWS_REGION={{AWS_REGION}} \
        hashicorp/terraform:{{TERRAFORM_VERSION}} init -backend-config=$BACKEND_CONFIG

# Internal: Actual Terraform plan operation
@_infra-do-plan SCOPE:
    #!/usr/bin/env bash
    TERRAFORM_DIR="infra/terraform/workspaces/{{SCOPE}}"
    VOLUME_NAME="terraform-cache-{{SCOPE}}-{{ENV}}-$(echo $(pwd) | md5sum | cut -d' ' -f1)"
    WORKSPACE_NAME="{{SCOPE}}-{{ENV}}"

    docker run --rm \
        -v $(pwd)/$TERRAFORM_DIR:/terraform \
        -v $(pwd)/infra/environments:/environments:ro \
        -v $VOLUME_NAME:/terraform/.terraform \
        -v $HOME/.aws:/root/.aws:ro \
        -w /terraform \
        -e AWS_PROFILE={{AWS_PROFILE}} \
        -e AWS_REGION={{AWS_REGION}} \
        hashicorp/terraform:{{TERRAFORM_VERSION}} \
        sh -c "terraform workspace select $WORKSPACE_NAME 2>/dev/null || terraform workspace new $WORKSPACE_NAME; terraform plan -var-file=/environments/{{ENV}}.tfvars"

# Internal: Actual Terraform apply operation
@_infra-do-apply SCOPE AUTO:
    #!/usr/bin/env bash
    TERRAFORM_DIR="infra/terraform/workspaces/{{SCOPE}}"
    VOLUME_NAME="terraform-cache-{{SCOPE}}-{{ENV}}-$(echo $(pwd) | md5sum | cut -d' ' -f1)"
    WORKSPACE_NAME="{{SCOPE}}-{{ENV}}"

    if [ "{{AUTO}}" = "true" ]; then
        APPROVE_FLAG="-auto-approve"
    else
        APPROVE_FLAG=""
    fi

    docker run --rm -it \
        -v $(pwd)/$TERRAFORM_DIR:/terraform \
        -v $(pwd)/infra/environments:/environments:ro \
        -v $VOLUME_NAME:/terraform/.terraform \
        -v $HOME/.aws:/root/.aws:ro \
        -w /terraform \
        -e AWS_PROFILE={{AWS_PROFILE}} \
        -e AWS_REGION={{AWS_REGION}} \
        hashicorp/terraform:{{TERRAFORM_VERSION}} \
        sh -c "terraform workspace select $WORKSPACE_NAME 2>/dev/null || terraform workspace new $WORKSPACE_NAME; terraform apply -var-file=/environments/{{ENV}}.tfvars $APPROVE_FLAG"

# Internal: Actual Terraform destroy operation
@_infra-do-destroy SCOPE:
    #!/usr/bin/env bash
    TERRAFORM_DIR="infra/terraform/workspaces/{{SCOPE}}"
    VOLUME_NAME="terraform-cache-{{SCOPE}}-{{ENV}}-$(echo $(pwd) | md5sum | cut -d' ' -f1)"
    WORKSPACE_NAME="{{SCOPE}}-{{ENV}}"

    docker run --rm -it \
        -v $(pwd)/$TERRAFORM_DIR:/terraform \
        -v $(pwd)/infra/environments:/environments:ro \
        -v $VOLUME_NAME:/terraform/.terraform \
        -v $HOME/.aws:/root/.aws:ro \
        -w /terraform \
        -e AWS_PROFILE={{AWS_PROFILE}} \
        -e AWS_REGION={{AWS_REGION}} \
        hashicorp/terraform:{{TERRAFORM_VERSION}} \
        sh -c "terraform workspace select $WORKSPACE_NAME 2>/dev/null || exit 0; terraform destroy -var-file=/environments/{{ENV}}.tfvars"

# Internal: Actual Terraform validate operation
@_infra-do-validate SCOPE:
    #!/usr/bin/env bash
    TERRAFORM_DIR="infra/terraform/workspaces/{{SCOPE}}"
    VOLUME_NAME="terraform-cache-{{SCOPE}}-{{ENV}}-$(echo $(pwd) | md5sum | cut -d' ' -f1)"

    docker run --rm \
        -v $(pwd)/$TERRAFORM_DIR:/terraform \
        -v $VOLUME_NAME:/terraform/.terraform \
        -w /terraform \
        hashicorp/terraform:{{TERRAFORM_VERSION}} validate

# Internal: Actual Terraform output operation
@_infra-do-output SCOPE FORMAT:
    #!/usr/bin/env bash
    TERRAFORM_DIR="infra/terraform/workspaces/{{SCOPE}}"
    VOLUME_NAME="terraform-cache-{{SCOPE}}-{{ENV}}-$(echo $(pwd) | md5sum | cut -d' ' -f1)"
    WORKSPACE_NAME="{{SCOPE}}-{{ENV}}"

    if [ "{{FORMAT}}" = "json" ]; then
        OUTPUT_FLAG="-json"
    else
        OUTPUT_FLAG=""
    fi

    docker run --rm \
        -v $(pwd)/$TERRAFORM_DIR:/terraform \
        -v $VOLUME_NAME:/terraform/.terraform \
        -v $HOME/.aws:/root/.aws:ro \
        -w /terraform \
        -e AWS_PROFILE={{AWS_PROFILE}} \
        hashicorp/terraform:{{TERRAFORM_VERSION}} \
        sh -c "terraform workspace select $WORKSPACE_NAME && terraform output $OUTPUT_FLAG"

# Internal: Check workspace status
@_check-workspace-status SCOPE:
    #!/usr/bin/env bash
    VOLUME_NAME="terraform-cache-{{SCOPE}}-{{ENV}}-$(echo $(pwd) | md5sum | cut -d' ' -f1)"
    if docker volume inspect $VOLUME_NAME >/dev/null 2>&1; then
        echo -e "{{GREEN}}✓ {{SCOPE}} workspace initialized{{NC}}"
    else
        echo -e "{{YELLOW}}⚠ {{SCOPE}} workspace not initialized{{NC}}"
    fi

################################################################################
# GitHub Integration Targets
################################################################################

# Watch GitHub checks (required by /done command)
gh-watch-checks:
    @echo -e "{{YELLOW}}⏱️  NOTE: GitHub checks may take up to 3 minutes to start{{NC}}"
    @./scripts/gh-watch-checks.sh $(gh pr view --json number -q .number 2>/dev/null)

# Show detailed logs for failed checks
gh-check-details:
    #!/usr/bin/env bash
    PR_NUMBER=$(gh pr view --json number -q .number 2>/dev/null)
    if [ -z "$PR_NUMBER" ]; then
        echo -e "{{RED}}❌ No PR found for current branch{{NC}}"
        exit 1
    fi
    echo -e "{{CYAN}}Fetching detailed check information for PR #$PR_NUMBER...{{NC}}"
    ./scripts/gh-check-details.sh $PR_NUMBER

# Alias for compatibility
lint-all: lint
