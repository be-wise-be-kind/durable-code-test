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
TERRAFORM_BIN := `if [ -x "$HOME/.tfenv/bin/terraform" ]; then echo "$HOME/.tfenv/bin/terraform"; elif command -v terraform >/dev/null 2>&1; then command -v terraform; else echo "terraform"; fi`
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

# Initialize project (install tools, build images, install hooks)
init:
    @echo -e "{{CYAN}}Initializing project...{{NC}}"
    @echo -e "{{YELLOW}}Installing tfenv (Terraform version manager)...{{NC}}"
    @if ! command -v tfenv &> /dev/null; then \
        if [ -d "$HOME/.tfenv" ]; then \
            echo -e "{{GREEN}}✓ tfenv already installed at ~/.tfenv{{NC}}"; \
        else \
            git clone --depth=1 https://github.com/tfutils/tfenv.git ~/.tfenv && \
            echo -e "{{GREEN}}✓ tfenv installed. Add ~/.tfenv/bin to your PATH{{NC}}" && \
            echo -e "{{YELLOW}}  Add to ~/.bashrc: export PATH=\"\$HOME/.tfenv/bin:\$PATH\"{{NC}}"; \
        fi; \
    else \
        echo -e "{{GREEN}}✓ tfenv already available{{NC}}"; \
    fi
    @echo -e "{{YELLOW}}Installing Terraform {{TERRAFORM_VERSION}}...{{NC}}"
    @bash -c ' \
        if [ -x "$$HOME/.tfenv/bin/tfenv" ]; then \
            $$HOME/.tfenv/bin/tfenv install {{TERRAFORM_VERSION}} 2>/dev/null || echo -e "{{GREEN}}✓ Terraform {{TERRAFORM_VERSION}} already installed{{NC}}"; \
            $$HOME/.tfenv/bin/tfenv use {{TERRAFORM_VERSION}}; \
            echo -e "{{GREEN}}✓ Terraform {{TERRAFORM_VERSION}} configured{{NC}}"; \
        elif command -v tfenv &> /dev/null; then \
            tfenv install {{TERRAFORM_VERSION}} 2>/dev/null || echo -e "{{GREEN}}✓ Terraform {{TERRAFORM_VERSION}} already installed{{NC}}"; \
            tfenv use {{TERRAFORM_VERSION}}; \
            echo -e "{{GREEN}}✓ Terraform {{TERRAFORM_VERSION}} configured{{NC}}"; \
        else \
            echo -e "{{YELLOW}}⚠ tfenv not found. Install manually or add ~/.tfenv/bin to PATH{{NC}}"; \
        fi \
    '
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

# Run linting (Examples: lint, lint python, lint frontend, lint infra, lint security)
lint SCOPE="all":
    @echo -e "{{CYAN}}╔════════════════════════════════════════════════════════════╗{{NC}}"
    @echo -e "{{CYAN}}║              Running Linting: {{SCOPE}}                    ║{{NC}}"
    @echo -e "{{CYAN}}╚════════════════════════════════════════════════════════════╝{{NC}}"
    @echo ""
    @just _run-lint {{SCOPE}}
    @echo ""
    @echo -e "{{GREEN}}✅ Linting checks passed!{{NC}}"

# Internal: Execute linting based on scope
_run-lint SCOPE:
    #!/usr/bin/env bash
    set -e

    case "{{SCOPE}}" in
        all)
            echo -e "{{YELLOW}}Running all linters in parallel...{{NC}}"
            just _lint-python &
            PYTHON_PID=$!
            just _lint-frontend &
            FRONTEND_PID=$!

            wait $PYTHON_PID
            PYTHON_EXIT=$?
            wait $FRONTEND_PID
            FRONTEND_EXIT=$?

            if [ $PYTHON_EXIT -ne 0 ] || [ $FRONTEND_EXIT -ne 0 ]; then
                echo -e "{{RED}}❌ Linting failed{{NC}}"
                exit 1
            fi

            just _lint-infra
            ;;
        python)
            just _lint-python
            ;;
        frontend)
            just _lint-frontend
            ;;
        security)
            just _lint-security
            ;;
        infra)
            just _lint-infra
            ;;
        *)
            echo -e "{{RED}}Unknown scope: {{SCOPE}}{{NC}}"
            echo -e "{{YELLOW}}Valid scopes: all, python, frontend, security, infra{{NC}}"
            exit 1
            ;;
    esac

