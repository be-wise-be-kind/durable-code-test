# Makefile for Durable Code Test Project
# Docker-based development and deployment automation

.PHONY: help init dev-start dev-stop dev-restart dev-logs dev status clean shell-backend shell-frontend install-hooks deploy deploy-check

# Default target
.DEFAULT_GOAL := help

# Variables
# Get current git branch name, sanitized for Docker container names
# In CI, use GITHUB_HEAD_REF for PRs or GITHUB_REF_NAME for pushes
ifdef GITHUB_ACTIONS
  ifdef GITHUB_HEAD_REF
    BRANCH_NAME := $(shell echo "$(GITHUB_HEAD_REF)" | tr '/' '-' | tr '[:upper:]' '[:lower:]')
  else
    BRANCH_NAME := $(shell echo "$(GITHUB_REF_NAME)" | tr '/' '-' | tr '[:upper:]' '[:lower:]')
  endif
else
  BRANCH_NAME := $(shell git rev-parse --abbrev-ref HEAD 2>/dev/null | tr '/' '-' | tr '[:upper:]' '[:lower:]' || echo "main")
endif
export BRANCH_NAME

# Calculate dynamic ports based on branch name
FRONTEND_PORT := $(shell ./scripts/get-branch-ports.sh "$(BRANCH_NAME)" export 2>/dev/null | grep FRONTEND_PORT | cut -d= -f2 || echo "5173")
BACKEND_PORT := $(shell ./scripts/get-branch-ports.sh "$(BRANCH_NAME)" export 2>/dev/null | grep BACKEND_PORT | cut -d= -f2 || echo "8000")
export FRONTEND_PORT
export BACKEND_PORT

DOCKER_COMPOSE = docker compose
DOCKER_COMPOSE_APP = BRANCH_NAME=$(BRANCH_NAME) FRONTEND_PORT=$(FRONTEND_PORT) BACKEND_PORT=$(BACKEND_PORT) docker compose -f .docker/compose/app.yml
FRONTEND_DEV_URL = http://localhost:$(FRONTEND_PORT)
BACKEND_URL = http://localhost:$(BACKEND_PORT)

