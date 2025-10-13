# Purpose: Output definitions for bootstrap workspace
# Scope: Expose GitHub OIDC and IAM role information for other workspaces

output "github_oidc_provider_arn" {
  description = "ARN of the GitHub OIDC provider"
  value       = aws_iam_openid_connect_provider.github.arn
}

output "github_actions_role_arn" {
  description = "ARN of the GitHub Actions IAM role"
  value       = aws_iam_role.github_actions.arn
}

output "github_actions_role_name" {
  description = "Name of the GitHub Actions IAM role"
  value       = aws_iam_role.github_actions.name
}

output "workspace_name" {
  description = "Name of the Terraform workspace"
  value       = local.workspace_name
}

output "environment" {
  description = "Environment name extracted from workspace"
  value       = local.environment
}
