# Purpose: Output values from runtime infrastructure workspace for operational visibility
# Scope: ECS cluster, services, task definitions, ALB endpoints, and CloudWatch log groups
# Overview: This file exports key runtime infrastructure values for operational tasks, monitoring,
#     debugging, and integration with deployment pipelines. Outputs include ECS cluster and service
#     identifiers for container deployments, task definition ARNs for rollback operations, ALB
#     endpoint URLs for application access, and CloudWatch log group names for troubleshooting.
#     The outputs provide essential information for CI/CD pipelines, monitoring dashboards, and
#     operational runbooks. Values are structured to support both human operators and automated
#     tools, with clear descriptions explaining each output's purpose and usage scenarios.
# Dependencies: Resources created within runtime workspace (ECS, ALB listeners, CloudWatch)
# Exports: Operational endpoints, resource identifiers, and monitoring references
# Configuration: Outputs automatically reflect current workspace state
# Environment: Values specific to workspace environment (dev/staging/prod)
# Related: Used by deployment scripts, monitoring tools, and operational procedures
# Implementation: Combines resource attributes with computed values for comprehensive visibility

# ECS Cluster Outputs
output "ecs_cluster_id" {
  description = "ECS cluster ID for deployments and monitoring"
  value       = aws_ecs_cluster.main.id
}

output "ecs_cluster_arn" {
  description = "ECS cluster ARN for IAM policies and cross-account access"
  value       = aws_ecs_cluster.main.arn
}

output "ecs_cluster_name" {
  description = "ECS cluster name for CLI commands and scripts"
  value       = aws_ecs_cluster.main.name
}

# ECS Service Outputs
output "backend_service_name" {
  description = "Backend ECS service name for deployments and scaling"
  value       = aws_ecs_service.backend.name
}

output "backend_service_arn" {
  description = "Backend ECS service ARN for monitoring and policies"
  value       = aws_ecs_service.backend.id
}

output "frontend_service_name" {
  description = "Frontend ECS service name for deployments and scaling"
  value       = aws_ecs_service.frontend.name
}

output "frontend_service_arn" {
  description = "Frontend ECS service ARN for monitoring and policies"
  value       = aws_ecs_service.frontend.id
}

# Task Definition Outputs
output "backend_task_definition_arn" {
  description = "Backend task definition ARN for rollback and updates"
  value       = aws_ecs_task_definition.backend.arn
}

output "backend_task_definition_family" {
  description = "Backend task definition family for revision tracking"
  value       = aws_ecs_task_definition.backend.family
}

output "backend_task_definition_revision" {
  description = "Backend task definition revision number"
  value       = aws_ecs_task_definition.backend.revision
}

output "frontend_task_definition_arn" {
  description = "Frontend task definition ARN for rollback and updates"
  value       = aws_ecs_task_definition.frontend.arn
}

output "frontend_task_definition_family" {
  description = "Frontend task definition family for revision tracking"
  value       = aws_ecs_task_definition.frontend.family
}

output "frontend_task_definition_revision" {
  description = "Frontend task definition revision number"
  value       = aws_ecs_task_definition.frontend.revision
}

# Target Group Outputs
output "backend_target_group_arn" {
  description = "Backend target group ARN for health monitoring"
  value       = aws_lb_target_group.backend.arn
}

output "backend_target_group_name" {
  description = "Backend target group name for AWS console navigation"
  value       = aws_lb_target_group.backend.name
}

output "frontend_target_group_arn" {
  description = "Frontend target group ARN for health monitoring"
  value       = aws_lb_target_group.frontend.arn
}

output "frontend_target_group_name" {
  description = "Frontend target group name for AWS console navigation"
  value       = aws_lb_target_group.frontend.name
}

# Application Endpoints
output "alb_dns_name" {
  description = "ALB DNS name for application access"
  value       = aws_lb.main.dns_name
}

output "application_url_http" {
  description = "HTTP URL for accessing the application"
  value       = "http://${aws_lb.main.dns_name}"
}

output "application_url_https" {
  description = "HTTPS URL for accessing the application (if certificate configured)"
  value       = var.domain_name != "" ? "https://${var.domain_name}" : "N/A - No domain configured"
}

output "backend_api_endpoint" {
  description = "Backend API endpoint URL"
  value       = "http://${aws_lb.main.dns_name}/api"
}

# CloudWatch Log Groups
output "backend_log_group" {
  description = "Backend CloudWatch log group name for troubleshooting"
  value       = aws_cloudwatch_log_group.backend.name
}

output "frontend_log_group" {
  description = "Frontend CloudWatch log group name for troubleshooting"
  value       = aws_cloudwatch_log_group.frontend.name
}

# IAM Role Outputs
output "ecs_task_execution_role_arn" {
  description = "ECS task execution role ARN for CI/CD pipelines"
  value       = aws_iam_role.ecs_task_execution.arn
}

output "ecs_task_role_arn" {
  description = "ECS task role ARN for application permissions"
  value       = aws_iam_role.ecs_task.arn
}

# Environment Information
output "environment" {
  description = "Current environment name"
  value       = local.environment
}

output "workspace_name" {
  description = "Current Terraform workspace name"
  value       = local.workspace_name
}

# Deployment Information
output "deployment_info" {
  description = "Summary of deployment endpoints and services"
  value = {
    environment      = local.environment
    cluster          = aws_ecs_cluster.main.name
    backend_service  = aws_ecs_service.backend.name
    frontend_service = aws_ecs_service.frontend.name
    application_url  = var.domain_name != "" ? "https://${var.domain_name}" : "http://${aws_lb.main.dns_name}"
    api_endpoint     = "http://${aws_lb.main.dns_name}/api"
  }
}

# DNS Outputs
output "application_url" {
  description = "Application URL"
  value       = var.domain_name != "" ? "https://${local.environment}.${var.domain_name}" : "http://${aws_lb.main.dns_name}"
}

output "dns_records_created" {
  description = "DNS records created"
  value = var.domain_name != "" ? {
    main = "${local.environment}.${var.domain_name}"
    www  = "www.${local.environment}.${var.domain_name}"
    api  = "api-${local.environment}.${var.domain_name}"
  } : {}
}

# Observability Outputs
output "observability_ec2_private_ip" {
  description = "Private IP of observability EC2 instance"
  value       = var.enable_observability ? aws_instance.observability[0].private_ip : ""
}

output "observability_grafana_url" {
  description = "Grafana URL via ALB"
  value       = var.enable_observability ? "http://${aws_lb.main.dns_name}/grafana/" : ""
}

output "observability_ec2_instance_id" {
  description = "Observability EC2 instance ID for SSM access"
  value       = var.enable_observability ? aws_instance.observability[0].id : ""
}