# Internal: Python linting
@_lint-python:
    echo -e "{{YELLOW}}━━━ Python Linters ━━━{{NC}}"
    cd durable-code-app/backend && \
        echo '• Ruff format...' && poetry run ruff format --check app ../../tools && \
        echo '• Ruff lint...' && poetry run ruff check app ../../tools && \
        echo '• Flake8...' && poetry run flake8 app --count 2>/dev/null && poetry run flake8 ../../tools --config ../../tools/.flake8 --count 2>/dev/null && \
        echo '• MyPy...' && poetry run mypy . && \
        echo '• Pylint...' && poetry run pylint app ../../tools 2>&1 | tail -3 && \
        echo '• Bandit...' && poetry run bandit -r app ../../tools -q && \
        echo '• Xenon...' && poetry run xenon --max-absolute B --max-modules B --max-average A app
    echo -e "{{GREEN}}✓ Python linting passed{{NC}}"

# Internal: Frontend linting
@_lint-frontend:
    echo -e "{{YELLOW}}━━━ TypeScript/React Linters ━━━{{NC}}"
    cd durable-code-app/frontend && \
        echo '• TypeScript...' && npm run typecheck && \
        echo '• ESLint...' && npm run lint && \
        echo '• Stylelint...' && npm run lint:css && \
        echo '• Prettier...' && npm run format:check
    echo -e "{{GREEN}}✓ Frontend linting passed{{NC}}"

# Internal: Security linting
@_lint-security:
    echo -e "{{YELLOW}}━━━ Security Linters ━━━{{NC}}"
    cd durable-code-app/backend && \
        echo '• Bandit (Python security)...' && poetry run bandit -r app ../../tools -q
    echo -e "{{GREEN}}✓ Security linting passed{{NC}}"

