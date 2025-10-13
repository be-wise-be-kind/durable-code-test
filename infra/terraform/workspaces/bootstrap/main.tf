# Purpose: Bootstrap workspace for permanent GitHub Actions authentication infrastructure
# Scope: GitHub OIDC provider and IAM role - never destroyed by automated workflows
# Overview: This workspace manages the foundational resources required for GitHub Actions
#     to authenticate with AWS and manage infrastructure. It contains only the GitHub
#     OIDC provider and the IAM role with policies that GitHub Actions uses. These
#     resources are permanent and should never be destroyed by automated workflows,
#     as destroying them would break GitHub Actions' ability to deploy infrastructure.
#     The S3 backend and DynamoDB table are created manually via setup-terraform-backend.sh
#     and are not managed by Terraform to avoid circular dependencies.
# Dependencies: S3 bucket and DynamoDB table (created via setup-terraform-backend.sh)
# Exports: GitHub OIDC provider ARN and IAM role ARN for use by GitHub Actions
# Configuration: Backend configuration provided via backend-config/bootstrap-{env}.hcl
# Environment: Supports dev, staging, and production
# Related: base and runtime workspaces depend on this for GitHub Actions authentication
# Implementation: Minimal workspace containing only authentication resources

terraform {
  required_version = ">= 1.0"

  backend "s3" {
    # Backend configuration is provided via backend-config file
    # See infra/terraform/backend-config/bootstrap-{env}.hcl
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

locals {
  workspace_name = terraform.workspace
  # Extract environment from workspace name (e.g., bootstrap-dev -> dev)
  environment = length(split("-", terraform.workspace)) > 1 ? split("-", terraform.workspace)[1] : "dev"

  common_tags = {
    Environment = local.environment
    Workspace   = local.workspace_name
    ManagedBy   = "Terraform"
    Scope       = "bootstrap"
    Purpose     = "GitHub Actions Authentication"
  }
}
