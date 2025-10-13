#!/bin/bash
# Purpose: Unified deployment script for Terraform workspaces
# Scope: Handle deployment of base, runtime, or all infrastructure based on SCOPE parameter
# Overview: This script orchestrates Terraform deployments across workspace-separated infrastructure.
#     It ensures proper deployment order (base before runtime) and handles both individual
#     workspace deployments and full infrastructure deployment. The script delegates to
#     specific workspace deployment scripts for actual Terraform operations.
# Dependencies: workspace-deploy-base.sh, workspace-deploy-runtime.sh
# Usage: ./workspace-deploy.sh <env> <scope>
#   env: dev|staging|prod
#   scope: base|runtime|all

set -e

ENV=$1
SCOPE=$2
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Validate arguments
if [[ -z "$ENV" || -z "$SCOPE" ]]; then
    echo -e "${RED}Error: Missing required arguments${NC}"
    echo "Usage: $0 <env> <scope>"
    echo "  env: dev|staging|prod"
    echo "  scope: base|runtime|all"
    exit 1
fi

# Validate environment
if [[ ! "$ENV" =~ ^(dev|staging|prod)$ ]]; then
    echo -e "${RED}Error: Invalid environment '${ENV}'${NC}"
    echo "Valid environments: dev, staging, prod"
    exit 1
fi

# Validate scope
if [[ ! "$SCOPE" =~ ^(base|runtime|all)$ ]]; then
    echo -e "${RED}Error: Invalid scope '${SCOPE}'${NC}"
    echo "Valid scopes: base, runtime, all"
    exit 1
fi

echo -e "${CYAN}=== Terraform Workspace Deployment ===${NC}"
echo -e "${YELLOW}Environment: ${ENV}${NC}"
echo -e "${YELLOW}Scope: ${SCOPE}${NC}"
echo ""

case $SCOPE in
    base)
        echo -e "${BLUE}Deploying base infrastructure...${NC}"
        if "${SCRIPT_DIR}/workspace-deploy-base.sh" "$ENV"; then
            echo -e "${GREEN}✓ Base infrastructure deployed successfully${NC}"
        else
            echo -e "${RED}✗ Base infrastructure deployment failed${NC}"
            exit 1
        fi
        ;;

    runtime)
        echo -e "${GREEN}Deploying runtime infrastructure...${NC}"
        if "${SCRIPT_DIR}/workspace-deploy-runtime.sh" "$ENV"; then
            echo -e "${GREEN}✓ Runtime infrastructure deployed successfully${NC}"
        else
            echo -e "${RED}✗ Runtime infrastructure deployment failed${NC}"
            exit 1
        fi
        ;;

    all)
        echo -e "${YELLOW}Deploying all infrastructure (base + runtime)...${NC}"
        echo ""

        # Deploy base first
        echo -e "${BLUE}Step 1/2: Deploying base infrastructure...${NC}"
        if ! "${SCRIPT_DIR}/workspace-deploy-base.sh" "$ENV"; then
            echo -e "${RED}✗ Base infrastructure deployment failed${NC}"
            echo -e "${RED}Aborting deployment${NC}"
            exit 1
        fi
        echo -e "${GREEN}✓ Base infrastructure deployed${NC}"
        echo ""

        # Then deploy runtime
        echo -e "${GREEN}Step 2/2: Deploying runtime infrastructure...${NC}"
        if ! "${SCRIPT_DIR}/workspace-deploy-runtime.sh" "$ENV"; then
            echo -e "${RED}✗ Runtime infrastructure deployment failed${NC}"
            echo -e "${YELLOW}Note: Base infrastructure was deployed successfully${NC}"
            exit 1
        fi
        echo -e "${GREEN}✓ Runtime infrastructure deployed${NC}"
        echo ""
        echo -e "${GREEN}✓ All infrastructure deployed successfully!${NC}"
        ;;
esac

echo ""
echo -e "${CYAN}Deployment complete!${NC}"
echo -e "${YELLOW}To view infrastructure status, run: just infra-status ENV=${ENV}${NC}"
echo -e "${YELLOW}To view outputs, run: just infra-output SCOPE=${SCOPE} ENV=${ENV}${NC}"