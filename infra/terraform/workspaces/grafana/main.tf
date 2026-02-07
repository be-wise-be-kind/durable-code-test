# Purpose: Main configuration for grafana infrastructure workspace containing Grafana API resources
# Scope: Terraform backend configuration, provider requirements, and workspace-aware local values
# Overview: Establishes the foundation for the grafana infrastructure workspace which manages
#     Grafana API resources (datasources, folders, dashboards, organization preferences) via the
#     Grafana Terraform provider. Resources are separated from the runtime workspace to enable
#     independent dashboard deployments without refreshing ECS, ALB, WAF, or other AWS infrastructure.
#     Uses the same S3 backend for state management with workspace-specific state files. Depends on
#     the runtime workspace having deployed the observability EC2 instance and on an active SSM
#     port-forward tunnel to the Grafana API.
# Dependencies: Grafana provider, S3 backend bucket, DynamoDB lock table, backend-config files
# Exports: Local values for workspace naming, environment extraction, and common tags
# Configuration: Backend configuration provided via backend-config/grafana-{env}.hcl files
# Environment: Supports dev, staging, and production with workspace-based separation
# Related: data.tf for runtime remote state reference, dashboards.tf for Grafana resources
# Implementation: Uses Terraform workspace naming convention grafana-{env} for state isolation

terraform {
  required_version = ">= 1.0"

  backend "s3" {
    # Backend configuration is provided via backend-config file
    # See infra/terraform/backend-config/grafana-{env}.hcl
  }

  required_providers {
    grafana = {
      source  = "grafana/grafana"
      version = "~> 3.0"
    }
  }
}

locals {
  workspace_name = "grafana-${var.environment}"
  environment    = var.environment

  common_tags = {
    Environment = local.environment
    Workspace   = local.workspace_name
    ManagedBy   = "Terraform"
    Scope       = "grafana"
  }
}
