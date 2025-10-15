# Purpose: Data source definitions for cross-workspace resource references from base infrastructure
# Scope: Lookup of VPC, subnets, security groups, ECR repositories, ALB, and Route53 resources from base workspace
# Overview: This file contains data source definitions that enable the runtime workspace to reference
#     resources created and managed by the base infrastructure workspace. Instead of direct resource
#     references, the runtime workspace uses tag-based and name-based lookups to discover base
#     resources dynamically. This approach provides loose coupling between workspaces while
#     maintaining operational integrity. Data sources use consistent tagging strategies and naming
#     conventions established in the base workspace to ensure reliable resource discovery across
#     environments. The file includes comprehensive lookups for networking, security, container
#     registry, load balancer, and DNS resources required by runtime services.
# Dependencies: Base workspace must be deployed first with properly tagged resources
# Exports: Data source references for use throughout runtime workspace configuration
# Configuration: Uses environment-aware tags and naming patterns for resource discovery
# Environment: Filters resources based on local.environment from workspace name
# Related: Base workspace outputs.tf for available resources, ecs.tf and alb-listeners.tf for usage
# Implementation: Tag-based filtering with fallback to name-based lookups where appropriate

# Data source for current AWS account
data "aws_caller_identity" "current" {}

# Data source for current AWS region
data "aws_region" "current" {}

# Remote state data source - Reference base workspace outputs
data "terraform_remote_state" "base" {
  backend = "s3"

  config = {
    bucket               = "durable-code-terraform-state"
    key                  = "env:/base-${local.environment}/base/${local.environment}/terraform.tfstate"
    region               = "us-west-2"
    workspace_key_prefix = ""
  }
}

# Internet Gateway Lookup - Required for NAT Gateway dependencies
data "aws_internet_gateway" "main" {
  filter {
    name   = "attachment.vpc-id"
    values = [data.aws_vpc.main.id]
  }
}

# VPC Lookup - Reference from base workspace remote state
data "aws_vpc" "main" {
  id = data.terraform_remote_state.base.outputs.vpc_id
}

# Public Subnets Lookup - For ALB placement
data "aws_subnets" "public" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.main.id]
  }

  filter {
    name   = "tag:Type"
    values = ["public"]
  }

  filter {
    name   = "tag:Scope"
    values = ["base"]
  }
}

# Private Subnets Lookup - For ECS task placement
data "aws_subnets" "private" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.main.id]
  }

  filter {
    name   = "tag:Type"
    values = ["private"]
  }

  filter {
    name   = "tag:Scope"
    values = ["base"]
  }
}

# ALB Security Group - Reference from base workspace remote state
data "aws_security_group" "alb" {
  id = data.terraform_remote_state.base.outputs.alb_security_group_id
}

# ECS Tasks Security Group - Reference from base workspace remote state
data "aws_security_group" "ecs_tasks" {
  id = data.terraform_remote_state.base.outputs.ecs_tasks_security_group_id
}

# Backend ECR Repository Lookup
data "aws_ecr_repository" "backend" {
  name = "${var.product_domain}-${local.environment}-backend"
}

# Frontend ECR Repository Lookup
data "aws_ecr_repository" "frontend" {
  name = "${var.product_domain}-${local.environment}-frontend"
}

# ALB moved to runtime workspace - created directly instead of looked up

# Route53 Hosted Zone from base workspace
# Get the zone_id and name from base workspace remote state
# The zone is environment-specific (e.g., dev.durableaicoding.net)
locals {
  route53_zone_id   = var.domain_name != "" ? data.terraform_remote_state.base.outputs.route53_zone_id : ""
  route53_zone_name = var.domain_name != "" ? data.terraform_remote_state.base.outputs.route53_zone_name : ""
}

# ACM Certificate Lookup (conditional - only if domain is configured)
data "aws_acm_certificate" "main" {
  count  = var.domain_name != "" ? 1 : 0
  domain = var.domain_name

  statuses = ["ISSUED"]
  types    = ["AMAZON_ISSUED"]

  most_recent = true
}

