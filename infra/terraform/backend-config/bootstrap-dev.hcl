# Purpose: Backend configuration for bootstrap workspace in dev environment
# Scope: S3 backend configuration for Terraform state management
# Overview: Defines the S3 backend settings for the bootstrap workspace which contains
#     permanent GitHub Actions authentication infrastructure (OIDC provider and IAM role).
#     This workspace should never be destroyed by automated workflows as it provides
#     the authentication mechanism for GitHub Actions to manage other infrastructure.
# Dependencies: S3 bucket and DynamoDB table must exist for state storage
# Environment: Development environment bootstrap workspace

bucket         = "durable-code-terraform-state"
key            = "bootstrap/dev/terraform.tfstate"
region         = "us-west-2"
encrypt        = true
dynamodb_table = "durable-code-terraform-locks"
