#!/bin/bash
# Purpose: Deploy runtime infrastructure workspace containing ephemeral ECS resources
# Scope: Manages ECS cluster, services, task definitions, ALB listeners via Terraform workspace
# Overview: This script automates the deployment of runtime infrastructure in the specified
#     environment using Terraform workspaces. It handles workspace initialization, selection,
#     and application of runtime configurations. The script ensures the base workspace is
#     deployed first (as a dependency), initializes the runtime workspace with appropriate
#     backend configuration, and applies the runtime infrastructure changes. It includes
#     safety checks, proper error handling, and informative output for operators. The runtime
#     workspace can be safely destroyed and recreated for cost optimization without affecting
#     persistent base resources like VPC, NAT Gateways, or ECR repositories.
# Dependencies: Terraform, AWS CLI, base workspace must be deployed, backend S3
# Exports: None (side effects: deploys AWS resources, modifies Terraform state)
# Configuration: Environment parameter required, uses backend-config and tfvars files
# Environment: Supports dev, staging, prod with environment-specific configurations
# Related: workspace-init.sh, workspace-deploy-base.sh, workspace-destroy-runtime.sh
# Implementation: Sequential execution with dependency validation and error handling

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored messages
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to print section headers
print_header() {
    echo ""
    echo "================================================"
    echo "$1"
    echo "================================================"
}

# Check for required arguments
if [[ $# -lt 1 ]]; then
    print_message "$RED" "Error: Environment argument required"
    echo "Usage: $0 <environment> [additional terraform args]"
    echo "Example: $0 dev"
    echo "Example: $0 prod -auto-approve"
    exit 1
fi

ENV=$1
shift # Remove first argument, leaving any additional args

# Validate environment
if [[ ! "$ENV" =~ ^(dev|staging|prod)$ ]]; then
    print_message "$RED" "Error: Invalid environment. Must be dev, staging, or prod"
    exit 1
fi

# Set paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
RUNTIME_DIR="${PROJECT_ROOT}/infra/terraform/workspaces/runtime"
BASE_DIR="${PROJECT_ROOT}/infra/terraform/workspaces/base"
BACKEND_CONFIG="${PROJECT_ROOT}/infra/terraform/backend-config/runtime-${ENV}.hcl"
TFVARS_FILE="${RUNTIME_DIR}/terraform.tfvars"

# Check if terraform is installed
if ! command -v terraform &> /dev/null; then
    print_message "$RED" "Error: Terraform is not installed"
    exit 1
fi

print_header "Runtime Workspace Deployment for ${ENV}"

# Check if backend config exists
if [[ ! -f "$BACKEND_CONFIG" ]]; then
    print_message "$YELLOW" "Warning: Backend config not found at $BACKEND_CONFIG"
    print_message "$YELLOW" "Creating backend config from template..."

    # Create backend config
    cat > "$BACKEND_CONFIG" << EOF
bucket         = "${PROJECT_NAME}-terraform-state"
key            = "runtime/${ENV}/terraform.tfstate"
region         = "us-west-2"
encrypt        = true
use_lockfile   = true
EOF
    print_message "$GREEN" "✓ Backend config created"
fi

# Check if base workspace is deployed
print_message "$CYAN" "Checking base workspace status..."
cd "$BASE_DIR"

# Initialize base workspace to check its status
terraform init -backend-config="${PROJECT_ROOT}/infra/terraform/backend-config/base-${ENV}.hcl" > /dev/null 2>&1

# Select or create base workspace
terraform workspace select "base-${ENV}" 2>/dev/null || {
    print_message "$RED" "Error: Base workspace 'base-${ENV}' not found"
    print_message "$YELLOW" "Please deploy base workspace first using:"
    echo "  ./infra/scripts/workspace-deploy-base.sh ${ENV}"
    exit 1
}

# Check if base has outputs (indicating it's deployed)
if ! terraform output -json > /dev/null 2>&1; then
    print_message "$RED" "Error: Base workspace appears to not be deployed"
    print_message "$YELLOW" "Please deploy base workspace first using:"
    echo "  ./infra/scripts/workspace-deploy-base.sh ${ENV}"
    exit 1
fi

print_message "$GREEN" "✓ Base workspace is deployed"

# Change to runtime directory
cd "$RUNTIME_DIR"

# Initialize runtime workspace
print_message "$CYAN" "Initializing runtime workspace..."
terraform init -backend-config="$BACKEND_CONFIG"

# Select or create workspace
WORKSPACE_NAME="runtime-${ENV}"
print_message "$CYAN" "Selecting workspace: $WORKSPACE_NAME"
terraform workspace select "$WORKSPACE_NAME" 2>/dev/null || {
    print_message "$YELLOW" "Workspace doesn't exist, creating..."
    terraform workspace new "$WORKSPACE_NAME"
}

# Create tfvars file if it doesn't exist
if [[ ! -f "$TFVARS_FILE" ]]; then
    print_message "$YELLOW" "Creating terraform.tfvars from example..."
    if [[ -f "${RUNTIME_DIR}/terraform.tfvars.example" ]]; then
        cp "${RUNTIME_DIR}/terraform.tfvars.example" "$TFVARS_FILE"
        # Update environment in tfvars
        sed -i.bak "s/environment = \".*\"/environment = \"${ENV}\"/" "$TFVARS_FILE"
        rm -f "${TFVARS_FILE}.bak"
        print_message "$GREEN" "✓ Created terraform.tfvars - please review and adjust as needed"
    fi
fi

# Plan deployment
print_header "Planning Runtime Infrastructure"
print_message "$CYAN" "Running terraform plan..."
terraform plan -out=runtime.tfplan "$@"

# Ask for confirmation if not auto-approved
if [[ ! " $* " =~ " -auto-approve " ]]; then
    echo ""
    read -p "Do you want to apply this plan? (yes/no): " -n 3 -r
    echo ""
    if [[ ! $REPLY =~ ^yes$ ]]; then
        print_message "$YELLOW" "Deployment cancelled"
        rm -f runtime.tfplan
        exit 0
    fi
fi

# Apply deployment
print_header "Applying Runtime Infrastructure"
print_message "$CYAN" "Deploying runtime infrastructure..."
terraform apply runtime.tfplan

# Clean up plan file
rm -f runtime.tfplan

# Show outputs
print_header "Deployment Complete"
print_message "$GREEN" "✓ Runtime infrastructure deployed successfully!"
echo ""
print_message "$CYAN" "Key Outputs:"
echo "---"
terraform output -json | jq -r 'to_entries[] | "\(.key): \(.value.value)"' 2>/dev/null || terraform output

# Show next steps
echo ""
print_message "$CYAN" "Next Steps:"
echo "1. Access application at: $(terraform output -raw application_url_http 2>/dev/null || echo 'Check outputs above')"
echo "2. View ECS services: aws ecs list-services --cluster $(terraform output -raw ecs_cluster_name 2>/dev/null || echo "${PROJECT_NAME}-${ENV}-cluster")"
echo "3. Check logs in CloudWatch: $(terraform output -raw backend_log_group 2>/dev/null || echo "/ecs/${PROJECT_NAME}-${ENV}/backend")"
echo ""
print_message "$YELLOW" "To destroy runtime infrastructure (preserving base):"
echo "  ${SCRIPT_DIR}/workspace-destroy-runtime.sh ${ENV}"