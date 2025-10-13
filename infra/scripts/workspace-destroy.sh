#!/bin/bash
# Purpose: Unified destruction script for Terraform workspaces
# Scope: Handle destruction of runtime or all infrastructure based on SCOPE parameter
# Overview: This script orchestrates Terraform destruction across workspace-separated infrastructure.
#     It ensures proper destruction order (runtime before base) and includes safety checks to
#     prevent accidental destruction of base infrastructure. The script delegates to specific
#     workspace destruction scripts for actual Terraform operations. Base infrastructure can
#     only be destroyed as part of 'all' scope with explicit confirmation.
# Dependencies: workspace-destroy-runtime.sh, workspace-destroy-base.sh
# Usage: ./workspace-destroy.sh <env> <scope>
#   env: dev|staging|prod
#   scope: runtime|all (base alone is not allowed)

set -e

ENV=$1
SCOPE=$2
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Validate arguments
if [[ -z "$ENV" || -z "$SCOPE" ]]; then
    echo -e "${RED}Error: Missing required arguments${NC}"
    echo "Usage: $0 <env> <scope>"
    echo "  env: dev|staging|prod"
    echo "  scope: runtime|all"
    echo ""
    echo "Note: 'base' scope is not allowed for destroy operations."
    echo "      Use 'all' with CONFIRM=destroy-base to destroy base infrastructure."
    exit 1
fi

# Validate environment
if [[ ! "$ENV" =~ ^(dev|staging|prod)$ ]]; then
    echo -e "${RED}Error: Invalid environment '${ENV}'${NC}"
    echo "Valid environments: dev, staging, prod"
    exit 1
fi

# Validate scope
if [[ ! "$SCOPE" =~ ^(runtime|all)$ ]]; then
    if [[ "$SCOPE" == "base" ]]; then
        echo -e "${RED}Error: Direct base destruction not allowed${NC}"
        echo "Base infrastructure is protected from accidental deletion."
        echo "To destroy base infrastructure, use:"
        echo "  SCOPE=all CONFIRM=destroy-base $0 ${ENV} all"
    else
        echo -e "${RED}Error: Invalid scope '${SCOPE}'${NC}"
    fi
    echo "Valid scopes for destroy: runtime, all"
    exit 1
fi

echo -e "${CYAN}=== Terraform Workspace Destruction ===${NC}"
echo -e "${YELLOW}Environment: ${ENV}${NC}"
echo -e "${YELLOW}Scope: ${SCOPE}${NC}"
echo ""

case $SCOPE in
    runtime)
        echo -e "${YELLOW}Destroying runtime infrastructure...${NC}"
        echo -e "${GREEN}Note: Base infrastructure (VPC, NAT, ECR) will be preserved${NC}"
        echo ""

        if "${SCRIPT_DIR}/workspace-destroy-runtime.sh" "$ENV"; then
            echo -e "${GREEN}✓ Runtime infrastructure destroyed successfully${NC}"
        else
            echo -e "${RED}✗ Runtime infrastructure destruction failed${NC}"
            exit 1
        fi
        ;;

    all)
        echo -e "${RED}╔════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${RED}║  ⚠️  WARNING: Destroying ALL infrastructure! ⚠️            ║${NC}"
        echo -e "${RED}║                                                            ║${NC}"
        echo -e "${RED}║  This will destroy:                                       ║${NC}"
        echo -e "${RED}║   - Runtime resources (ECS, ALB listeners, services)      ║${NC}"
        echo -e "${RED}║   - Base resources (VPC, NAT, ECR, Route53, ALB)         ║${NC}"
        echo -e "${RED}║                                                            ║${NC}"
        echo -e "${RED}║  This operation is IRREVERSIBLE!                          ║${NC}"
        echo -e "${RED}╚════════════════════════════════════════════════════════════╝${NC}"
        echo ""

        # Check for confirmation
        if [[ "$CONFIRM" != "destroy-base" ]]; then
            echo -e "${RED}Error: Full infrastructure destruction requires confirmation${NC}"
            echo -e "${YELLOW}To proceed, run:${NC}"
            echo "  CONFIRM=destroy-base $0 ${ENV} all"
            exit 1
        fi

        echo -e "${YELLOW}Confirmation received. Proceeding with full destruction...${NC}"
        echo ""

        # Destroy runtime first
        echo -e "${YELLOW}Step 1/2: Destroying runtime infrastructure...${NC}"
        if ! "${SCRIPT_DIR}/workspace-destroy-runtime.sh" "$ENV"; then
            echo -e "${RED}✗ Runtime infrastructure destruction failed${NC}"
            echo -e "${YELLOW}Aborting. Base infrastructure remains intact.${NC}"
            exit 1
        fi
        echo -e "${GREEN}✓ Runtime infrastructure destroyed${NC}"
        echo ""

        # Then destroy base
        echo -e "${BLUE}Step 2/2: Destroying base infrastructure...${NC}"
        if ! "${SCRIPT_DIR}/workspace-destroy-base.sh" "$ENV"; then
            echo -e "${RED}✗ Base infrastructure destruction failed${NC}"
            echo -e "${YELLOW}Warning: Partial destruction may have occurred${NC}"
            exit 1
        fi
        echo -e "${GREEN}✓ Base infrastructure destroyed${NC}"
        echo ""
        echo -e "${GREEN}✓ All infrastructure destroyed successfully${NC}"
        ;;
esac

echo ""
echo -e "${CYAN}Destruction complete!${NC}"

# Provide helpful next steps
if [[ "$SCOPE" == "runtime" ]]; then
    echo -e "${YELLOW}Base infrastructure remains deployed.${NC}"
    echo -e "${YELLOW}To redeploy runtime: just infra-up SCOPE=runtime ENV=${ENV}${NC}"
else
    echo -e "${YELLOW}All infrastructure has been destroyed.${NC}"
    echo -e "${YELLOW}To redeploy: just infra-up SCOPE=all ENV=${ENV}${NC}"
fi