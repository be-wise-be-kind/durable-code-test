# Purpose: Backend configuration for base infrastructure workspace in staging environment
# Scope: S3 backend configuration for Terraform state management
# Overview: Defines the S3 backend settings for the base workspace which contains
#     persistent infrastructure resources like VPC, NAT Gateways, ECR repositories.
#     This configuration ensures base infrastructure state is stored separately
#     from runtime resources, enabling independent lifecycle management.
# Dependencies: S3 bucket must exist for state storage and locking
# Environment: Staging environment base workspace

bucket               = "durable-code-terraform-state"
key                  = "base/staging/terraform.tfstate"
region               = "us-west-2"
encrypt              = true
use_lockfile         = true
workspace_key_prefix = ""  # Disable env:/ prefixing for predictable state paths