# Colors for output
CYAN = \033[0;36m
GREEN = \033[0;32m
YELLOW = \033[0;33m
RED = \033[0;31m
NC = \033[0m # No Color

# Help target - displays all available commands
help: ## Show this help message
	@echo "$(CYAN)╔════════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(CYAN)║          Durable Code Test - Docker Management            ║$(NC)"
	@echo "$(CYAN)╚════════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(GREEN)Core Commands:$(NC)"
	@echo "  $(YELLOW)make dev$(NC)          # Start development environment and open browser"
	@echo "  $(YELLOW)make dev-stop$(NC)     # Stop development environment"
	@echo "  $(YELLOW)make deploy$(NC)       # Deploy application to dev environment (requires infra)"
	@echo "  $(YELLOW)make status$(NC)       # Check container status"
	@echo ""
	@echo "$(GREEN)Available targets:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sed 's/^[^:]*://' | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}' | sort
	@echo ""

# Core targets
init: ## Initialize project (build images, install all git hooks)
	@echo "$(CYAN)Initializing project...$(NC)"
	@echo "$(YELLOW)Installing pre-commit framework...$(NC)"
	@pip3 install pre-commit 2>/dev/null || pip install pre-commit 2>/dev/null || echo "$(YELLOW)⚠ Pre-commit not installed - please install manually$(NC)"
	@echo "$(YELLOW)Installing pre-commit hooks...$(NC)"
	@pre-commit install 2>/dev/null || echo "$(YELLOW)⚠ Pre-commit hooks not installed$(NC)"
	@echo "$(YELLOW)Installing pre-push hooks...$(NC)"
	@pre-commit install --hook-type pre-push 2>/dev/null || echo "$(YELLOW)⚠ Pre-push hooks not installed$(NC)"
	@echo "$(YELLOW)Building Docker images...$(NC)"
	@$(DOCKER_COMPOSE_APP) build --no-cache
	@echo "$(GREEN)✓ Initialization complete!$(NC)"

# Development targets
dev-start: ## Start development environment with hot reload
	@echo "$(CYAN)Starting development environment...$(NC)"
	@$(DOCKER_COMPOSE_APP) up -d
	@echo "$(GREEN)✓ Development environment started!$(NC)"
	@echo "$(YELLOW)Frontend (Vite): $(FRONTEND_DEV_URL)$(NC)"
	@echo "$(YELLOW)Backend (FastAPI): $(BACKEND_URL)$(NC)"
	@echo "$(YELLOW)API Docs: $(BACKEND_URL)/docs$(NC)"

dev-stop: ## Stop development environment
	@echo "$(CYAN)Stopping development environment for branch: $(BRANCH_NAME)...$(NC)"
	@$(DOCKER_COMPOSE_APP) down
	@echo "$(GREEN)✓ Development environment stopped!$(NC)"

dev-restart: dev-stop dev-start ## Restart development environment

dev-logs: ## Show development logs (follow mode)
	@$(DOCKER_COMPOSE_APP) logs -f

dev: dev-start ## Start dev environment and open browser (main dev command)
	@echo "$(CYAN)Launching development environment...$(NC)"
	@sleep 3
	@echo "$(GREEN)Opening browser at $(FRONTEND_DEV_URL)...$(NC)"
	@if command -v xdg-open > /dev/null; then \
		xdg-open $(FRONTEND_DEV_URL); \
	elif command -v open > /dev/null; then \
		open $(FRONTEND_DEV_URL); \
	elif command -v start > /dev/null; then \
		start $(FRONTEND_DEV_URL); \
	else \
		echo "$(YELLOW)Please open your browser and navigate to $(FRONTEND_DEV_URL)$(NC)"; \
	fi

# Utility targets
status: ## Show status of all containers
	@echo "$(CYAN)Container Status:$(NC)"
	@docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "durable-code|NAMES" || echo "$(YELLOW)No containers running$(NC)"

clean: ## Remove all containers, networks, and volumes
	@echo "$(RED)⚠️  Warning: This will remove all containers, networks, and volumes!$(NC)"
	@echo "$(YELLOW)Press Ctrl+C to cancel, or wait 5 seconds to continue...$(NC)"
	@sleep 5
	@echo "$(CYAN)Cleaning up...$(NC)"
	@$(DOCKER_COMPOSE_APP) down -v --remove-orphans
	@docker system prune -f
	@echo "$(GREEN)✓ Cleanup complete!$(NC)"

shell-backend: ## Open shell in backend container
	@docker exec -it durable-code-backend-$(BRANCH_NAME)-dev /bin/bash

shell-frontend: ## Open shell in frontend container
	@docker exec -it durable-code-frontend-$(BRANCH_NAME)-dev /bin/sh

# Pre-commit hooks
install-hooks: ## Install pre-commit hooks
	@echo "$(CYAN)Installing pre-commit hooks...$(NC)"
	@which pre-commit > /dev/null 2>&1 || (echo "$(YELLOW)Installing pre-commit...$(NC)" && pip3 install pre-commit)
	@pre-commit install
	@echo "$(GREEN)✓ Pre-commit hooks installed!$(NC)"
	@echo "$(YELLOW)Hooks will run automatically on git commit$(NC)"

# Deployment targets
deploy: ## Deploy application to dev environment (assumes infrastructure is up)
	@echo "$(CYAN)Deploying application to development environment...$(NC)"
	@echo "$(YELLOW)Environment: $(ENV)$(NC)"
	@echo "$(YELLOW)This assumes infrastructure has been deployed via 'make infra-up'$(NC)"
	@echo ""
	@echo "$(YELLOW)Running deployment script...$(NC)"
	@if [ -n "$(AWS_PROFILE)" ]; then \
		export AWS_PROFILE=$(AWS_PROFILE) && ENV=$(ENV) ./infra/scripts/deploy-app.sh; \
	else \
		ENV=$(ENV) ./infra/scripts/deploy-app.sh; \
	fi
	@echo ""
	@echo "$(GREEN)✓ Deployment complete!$(NC)"
	@echo "$(YELLOW)Checking application URL...$(NC)"
	@echo "Your application should be available at:"
	@if [ -n "$(AWS_PROFILE)" ]; then \
		export AWS_PROFILE=$(AWS_PROFILE) && aws elbv2 describe-load-balancers --names durableai-$(ENV)-alb --query 'LoadBalancers[0].DNSName' --output text 2>/dev/null | sed 's/^/  http:\/\//'; \
	else \
		aws elbv2 describe-load-balancers --names durableai-$(ENV)-alb --query 'LoadBalancers[0].DNSName' --output text 2>/dev/null | sed 's/^/  http:\/\//'; \
	fi || echo "  $(RED)Unable to retrieve ALB URL - check AWS credentials$(NC)"

deploy-check: ## Check if infrastructure is deployed and ready
	@echo "$(CYAN)Checking infrastructure status...$(NC)"
	@if [ -n "$(AWS_PROFILE)" ]; then export AWS_PROFILE=$(AWS_PROFILE); fi && \
	if aws elbv2 describe-load-balancers --names durableai-$(ENV)-alb >/dev/null 2>&1; then \
		echo "$(GREEN)✓ Infrastructure appears to be deployed$(NC)"; \
		echo "$(YELLOW)ALB DNS:$(NC)"; \
		aws elbv2 describe-load-balancers --names durableai-$(ENV)-alb --query 'LoadBalancers[0].DNSName' --output text | sed 's/^/  http:\/\//'; \
	else \
		echo "$(RED)❌ Infrastructure not found!$(NC)"; \
		echo "$(YELLOW)Please run: make infra-up$(NC)"; \
		exit 1; \
	fi

# Include comprehensive linting and testing targets
-include Makefile.lint
-include Makefile.test
-include Makefile.gh
-include Makefile.infra
