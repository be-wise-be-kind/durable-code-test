#!/bin/bash
# Purpose: Display status information for Terraform workspaces
# Scope: Terraform workspace inspection and status reporting
# Overview: This script provides a comprehensive view of the current state of both
#     base and runtime workspaces for a given environment. It shows which resources
#     are deployed, workspace selection status, and basic output values. Useful for
#     operators to quickly understand the infrastructure state before making changes.
# Dependencies: Terraform CLI, AWS credentials, initialized workspaces
# Usage: ./workspace-status.sh [dev|staging|prod]
# Example: ./workspace-status.sh dev

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Function to print colored messages
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to print usage information
usage() {
    echo "Usage: $0 [dev|staging|prod]"
    echo ""
    echo "Display status information for Terraform workspaces."
    echo ""
    echo "Arguments:"
    echo "  env  Environment to check (dev, staging, or prod)"
    echo ""
    echo "Example:"
    echo "  $0 dev  # Show status for development environment"
    exit 1
}

# Validate arguments
if [ $# -ne 1 ]; then
    print_message "$RED" "Error: Environment argument required"
    usage
fi

ENV=$1

# Validate environment argument
if [[ "$ENV" != "dev" && "$ENV" != "staging" && "$ENV" != "prod" ]]; then
    print_message "$RED" "Error: Invalid environment '$ENV'. Must be 'dev', 'staging', or 'prod'"
    usage
fi

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"

print_message "$CYAN" "========================================="
print_message "$CYAN" "Terraform Workspace Status for $ENV"
print_message "$CYAN" "========================================="
echo ""

# Function to check workspace status
check_workspace() {
    local workspace_type=$1
    local workspace_name="${workspace_type}-${ENV}"
    local workspace_dir="${PROJECT_ROOT}/infra/terraform/workspaces/${workspace_type}"

    print_message "$MAGENTA" "--- ${workspace_type^^} Workspace ---"

    # Check if workspace directory exists
    if [ ! -d "$workspace_dir" ]; then
        print_message "$YELLOW" "⚠  Directory not found: $workspace_dir"
        print_message "$YELLOW" "   (Expected in PR1 - will be created in PR2/PR3)"
        echo ""
        return
    fi

    # Check if terraform is initialized
    if [ ! -d "$workspace_dir/.terraform" ]; then
        print_message "$YELLOW" "⚠  Workspace not initialized"
        print_message "$YELLOW" "   Run: ./infra/scripts/workspace-init.sh $workspace_type $ENV"
        echo ""
        return
    fi

    cd "$workspace_dir"

    # Check current workspace
    current_workspace=$(terraform workspace show 2>/dev/null || echo "none")
    if [ "$current_workspace" == "$workspace_name" ]; then
        print_message "$GREEN" "✓ Workspace selected: $workspace_name"
    else
        print_message "$YELLOW" "⚠  Different workspace selected: $current_workspace"
        print_message "$YELLOW" "   Expected: $workspace_name"
    fi

    # Try to get outputs (will fail if no state exists)
    if terraform output -json 2>/dev/null 1>/dev/null; then
        print_message "$GREEN" "✓ State file exists"

        # Show key outputs if they exist
        outputs=$(terraform output -json 2>/dev/null)
        if [ -n "$outputs" ] && [ "$outputs" != "{}" ]; then
            print_message "$CYAN" "  Key outputs:"
            echo "$outputs" | jq -r 'keys[]' 2>/dev/null | head -5 | while read -r key; do
                echo "    - $key"
            done
        else
            print_message "$YELLOW" "  No outputs defined"
        fi
    else
        print_message "$YELLOW" "⚠  No state file or resources"
    fi

    # List available workspaces
    print_message "$CYAN" "  Available workspaces:"
    terraform workspace list 2>/dev/null | grep -E "^\s+${workspace_type}-" | sed 's/^/  /' || echo "    None found"

    echo ""
}

# Check AWS credentials
print_message "$CYAN" "AWS Configuration:"
if aws sts get-caller-identity &>/dev/null; then
    account=$(aws sts get-caller-identity --query Account --output text)
    user=$(aws sts get-caller-identity --query Arn --output text)
    print_message "$GREEN" "✓ AWS credentials configured"
    echo "  Account: $account"
    echo "  User: $user"
else
    print_message "$RED" "✗ AWS credentials not configured or invalid"
fi
echo ""

# Check base workspace
check_workspace "base"

# Check runtime workspace
check_workspace "runtime"

# Show related Just targets
print_message "$CYAN" "Related Just targets for $ENV environment:"
echo "  just infra-up-base ENV=$ENV      # Deploy base infrastructure"
echo "  just infra-up-runtime ENV=$ENV   # Deploy runtime infrastructure"
echo "  just infra-down-runtime ENV=$ENV # Destroy runtime infrastructure"
echo "  just infra-status ENV=$ENV        # Show this status"
echo ""

# Check for any running resources (if state exists)
if [ -d "${PROJECT_ROOT}/infra/terraform" ]; then
    cd "${PROJECT_ROOT}/infra/terraform"
    if [ -f "terraform.tfstate" ] || [ -f ".terraform/terraform.tfstate" ]; then
        print_message "$YELLOW" "⚠  Legacy state file detected in main terraform directory"
        print_message "$YELLOW" "   Migration to workspaces will be needed (PR2-PR3)"
    fi
fi

print_message "$GREEN" "✓ Status check complete!"