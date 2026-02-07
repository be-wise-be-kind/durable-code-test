# Purpose: Variable definitions for grafana infrastructure workspace configuration
# Scope: Input variables for Grafana provider connectivity and conditional deployment
# Overview: Defines all input variables required for the grafana infrastructure workspace,
#     which manages Grafana API resources (datasources, folders, dashboards). Variables include
#     environment selection, Grafana provider connectivity settings, and the observability feature
#     flag for conditional resource creation.
# Dependencies: Used by provider configuration and all grafana workspace resources
# Exports: Variable values accessible throughout grafana workspace configuration
# Configuration: Override defaults using terraform.tfvars or -var-file parameter
# Environment: Environment-aware configuration supporting dev, staging, and production
# Related: providers.tf for Grafana provider usage, data.tf for remote state reference
# Implementation: Minimal variable set focused on Grafana connectivity and deployment control

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "aws_region" {
  description = "AWS region (used for CloudWatch datasource and remote state lookup)"
  type        = string
  default     = "us-west-2"
}

variable "enable_observability" {
  description = "Enable Grafana observability resources (datasources, dashboards)"
  type        = bool
  default     = false
}

variable "grafana_admin_password" {
  description = "Admin password for Grafana UI"
  type        = string
  default     = "admin"
  sensitive   = true
}

variable "grafana_url" {
  description = "Grafana API URL for Terraform provider. Requires SSM port-forward tunnel: aws ssm start-session --target <instance-id> --document-name AWS-StartPortForwardingSession --parameters portNumber=3001,localPortNumber=3001"
  type        = string
  default     = "http://localhost:3001/grafana/"
}
