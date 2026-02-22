# Purpose: Backend configuration for grafana infrastructure workspace in dev environment
# Scope: S3 backend configuration for Terraform state management
# Overview: Defines the S3 backend settings for the grafana workspace which contains
#     Grafana API resources (datasources, folders, dashboards). This configuration
#     ensures Grafana state is stored separately from runtime infrastructure, enabling
#     independent dashboard deployments without refreshing ECS, ALB, or WAF resources.
# Dependencies: S3 bucket and DynamoDB table must exist for state storage
# Environment: Development environment grafana workspace

bucket               = "durable-code-terraform-state"
key                  = "grafana/dev/terraform.tfstate"
region               = "us-west-2"
encrypt              = true
dynamodb_table       = "durable-code-terraform-locks"
workspace_key_prefix = ""  # Disable env:/ prefixing for predictable state paths
