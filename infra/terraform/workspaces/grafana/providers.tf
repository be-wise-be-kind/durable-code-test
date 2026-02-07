# Purpose: Grafana provider configuration for dashboard and datasource management
# Scope: Provider configuration for Grafana API connectivity via SSM port-forward tunnel
# Overview: Configures the Grafana Terraform provider for API-based management of datasources,
#     folders, dashboards, and organization preferences. Connects via an SSM port-forward tunnel
#     (localhost:3001) to the Grafana instance running on the observability EC2 instance. Retry
#     settings accommodate Grafana startup delays after EC2 provisioning.
# Dependencies: Active SSM port-forward tunnel to observability EC2 instance
# Exports: Configured Grafana provider for use by all resources in grafana workspace
# Configuration: URL and credentials via variables, retry settings for resilience
# Environment: Same provider configuration across dev/staging/prod environments
# Related: variables.tf for grafana_url and grafana_admin_password
# Implementation: Direct Grafana API connection with retry logic for tunnel stability

provider "grafana" {
  url        = var.grafana_url
  auth       = "admin:${var.grafana_admin_password}"
  retries    = 40
  retry_wait = 15
}
