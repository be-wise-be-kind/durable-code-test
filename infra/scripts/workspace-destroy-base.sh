#!/bin/bash
# Purpose: Destroy base infrastructure workspace containing persistent resources
# Scope: Manages destruction of VPC, NAT, ECR, Route53, ACM, ALB base resources via Terraform
# Overview: This script automates the destruction of base infrastructure resources. It should
#     only be called when completely tearing down an environment, as these resources are
#     expensive to recreate and may have dependencies. The script includes multiple safety
#     checks and requires explicit confirmation. Base resources include VPC, subnets, NAT
#     gateways, Internet Gateway, ECR repositories, Route53 zones, ACM certificates, and
#     the Application Load Balancer itself.
# Dependencies: Terraform, AWS credentials, initialized base workspace
# Usage: ./workspace-destroy-base.sh [dev|staging|prod]
# Environment: Requires AWS credentials and proper IAM permissions for resource deletion
# Configuration: Uses backend-config/base-{env}.hcl and environments/{env}.tfvars
# Warning: This is a destructive operation that removes critical infrastructure

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

echo -e "${RED}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${RED}║  ⚠️  CRITICAL: Destroying BASE infrastructure! ⚠️          ║${NC}"
echo -e "${RED}║                                                            ║${NC}"
echo -e "${RED}║  This is a DANGEROUS operation that will destroy:         ║${NC}"
echo -e "${RED}║   - VPC and all networking resources                      ║${NC}"
echo -e "${RED}║   - NAT Gateways (costs money to recreate)               ║${NC}"
echo -e "${RED}║   - ECR repositories (container images will be lost)      ║${NC}"
echo -e "${RED}║   - Route53 zones and DNS records                         ║${NC}"
echo -e "${RED}║   - ACM certificates                                      ║${NC}"
echo -e "${RED}║   - Application Load Balancer                             ║${NC}"
echo -e "${RED}║                                                            ║${NC}"
echo -e "${RED}║  Environment: ${ENV}                                        ║${NC}"
echo -e "${RED}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Navigate to base workspace
cd "$(dirname "$0")/../terraform/workspaces/base"

# Check if workspace is initialized
if [ ! -d ".terraform" ]; then
    echo -e "${RED}Error: Base workspace not initialized${NC}"
    echo "Run 'just infra-init SCOPE=base ENV=${ENV}' first"
    exit 1
fi

# Select workspace
echo -e "${YELLOW}Selecting workspace base-${ENV}...${NC}"
terraform workspace select "base-${ENV}" || {
    echo -e "${RED}Error: Workspace base-${ENV} does not exist${NC}"
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
echo -e "${RED}════════════════════════════════════════════════════════════${NC}"
echo -e "${RED}  FINAL WARNING: This will destroy ALL base infrastructure!${NC}"
echo -e "${RED}  This operation is IRREVERSIBLE and EXPENSIVE to undo!${NC}"
echo -e "${RED}════════════════════════════════════════════════════════════${NC}"
echo ""

# Multiple confirmation prompts for safety
read -p "Are you ABSOLUTELY SURE you want to destroy base infrastructure? (yes/no): " -r
echo ""
if [[ ! $REPLY =~ ^[Yy]es$ ]]; then
    echo -e "${GREEN}Destruction cancelled - good choice!${NC}"
    rm -f destroy.tfplan
    exit 0
fi

# Second confirmation for production
if [[ "$ENV" == "prod" ]]; then
    echo -e "${RED}This is PRODUCTION environment!${NC}"
    read -p "Type 'destroy production base' to confirm: " -r
    echo ""
    if [[ "$REPLY" != "destroy production base" ]]; then
        echo -e "${GREEN}Destruction cancelled${NC}"
        rm -f destroy.tfplan
        exit 0
    fi
fi

# Apply destruction
echo -e "${RED}Destroying base infrastructure...${NC}"
echo -e "${YELLOW}This may take several minutes...${NC}"
terraform apply destroy.tfplan

# Clean up plan file
rm -f destroy.tfplan

echo -e "${GREEN}✓ Base infrastructure destroyed${NC}"
echo ""
echo -e "${YELLOW}All base resources have been removed.${NC}"
echo -e "${YELLOW}To recreate, run: just infra-up SCOPE=base ENV=${ENV}${NC}"
echo -e "${YELLOW}Note: NAT Gateway creation can take 5-10 minutes${NC}"