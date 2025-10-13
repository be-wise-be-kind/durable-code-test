# Purpose: Output definitions for base infrastructure resources consumed by runtime workspace
# Scope: Exports all base resource identifiers, endpoints, and configuration values
# Overview: Provides comprehensive outputs from the base infrastructure workspace that are consumed
#     by the runtime workspace via Terraform data sources. These outputs include all necessary
#     identifiers and configuration values for VPC networking, subnets, security groups, ECR
#     repositories, ALB resources, Route53 zones, and ACM certificates. The outputs enable the
#     runtime workspace to reference base resources without direct state file dependencies, maintaining
#     clean separation between persistent and ephemeral infrastructure. Each output includes a
#     description for documentation and proper handling of conditional resources.
# Dependencies: All base workspace resources (networking.tf, ecr.tf, dns.tf, alb.tf)
# Exports: Resource IDs, ARNs, URLs, and configuration values for runtime consumption
# Configuration: Conditional outputs based on resource creation flags
# Environment: Workspace and environment-aware values included in outputs
# Related: Runtime workspace data.tf will consume these outputs via remote state or data sources
# Implementation: Comprehensive output strategy for cross-workspace resource sharing

# VPC Outputs
output "vpc_id" {
  description = "VPC ID for runtime resources"
  value       = aws_vpc.main.id
}

output "vpc_cidr" {
  description = "VPC CIDR block"
  value       = aws_vpc.main.cidr_block
}

# Subnet Outputs
output "public_subnet_ids" {
  description = "Public subnet IDs for ALB"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "Private subnet IDs for ECS tasks"
  value       = aws_subnet.private[*].id
}

output "public_subnet_cidrs" {
  description = "Public subnet CIDR blocks"
  value       = aws_subnet.public[*].cidr_block
}

output "private_subnet_cidrs" {
  description = "Private subnet CIDR blocks"
  value       = aws_subnet.private[*].cidr_block
}

# Security Group Outputs
output "alb_security_group_id" {
  description = "ALB security group ID"
  value       = aws_security_group.alb.id
}

output "ecs_tasks_security_group_id" {
  description = "ECS tasks security group ID"
  value       = aws_security_group.ecs_tasks.id
}

# VPC endpoints security group moved to runtime workspace

# ECR Repository Outputs
output "backend_ecr_repository_url" {
  description = "Backend ECR repository URL"
  value       = aws_ecr_repository.backend.repository_url
}

output "frontend_ecr_repository_url" {
  description = "Frontend ECR repository URL"
  value       = aws_ecr_repository.frontend.repository_url
}

output "backend_ecr_repository_arn" {
  description = "Backend ECR repository ARN"
  value       = aws_ecr_repository.backend.arn
}

output "frontend_ecr_repository_arn" {
  description = "Frontend ECR repository ARN"
  value       = aws_ecr_repository.frontend.arn
}

output "backend_ecr_repository_name" {
  description = "Backend ECR repository name"
  value       = aws_ecr_repository.backend.name
}

output "frontend_ecr_repository_name" {
  description = "Frontend ECR repository name"
  value       = aws_ecr_repository.frontend.name
}

# ALB outputs moved to runtime workspace

# Route53 Outputs
output "route53_zone_id" {
  description = "Route53 zone ID (if created)"
  value       = var.domain_name != "" && var.create_route53_zone ? aws_route53_zone.main[0].zone_id : ""
}

output "route53_zone_name" {
  description = "Route53 zone name (if created)"
  value       = var.domain_name != "" && var.create_route53_zone ? aws_route53_zone.main[0].name : ""
}

output "route53_name_servers" {
  description = "Route53 zone name servers (if created)"
  value       = var.domain_name != "" && var.create_route53_zone ? aws_route53_zone.main[0].name_servers : []
}

# ACM Certificate Outputs
output "acm_certificate_arn" {
  description = "ACM certificate ARN (if created)"
  value       = var.domain_name != "" && var.create_route53_zone ? aws_acm_certificate.main[0].arn : ""
}

output "acm_certificate_domain_name" {
  description = "ACM certificate domain name (if created)"
  value       = var.domain_name != "" && var.create_route53_zone ? aws_acm_certificate.main[0].domain_name : ""
}

output "acm_certificate_status" {
  description = "ACM certificate status (if created)"
  value       = var.domain_name != "" && var.create_route53_zone ? aws_acm_certificate.main[0].status : ""
}

# NAT Gateway outputs moved to runtime workspace

# VPC Endpoint outputs moved to runtime workspace

# VPC Flow Logs Outputs
output "vpc_flow_log_id" {
  description = "VPC Flow Log ID"
  value       = aws_flow_log.main.id
}

output "vpc_flow_log_group_name" {
  description = "CloudWatch Log Group name for VPC Flow Logs"
  value       = aws_cloudwatch_log_group.vpc_flow_logs.name
}

output "vpc_flow_log_group_arn" {
  description = "CloudWatch Log Group ARN for VPC Flow Logs"
  value       = aws_cloudwatch_log_group.vpc_flow_logs.arn
}

# Resource Tags (for data source filtering)
output "base_resource_tags" {
  description = "Tags applied to base resources for filtering"
  value = {
    Environment = local.environment
    Workspace   = local.workspace_name
    Scope       = "base"
    Project     = var.project_name
  }
}

# Environment and Configuration Info
output "environment" {
  description = "Environment name"
  value       = local.environment
}

output "aws_region" {
  description = "AWS region"
  value       = var.aws_region
}

output "workspace_name" {
  description = "Current Terraform workspace name"
  value       = local.workspace_name
}