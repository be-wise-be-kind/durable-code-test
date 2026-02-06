# Purpose: Main configuration for runtime infrastructure workspace containing ephemeral resources
# Scope: Terraform backend configuration, provider requirements, and workspace-aware local values
# Overview: This file establishes the foundation for the runtime infrastructure workspace which manages
#     ephemeral resources that can be destroyed and recreated frequently without significant impact.
#     It configures the S3 backend for state management with workspace-specific state files, defines
#     provider requirements for AWS resources, and establishes workspace-aware naming conventions
#     and tagging strategies. The runtime workspace includes ECS clusters, task definitions, services,
#     ALB listeners and target groups, auto-scaling policies, and CloudWatch resources. These resources
#     depend on the base workspace infrastructure via data sources and can be safely destroyed for
#     cost optimization during non-business hours or development cycles.
# Dependencies: AWS provider, S3 backend bucket, DynamoDB lock table, backend-config files, base workspace outputs
# Exports: Local values for workspace naming, environment extraction, and common tags
# Configuration: Backend configuration provided via backend-config/runtime-{env}.hcl files
# Environment: Supports dev, staging, and production with workspace-based separation
# Related: data.tf, ecs.tf, alb-listeners.tf, outputs.tf in this workspace
# Implementation: Uses Terraform workspace naming convention runtime-{env} for state isolation

terraform {
  required_version = ">= 1.0"

  backend "s3" {
    # Backend configuration is provided via backend-config file
    # See infra/terraform/backend-config/runtime-{env}.hcl
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    grafana = {
      source  = "grafana/grafana"
      version = "~> 3.0"
    }
  }
}

locals {
  workspace_name = "runtime-${var.environment}"
  environment    = var.environment

  common_tags = {
    Environment = local.environment
    Workspace   = local.workspace_name
    ManagedBy   = "Terraform"
    Scope       = "runtime"
  }
}