# Internal: Infrastructure linting
@_lint-infra:
    echo -e "{{YELLOW}}━━━ Infrastructure Linters ━━━{{NC}}"
    printf '%-30s' "• Terraform format" && (just _infra-fmt >/dev/null 2>&1 && echo -e "{{GREEN}}✓{{NC}}" || exit 1)
    printf '%-30s' "• Shellcheck" && (shellcheck infra/scripts/*.sh scripts/*.sh 2>/dev/null && echo -e "{{GREEN}}✓{{NC}}" || echo -e "{{YELLOW}}⚠ (not installed){{NC}}")
    echo -e "{{GREEN}}✓ Infrastructure linting passed{{NC}}"

# Auto-fix formatting issues
lint-fix:
    @echo -e "{{CYAN}}Auto-fixing code formatting...{{NC}}"
    @echo -e "{{YELLOW}}Fixing Python code...{{NC}}"
    @cd durable-code-app/backend && poetry run ruff format app ../../tools && poetry run ruff check --fix app ../../tools
    @echo -e "{{YELLOW}}Fixing TypeScript/React code...{{NC}}"
    @cd durable-code-app/frontend && npm run lint:fix && npm run lint:css:fix && npm run format
    @echo -e "{{GREEN}}✅ Auto-fix complete!{{NC}}"

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
    @docker exec durable-code-backend-{{BRANCH_NAME}}-dev bash -c "cd /app && PYTHONPATH=/app:/app/tools poetry config virtualenvs.create false && poetry run pytest test/ --cov=app --cov-report=term --cov-report=term:skip-covered --tb=short -v"
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
        docker run --rm --network durable-network-dev \
            -e PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
            -e BRANCH_NAME="{{BRANCH_NAME}}" \
            -e FRONTEND_PORT="{{FRONTEND_PORT}}" \
            -e BACKEND_PORT="{{BACKEND_PORT}}" \
            -e RUN_PLAYWRIGHT_TESTS=true \
            -e USE_HOST_NETWORK=false \
            playwright-tests
    else
        docker run --rm --network host \
            -e PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
            -e BRANCH_NAME="{{BRANCH_NAME}}" \
            -e FRONTEND_PORT="{{FRONTEND_PORT}}" \
            -e BACKEND_PORT="{{BACKEND_PORT}}" \
            -e RUN_PLAYWRIGHT_TESTS=true \
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
# Infrastructure Targets (Terraform Direct Execution)
################################################################################

# Infrastructure management (Examples: infra plan runtime, infra up all, infra down runtime destroy-runtime, infra status)
infra SUBCOMMAND *ARGS:
    @just _infra-dispatch {{SUBCOMMAND}} {{ARGS}}

# Internal: Dispatch subcommands to appropriate handlers
_infra-dispatch SUBCOMMAND *ARGS:
    #!/usr/bin/env bash
    set -euo pipefail

    # Extract arguments from Just's ARGS
    ARGS_ARRAY=({{ARGS}})
    ARG1="${ARGS_ARRAY[0]:-runtime}"
    ARG2="${ARGS_ARRAY[1]:-}"

    case "{{SUBCOMMAND}}" in
        --list|list|help)
            just _infra-help
            ;;
        login)
            just _infra-aws-login
            ;;
        check-aws)
            just _infra-check-aws
            ;;
        init)
            just _infra-init-scope "$ARG1"
            ;;
        plan)
            just _infra-plan-scope "$ARG1"
            ;;
        up)
            AUTO="${ARG2:-false}"
            just _infra-apply-scope "$ARG1" "$AUTO"
            ;;
        down)
            just _infra-destroy-scope "$ARG1"
            ;;
        down-force)
            just _infra-destroy-force-scope "$ARG1"
            ;;
        fmt)
            just _infra-fmt
            ;;
        validate)
            just _infra-validate-scope "$ARG1"
            ;;
        output)
            just _infra-output-scope "$ARG1" "$ARG2"
            ;;
        status)
            just _infra-status
            ;;
        state)
            just _infra-state-list "$ARG1"
            ;;
        unlock)
            just _infra-force-unlock "$ARG1" "$ARG2"
            ;;
        *)
            echo -e "{{RED}}Error: Unknown subcommand '{{SUBCOMMAND}}'{{NC}}"
            echo ""
            just _infra-help
            exit 1
            ;;
    esac

# Internal: Show infrastructure command help
_infra-help:
    @echo -e "{{CYAN}}╔════════════════════════════════════════════════════════════╗{{NC}}"
    @echo -e "{{CYAN}}║          Infrastructure Management Commands               ║{{NC}}"
    @echo -e "{{CYAN}}╚════════════════════════════════════════════════════════════╝{{NC}}"
    @echo ""
    @echo -e "{{GREEN}}Usage:{{NC}} just infra <subcommand> [arguments]"
    @echo ""
    @echo -e "{{GREEN}}Subcommands:{{NC}}"
    @echo -e "  {{YELLOW}}login{{NC}}                    Login to AWS via SSO (opens browser)"
    @echo -e "  {{YELLOW}}check-aws{{NC}}                Check AWS credentials and configuration"
    @echo -e "  {{YELLOW}}status{{NC}}                   Show current infrastructure status"
    @echo -e "  {{YELLOW}}state [SCOPE]{{NC}}            List Terraform state resources"
    @echo -e "  {{YELLOW}}unlock [SCOPE] [LOCK_ID]{{NC}} Force unlock Terraform state (use with caution)"
    @echo -e "  {{YELLOW}}fmt{{NC}}                      Format all Terraform files"
    @echo ""
    @echo -e "  {{YELLOW}}init [SCOPE]{{NC}}             Initialize Terraform workspace"
    @echo -e "  {{YELLOW}}validate [SCOPE]{{NC}}         Validate Terraform configuration"
    @echo -e "  {{YELLOW}}plan [SCOPE]{{NC}}             Plan infrastructure changes"
    @echo -e "  {{YELLOW}}up [SCOPE] [AUTO]{{NC}}        Deploy infrastructure"
    @echo -e "  {{YELLOW}}down [SCOPE]{{NC}}             Destroy infrastructure"
    @echo -e "  {{YELLOW}}down-force [SCOPE]{{NC}}      Force destroy (skip refresh, auto-approve)"
    @echo -e "  {{YELLOW}}output [SCOPE] [FORMAT]{{NC}}  Show Terraform outputs"
    @echo ""
    @echo -e "{{GREEN}}Scopes:{{NC}}"
    @echo -e "  {{YELLOW}}base{{NC}}                     Base infrastructure (VPC, networking, security groups)"
    @echo -e "  {{YELLOW}}runtime{{NC}}                  Runtime infrastructure (ECS, ALB, services) [default]"
    @echo -e "  {{YELLOW}}all{{NC}}                      Both base and runtime (excludes bootstrap)"
    @echo -e "  {{YELLOW}}bootstrap{{NC}}                Bootstrap infrastructure (S3 state bucket)"
    @echo ""
    @echo -e "{{GREEN}}Common Examples:{{NC}}"
    @echo -e "  {{CYAN}}just infra check-aws{{NC}}                      # Verify AWS credentials"
    @echo -e "  {{CYAN}}just infra status{{NC}}                         # Check infrastructure status"
    @echo ""
    @echo -e "  {{CYAN}}just infra plan runtime{{NC}}                   # Plan runtime changes"
    @echo -e "  {{CYAN}}just infra plan all{{NC}}                       # Plan all infrastructure"
    @echo ""
    @echo -e "  {{CYAN}}just infra up runtime{{NC}}                     # Deploy runtime (interactive)"
    @echo -e "  {{CYAN}}just infra up runtime true{{NC}}                # Deploy runtime (auto-approve)"
    @echo -e "  {{CYAN}}just infra up all{{NC}}                         # Deploy base + runtime"
    @echo ""
    @echo -e "  {{CYAN}}just infra down runtime{{NC}}                    # Destroy runtime infrastructure"
    @echo -e "  {{CYAN}}just infra down all{{NC}}                        # Destroy all except bootstrap"
    @echo -e "  {{CYAN}}just infra down base{{NC}}                       # Destroy base infrastructure"
    @echo ""
    @echo -e "  {{CYAN}}just infra output runtime{{NC}}                 # Show runtime outputs (text)"
    @echo -e "  {{CYAN}}just infra output runtime json{{NC}}            # Show runtime outputs (JSON)"
    @echo ""
    @echo -e "{{YELLOW}}Note:{{NC}} Terraform will prompt for confirmation before destroying resources"
    @echo ""

# Internal: AWS Login - Configure credentials from .env
_infra-aws-login:
    #!/usr/bin/env bash
    set -euo pipefail

    # Colors
    CYAN='\033[0;36m'
    GREEN='\033[0;32m'
    YELLOW='\033[0;33m'
    RED='\033[0;31m'
    NC='\033[0m'

    PROFILE_NAME="{{AWS_PROFILE}}"
    DEFAULT_REGION="{{AWS_REGION}}"
    AWS_CREDENTIALS="$HOME/.aws/credentials"
    AWS_CONFIG="$HOME/.aws/config"

    echo -e "${CYAN}AWS Login - Configure Profile${NC}"
    echo -e "${YELLOW}Profile: $PROFILE_NAME${NC}"
    echo -e "${YELLOW}Region: $DEFAULT_REGION${NC}"
    echo ""

    # Check if .env has credentials
    if [ -f ".env" ]; then
        source .env 2>/dev/null || true
    fi

    if [ -z "${TERRAFORM_AWS_ACCESS_KEY_ID:-}" ] || [ -z "${TERRAFORM_AWS_SECRET_ACCESS_KEY:-}" ]; then
        echo -e "${RED}❌ AWS credentials not found in .env${NC}"
        echo -e "${YELLOW}Please set TERRAFORM_AWS_ACCESS_KEY_ID and TERRAFORM_AWS_SECRET_ACCESS_KEY in .env${NC}"
        exit 1
    fi

    # Ensure ~/.aws directory exists
    mkdir -p "$HOME/.aws"

    # Create/update credentials file
    echo -e "${YELLOW}Configuring AWS credentials for profile '$PROFILE_NAME'...${NC}"

    # Check if profile section exists in credentials, if not add it
    if ! grep -q "^\[$PROFILE_NAME\]" "$AWS_CREDENTIALS" 2>/dev/null; then
        {
            echo ""
            echo "[$PROFILE_NAME]"
            echo "aws_access_key_id = $TERRAFORM_AWS_ACCESS_KEY_ID"
            echo "aws_secret_access_key = $TERRAFORM_AWS_SECRET_ACCESS_KEY"
        } >> "$AWS_CREDENTIALS"
        echo -e "${GREEN}✓ Credentials added to $AWS_CREDENTIALS${NC}"
    else
        # Update existing profile using a temp file
        TEMP_FILE=$(mktemp)
        awk -v profile="$PROFILE_NAME" -v key="$TERRAFORM_AWS_ACCESS_KEY_ID" -v secret="$TERRAFORM_AWS_SECRET_ACCESS_KEY" '
            BEGIN { in_profile=0 }
            /^\[/ { in_profile=0 }
            $0 ~ "^\\[" profile "\\]" { in_profile=1; print; next }
            in_profile && /^aws_access_key_id/ { print "aws_access_key_id = " key; next }
            in_profile && /^aws_secret_access_key/ { print "aws_secret_access_key = " secret; next }
            { print }
        ' "$AWS_CREDENTIALS" > "$TEMP_FILE"
        mv "$TEMP_FILE" "$AWS_CREDENTIALS"
        echo -e "${GREEN}✓ Credentials updated in $AWS_CREDENTIALS${NC}"
    fi

    # Ensure config has the profile with region
    if ! grep -q "^\[profile $PROFILE_NAME\]" "$AWS_CONFIG" 2>/dev/null; then
        {
            echo ""
            echo "[profile $PROFILE_NAME]"
            echo "region = $DEFAULT_REGION"
            echo "output = json"
        } >> "$AWS_CONFIG"
        echo -e "${GREEN}✓ Profile config added to $AWS_CONFIG${NC}"
    fi

    chmod 600 "$AWS_CREDENTIALS"
    echo ""

    # Verify credentials work
    echo -e "${CYAN}Verifying credentials...${NC}"
    if aws sts get-caller-identity --profile "$PROFILE_NAME" --output table; then
        echo ""
        echo -e "${GREEN}✓ AWS credentials configured and verified!${NC}"
    else
        echo ""
        echo -e "${RED}❌ AWS credential verification failed${NC}"
        echo -e "${YELLOW}Check your access keys in .env${NC}"
        exit 1
    fi

# Internal: Check AWS credentials
_infra-check-aws:
    #!/usr/bin/env bash
    echo -e "{{CYAN}}Checking AWS credentials...{{NC}}"
    echo -e "{{YELLOW}}AWS Profile: {{AWS_PROFILE}}{{NC}}"
    echo -e "{{YELLOW}}AWS Region: {{AWS_REGION}}{{NC}}"
    if aws sts get-caller-identity --profile {{AWS_PROFILE}} --region {{AWS_REGION}} >/dev/null 2>&1; then
        echo -e "{{GREEN}}✓ AWS credentials are valid!{{NC}}"
        aws sts get-caller-identity --profile {{AWS_PROFILE}} --output table
    else
        echo -e "{{RED}}❌ AWS credentials check failed!{{NC}}"
        echo -e "{{YELLOW}}Try: just infra login{{NC}}"
        exit 1
    fi

# Internal: Format Terraform files
_infra-fmt:
    @cd infra/terraform && {{TERRAFORM_BIN}} fmt -recursive

# Internal: Show infrastructure status
_infra-status:
    @echo -e "{{CYAN}}Infrastructure Status - Environment: {{ENV}}{{NC}}"
    @echo ""
    @echo -e "{{CYAN}}=== Base Infrastructure ==={{NC}}"
    @just _check-workspace-status base
    @echo ""
    @echo -e "{{CYAN}}=== Runtime Infrastructure ==={{NC}}"
    @just _check-workspace-status runtime

# Internal: Initialize for specific scope
_infra-init-scope SCOPE:
    #!/usr/bin/env bash
    set -euo pipefail
    if [ "{{SCOPE}}" = "all" ]; then
        just _infra-do-init base
        just _infra-do-init runtime
    else
        just _infra-do-init {{SCOPE}}
    fi

# Internal: Plan for specific scope
_infra-plan-scope SCOPE:
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
_infra-apply-scope SCOPE AUTO:
    #!/usr/bin/env bash
    if [ "{{SCOPE}}" = "all" ]; then
        echo -e "{{CYAN}}--- Deploying base ---{{NC}}"
        just _infra-do-apply base {{AUTO}}
        echo -e "{{CYAN}}--- Deploying runtime ---{{NC}}"
        just _infra-do-apply runtime {{AUTO}}
        echo -e "{{CYAN}}--- Deploying application ---{{NC}}"
        just deploy
    elif [ "{{SCOPE}}" = "runtime" ]; then
        just _infra-do-apply {{SCOPE}} {{AUTO}}
        echo -e "{{CYAN}}--- Deploying application ---{{NC}}"
        just deploy
    else
        just _infra-do-apply {{SCOPE}} {{AUTO}}
    fi

# Internal: Destroy for specific scope
_infra-destroy-scope SCOPE:
    #!/usr/bin/env bash
    # Safety warning for bootstrap
    if [ "{{SCOPE}}" = "bootstrap" ]; then
        echo -e "{{RED}}⚠️  WARNING: You are about to destroy the bootstrap infrastructure!{{NC}}"
        echo -e "{{RED}}⚠️  This contains the Terraform state bucket and will affect ALL environments.{{NC}}"
        echo -e "{{YELLOW}}Press Ctrl+C to cancel, or Terraform will prompt for confirmation...{{NC}}"
        echo ""
        sleep 3
    fi

    if [ "{{SCOPE}}" = "all" ]; then
        echo -e "{{YELLOW}}Destroying all infrastructure (runtime + base)...{{NC}}"
        just _infra-do-destroy runtime
        just _infra-do-destroy base
    else
        just _infra-do-destroy {{SCOPE}}
    fi

# Internal: Validate for specific scope
_infra-validate-scope SCOPE:
    #!/usr/bin/env bash
    if [ "{{SCOPE}}" = "all" ]; then
        just _infra-do-validate base
        just _infra-do-validate runtime
    else
        just _infra-do-validate {{SCOPE}}
    fi

# Internal: Output for specific scope
_infra-output-scope SCOPE FORMAT:
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
_infra-do-init SCOPE:
    #!/usr/bin/env bash
    set -euo pipefail
    SCOPE="{{SCOPE}}"
    TERRAFORM_DIR="infra/terraform/workspaces/$SCOPE"
    BACKEND_CONFIG="$(pwd)/infra/terraform/backend-config/$SCOPE-{{ENV}}.hcl"

    echo -e "{{YELLOW}}Initializing Terraform in $TERRAFORM_DIR...{{NC}}"
    echo -e "{{YELLOW}}Using backend config: $BACKEND_CONFIG{{NC}}"

    cd "$TERRAFORM_DIR"
    AWS_PROFILE={{AWS_PROFILE}} AWS_REGION={{AWS_REGION}} \
        {{TERRAFORM_BIN}} init -backend-config="$BACKEND_CONFIG" -reconfigure

    echo -e "{{GREEN}}✓ Terraform initialized for $SCOPE{{NC}}"

# Internal: Actual Terraform plan operation
_infra-do-plan SCOPE:
    #!/usr/bin/env bash
    SCOPE="{{SCOPE}}"
    TERRAFORM_DIR="infra/terraform/workspaces/$SCOPE"
    TFVARS_FILE="$(pwd)/infra/environments/{{ENV}}.tfvars"

    echo -e "{{YELLOW}}Planning infrastructure for $SCOPE ({{ENV}})...{{NC}}"

    cd "$TERRAFORM_DIR"

    # Run plan - backend-config determines state path, no workspace needed
    AWS_PROFILE={{AWS_PROFILE}} AWS_REGION={{AWS_REGION}} \
        {{TERRAFORM_BIN}} plan -var-file="$TFVARS_FILE"

    echo -e "{{GREEN}}✓ Plan complete for $SCOPE{{NC}}"

# Internal: Actual Terraform apply operation
_infra-do-apply SCOPE AUTO:
    #!/usr/bin/env bash
    set -euo pipefail
    SCOPE="{{SCOPE}}"
    AUTO="{{AUTO}}"
    TERRAFORM_DIR="infra/terraform/workspaces/$SCOPE"
    TFVARS_FILE="$(pwd)/infra/environments/{{ENV}}.tfvars"

    if [ "$AUTO" = "true" ]; then
        APPROVE_FLAG="-auto-approve"
    else
        APPROVE_FLAG=""
    fi

    echo -e "{{YELLOW}}Applying infrastructure for $SCOPE ({{ENV}})...{{NC}}"

    cd "$TERRAFORM_DIR"

    # Run apply - backend-config determines state path, no workspace needed
    if ! AWS_PROFILE={{AWS_PROFILE}} AWS_REGION={{AWS_REGION}} \
        {{TERRAFORM_BIN}} apply -var-file="$TFVARS_FILE" $APPROVE_FLAG; then
        echo -e "{{RED}}✗ Apply failed for $SCOPE{{NC}}"
        exit 1
    fi

    echo -e "{{GREEN}}✓ Apply complete for $SCOPE{{NC}}"

# Internal: Actual Terraform destroy operation
_infra-do-destroy SCOPE:
    #!/usr/bin/env bash
    SCOPE="{{SCOPE}}"
    TERRAFORM_DIR="infra/terraform/workspaces/$SCOPE"
    TFVARS_FILE="$(pwd)/infra/environments/{{ENV}}.tfvars"

    echo -e "{{RED}}Destroying infrastructure for $SCOPE ({{ENV}})...{{NC}}"

    cd "$TERRAFORM_DIR"

    # Run destroy - backend-config determines state path, no workspace needed
    AWS_PROFILE={{AWS_PROFILE}} AWS_REGION={{AWS_REGION}} \
        {{TERRAFORM_BIN}} destroy -var-file="$TFVARS_FILE"

    echo -e "{{GREEN}}✓ Destroy complete for $SCOPE{{NC}}"

# Internal: Force destroy for specific scope (no refresh, auto-approve)
_infra-destroy-force-scope SCOPE:
    #!/usr/bin/env bash
    # Safety warning
    echo -e "{{RED}}⚠️  WARNING: Force destroying {{SCOPE}} (no refresh, auto-approve){{NC}}"
    echo -e "{{YELLOW}}This skips state refresh and confirmation - use only when normal destroy fails{{NC}}"
    echo -e "{{YELLOW}}Press Ctrl+C to cancel or wait 3 seconds...{{NC}}"
    echo ""
    sleep 3

    if [ "{{SCOPE}}" = "all" ]; then
        echo -e "{{YELLOW}}Force destroying all infrastructure (runtime + base)...{{NC}}"
        just _infra-do-destroy-force runtime
        just _infra-do-destroy-force base
    else
        just _infra-do-destroy-force {{SCOPE}}
    fi

# Internal: Actual force destroy operation
_infra-do-destroy-force SCOPE:
    #!/usr/bin/env bash
    SCOPE="{{SCOPE}}"
    TERRAFORM_DIR="infra/terraform/workspaces/$SCOPE"
    TFVARS_FILE="$(pwd)/infra/environments/{{ENV}}.tfvars"

    echo -e "{{RED}}Force destroying infrastructure for $SCOPE ({{ENV}})...{{NC}}"

    cd "$TERRAFORM_DIR"

    # Run destroy with -refresh=false and -auto-approve
    # Backend-config determines state path, no workspace needed
    AWS_PROFILE={{AWS_PROFILE}} AWS_REGION={{AWS_REGION}} \
        {{TERRAFORM_BIN}} destroy -var-file="$TFVARS_FILE" -refresh=false -auto-approve

    echo -e "{{GREEN}}✓ Force destroy complete for $SCOPE{{NC}}"

# Internal: Actual Terraform validate operation
_infra-do-validate SCOPE:
    #!/usr/bin/env bash
    SCOPE="{{SCOPE}}"
    TERRAFORM_DIR="infra/terraform/workspaces/$SCOPE"

    echo -e "{{YELLOW}}Validating Terraform configuration for $SCOPE...{{NC}}"

    cd "$TERRAFORM_DIR"
    {{TERRAFORM_BIN}} validate

    echo -e "{{GREEN}}✓ Validation passed for $SCOPE{{NC}}"

# Internal: Actual Terraform output operation
_infra-do-output SCOPE FORMAT:
    #!/usr/bin/env bash
    SCOPE="{{SCOPE}}"
    FORMAT="{{FORMAT}}"
    TERRAFORM_DIR="infra/terraform/workspaces/$SCOPE"

    if [ "$FORMAT" = "json" ]; then
        OUTPUT_FLAG="-json"
    else
        OUTPUT_FLAG=""
    fi

    echo -e "{{YELLOW}}Fetching outputs for $SCOPE ({{ENV}})...{{NC}}"

    cd "$TERRAFORM_DIR"

    # Get outputs - backend-config determines state path, no workspace needed
    AWS_PROFILE={{AWS_PROFILE}} {{TERRAFORM_BIN}} output $OUTPUT_FLAG

# Internal: Check workspace status
_check-workspace-status SCOPE:
    #!/usr/bin/env bash
    TERRAFORM_DIR="infra/terraform/workspaces/{{SCOPE}}"

    if [ -d "$TERRAFORM_DIR/.terraform" ]; then
        echo -e "{{GREEN}}✓ {{SCOPE}} initialized for {{ENV}}{{NC}}"
    else
        echo -e "{{YELLOW}}⚠ {{SCOPE}} not initialized{{NC}}"
    fi

# Internal: Force unlock Terraform state
_infra-force-unlock SCOPE LOCK_ID:
    #!/usr/bin/env bash
    SCOPE="{{SCOPE}}"
    LOCK_ID="{{LOCK_ID}}"
    TERRAFORM_DIR="infra/terraform/workspaces/$SCOPE"

    if [ -z "$LOCK_ID" ]; then
        echo -e "{{RED}}Error: LOCK_ID is required{{NC}}"
        echo -e "{{YELLOW}}Usage: just infra unlock [SCOPE] [LOCK_ID]{{NC}}"
        exit 1
    fi

    echo -e "{{RED}}⚠️  WARNING: Force unlocking Terraform state for $SCOPE ({{ENV}}){{NC}}"
    echo -e "{{YELLOW}}Lock ID: $LOCK_ID{{NC}}"
    echo -e "{{YELLOW}}Only proceed if you are certain no Terraform operations are running!{{NC}}"
    echo -e "{{YELLOW}}Press Ctrl+C to cancel or wait 5 seconds...{{NC}}"
    echo ""
    sleep 5

    cd "$TERRAFORM_DIR"

    # Force unlock - backend-config determines state path, no workspace needed
    AWS_PROFILE={{AWS_PROFILE}} {{TERRAFORM_BIN}} force-unlock -force "$LOCK_ID"

    echo -e "{{GREEN}}✓ State unlocked for $SCOPE{{NC}}"

# Internal: List Terraform state for specific scope
_infra-state-list SCOPE:
    #!/usr/bin/env bash
    SCOPE="{{SCOPE}}"
    TERRAFORM_DIR="infra/terraform/workspaces/$SCOPE"

    echo -e "{{YELLOW}}Listing Terraform state for $SCOPE ({{ENV}})...{{NC}}"

    cd "$TERRAFORM_DIR"

    # List state - backend-config determines state path, no workspace needed
    AWS_PROFILE={{AWS_PROFILE}} {{TERRAFORM_BIN}} state list

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

################################################################################
# Installation Targets
################################################################################

# Install all dependencies for linting and development
install:
    @echo -e "{{CYAN}}╔════════════════════════════════════════════════════════════╗{{NC}}"
    @echo -e "{{CYAN}}║              Installing Dependencies                      ║{{NC}}"
    @echo -e "{{CYAN}}╚════════════════════════════════════════════════════════════╝{{NC}}"
    @echo ""
    @echo -e "{{YELLOW}}Installing Python dependencies (Poetry)...{{NC}}"
    @cd durable-code-app/backend && poetry install
    @echo -e "{{GREEN}}✓ Python dependencies installed{{NC}}"
    @echo ""
    @echo -e "{{YELLOW}}Installing frontend dependencies (npm)...{{NC}}"
    @cd durable-code-app/frontend && npm ci
    @echo -e "{{GREEN}}✓ Frontend dependencies installed{{NC}}"
    @echo ""
    @echo -e "{{YELLOW}}Installing pre-commit hooks...{{NC}}"
    @pip3 install pre-commit 2>/dev/null || pip install pre-commit 2>/dev/null || echo -e "{{YELLOW}}⚠ Pre-commit not installed via pip{{NC}}"
    @pre-commit install 2>/dev/null || echo -e "{{YELLOW}}⚠ Pre-commit hooks not installed{{NC}}"
    @pre-commit install --hook-type pre-push 2>/dev/null || echo -e "{{YELLOW}}⚠ Pre-push hooks not installed{{NC}}"
    @echo -e "{{GREEN}}✓ Pre-commit hooks installed{{NC}}"
    @echo ""
    @echo -e "{{GREEN}}✅ All dependencies installed!{{NC}}"
