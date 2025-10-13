#!/bin/bash
# Purpose: Destroy runtime infrastructure workspace containing ephemeral resources
# Scope: Manages destruction of ECS cluster, services, task definitions, ALB listeners via Terraform
# Overview: This script automates the destruction of runtime infrastructure resources that can be
#     safely removed without affecting base infrastructure. It handles workspace selection and
#     executes terraform destroy for the runtime workspace. The script includes safety prompts
#     and provides colored output for better visibility. Runtime resources include ECS services,
#     task definitions, ALB target groups and listeners, CloudWatch logs, and IAM roles.
# Dependencies: Terraform, AWS credentials, initialized runtime workspace
# Usage: ./workspace-destroy-runtime.sh [dev|staging|prod]
# Environment: Requires AWS credentials and proper IAM permissions for resource deletion
# Configuration: Uses backend-config/runtime-{env}.hcl and environments/{env}.tfvars
# Error Handling: Exits on any error with proper error messages

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get environment parameter
ENV=${1:-dev}

if [[ -z "$ENV" ]]; then
    echo -e "${RED}Error: Environment parameter required${NC}"
    echo "Usage: $0 [dev|staging|prod]"
    exit 1
fi

echo -e "${YELLOW}Destroying runtime infrastructure for ${ENV} environment...${NC}"

# Navigate to runtime workspace
cd "$(dirname "$0")/../terraform/workspaces/runtime"

# Check if workspace is initialized
if [ ! -d ".terraform" ]; then
    echo -e "${RED}Error: Runtime workspace not initialized${NC}"
    echo "Run 'just infra-init SCOPE=runtime ENV=${ENV}' first"
    exit 1
fi

# Select workspace
echo -e "${YELLOW}Selecting workspace runtime-${ENV}...${NC}"
terraform workspace select "runtime-${ENV}" || {
    echo -e "${RED}Error: Workspace runtime-${ENV} does not exist${NC}"
    exit 1
}

# Check tfvars file
TFVARS_FILE="../../environments/${ENV}.tfvars"
if [ ! -f "$TFVARS_FILE" ]; then
    echo -e "${RED}Error: tfvars file not found: ${TFVARS_FILE}${NC}"
    exit 1
fi

# Plan destruction to show what will be destroyed
echo -e "${YELLOW}Planning destruction (showing what will be removed)...${NC}"
terraform plan -destroy -var-file="$TFVARS_FILE" -out=destroy.tfplan

echo ""
echo -e "${YELLOW}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${YELLOW}║  The following runtime resources will be destroyed:       ║${NC}"
echo -e "${YELLOW}║   - ECS services (frontend and backend)                   ║${NC}"
echo -e "${YELLOW}║   - ECS task definitions                                  ║${NC}"
echo -e "${YELLOW}║   - ALB target groups and listeners                       ║${NC}"
echo -e "${YELLOW}║   - CloudWatch log groups                                 ║${NC}"
echo -e "${YELLOW}║   - IAM roles and policies                                ║${NC}"
echo -e "${YELLOW}║                                                            ║${NC}"
echo -e "${YELLOW}║  Base infrastructure will be preserved.                   ║${NC}"
echo -e "${YELLOW}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Prompt for confirmation
read -p "Are you sure you want to destroy runtime infrastructure? (yes/no): " -r
echo ""
if [[ ! $REPLY =~ ^[Yy]es$ ]]; then
    echo -e "${YELLOW}Destruction cancelled${NC}"
    rm -f destroy.tfplan
    exit 0
fi

# Apply destruction
echo -e "${YELLOW}Destroying runtime infrastructure...${NC}"
terraform apply destroy.tfplan

# Clean up plan file
rm -f destroy.tfplan

echo -e "${GREEN}✓ Runtime infrastructure destroyed successfully${NC}"
echo ""
echo -e "${GREEN}Runtime resources have been removed.${NC}"
echo -e "${GREEN}Base infrastructure (VPC, NAT, ECR) remains intact.${NC}"