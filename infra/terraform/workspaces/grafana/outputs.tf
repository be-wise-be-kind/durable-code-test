# Purpose: Output values from grafana infrastructure workspace
# Scope: Grafana resource identifiers for operational visibility
# Overview: Exports key identifiers from Grafana resources for operational tasks and debugging.
# Dependencies: Grafana resources created within this workspace
# Exports: Environment, workspace name, and resource counts
# Configuration: Outputs automatically reflect workspace state
# Environment: Values specific to workspace environment (dev/staging/prod)
# Related: dashboards.tf for resource definitions
# Implementation: Conditional outputs based on enable_observability flag

output "environment" {
  description = "Environment name"
  value       = local.environment
}

output "workspace_name" {
  description = "Terraform workspace name"
  value       = local.workspace_name
}

output "grafana_datasource_count" {
  description = "Number of Grafana datasources configured"
  value       = var.enable_observability ? 5 : 0
}

output "grafana_dashboard_count" {
  description = "Number of Grafana dashboards configured"
  value       = var.enable_observability ? 13 : 0
}
