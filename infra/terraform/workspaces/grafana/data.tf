# Purpose: Data source definitions for cross-workspace resource references from runtime infrastructure
# Scope: Lookup of runtime workspace state to verify observability EC2 instance existence
# Overview: Contains the remote state data source that enables the grafana workspace to reference
#     the runtime workspace state. This verifies the observability EC2 instance has been deployed
#     before Grafana API resources are created. The remote state reference provides EC2 instance
#     metadata for operational visibility. The Grafana provider connects via SSM tunnel, not via
#     Terraform resource references.
# Dependencies: Runtime workspace must be deployed with enable_observability=true
# Exports: Runtime workspace state references for EC2 instance verification
# Configuration: Uses environment-aware state path for correct cross-workspace reference
# Environment: References environment-specific runtime state (dev/staging/prod)
# Related: Runtime workspace outputs.tf for available values, dashboards.tf for resource usage
# Implementation: S3 remote state reference with environment-parameterized state key

data "terraform_remote_state" "runtime" {
  backend = "s3"

  config = {
    bucket = "durable-code-terraform-state"
    key    = "runtime/${var.environment}/terraform.tfstate"
    region = var.aws_region
  }
}
