# Purpose: Main configuration for base infrastructure workspace containing persistent resources
# Scope: Terraform backend configuration, provider requirements, and workspace-aware local values
# Overview: This file establishes the foundation for the base infrastructure workspace which manages
#     persistent resources that are expensive to recreate and should survive runtime deployments.
#     It configures the S3 backend for state management with workspace-specific state files, defines
#     provider requirements for AWS resources, and establishes workspace-aware naming conventions
#     and tagging strategies. The base workspace includes VPC, NAT Gateways, ECR repositories,
#     Route53 zones, ACM certificates, and the Application Load Balancer itself. These resources
#     form the foundation that runtime resources depend upon via data sources.
# Dependencies: AWS provider, S3 backend bucket, DynamoDB lock table, backend-config files
# Exports: Local values for workspace naming, environment extraction, and common tags
# Configuration: Backend configuration provided via backend-config/base-{env}.hcl files
# Environment: Supports dev, staging, and production with workspace-based separation
# Related: networking.tf, ecr.tf, dns.tf, alb.tf, outputs.tf in this workspace
# Implementation: Uses Terraform workspace naming convention base-{env} for state isolation

terraform {
  required_version = ">= 1.0"

  backend "s3" {
    # Backend configuration is provided via backend-config file
    # See infra/terraform/backend-config/base-{env}.hcl
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

locals {
  workspace_name = "base-${var.environment}"
  environment    = var.environment

  common_tags = {
    Environment = local.environment
    Workspace   = local.workspace_name
    ManagedBy   = "Terraform"
    Scope       = "base"
  }
}