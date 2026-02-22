# Purpose: AWS provider configuration for runtime infrastructure workspace
# Scope: Provider configuration with region, authentication, and default tags for runtime resources
# Overview: This file configures the AWS provider for the runtime workspace, establishing the
#     authentication context and region for all AWS resources managed in this workspace. It sets
#     up default tags that are automatically applied to all resources created by this configuration,
#     ensuring consistent metadata for cost tracking, environment identification, and resource
#     management. The provider configuration uses standard AWS credential chain for authentication
#     and applies workspace-aware tags to differentiate runtime resources from base infrastructure.
# Dependencies: AWS credentials, IAM permissions for runtime resource management
# Exports: Configured AWS provider for use by all resources in runtime workspace
# Configuration: Region and default tags are parameterized via variables
# Environment: Uses local.environment for environment-aware tagging
# Related: main.tf for locals definition, variables.tf for configuration parameters
# Implementation: Provider aliasing not used; single-region deployment model

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = merge(
      local.common_tags,
      var.additional_tags,
      {
        Project     = var.project_name
        Environment = local.environment
        Workspace   = local.workspace_name
        ManagedBy   = "Terraform"
        Scope       = "runtime"
      }
    )
  }
}