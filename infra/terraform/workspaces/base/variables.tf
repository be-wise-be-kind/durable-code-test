# Purpose: Variable definitions for base infrastructure workspace configuration
# Scope: Input variables for persistent base resources including networking, DNS, and registries
# Overview: Defines all input variables required for the base infrastructure workspace which manages
#     persistent resources that form the foundation of the application infrastructure. These variables
#     control the configuration of VPC networking, availability zones, NAT Gateway enablement, ECR
#     repositories, Route53 zones, and ACM certificates. Each variable includes validation rules to
#     ensure proper values and sensible defaults optimized for different environments. The variables
#     support cost optimization through optional resource creation and environment-specific sizing.
# Dependencies: Used by all resource files in the base workspace
# Exports: Variables available for use throughout the base workspace configuration
# Configuration: Overridden by environment-specific tfvars files (dev.tfvars, staging.tfvars, prod.tfvars)
# Environment: Supports dev, staging, and production with environment-specific defaults
# Related: terraform.tfvars.example for sample values, outputs.tf for exposed values
# Implementation: Validation blocks ensure data integrity, defaults optimize for cost

# Core Configuration
variable "product_domain" {
  description = "Product domain identifier for resource naming and tagging"
  type        = string
  default     = "durableai"

  validation {
    condition     = can(regex("^[a-z][a-z0-9]*$", var.product_domain))
    error_message = "Product domain must start with a letter and contain only lowercase letters and numbers."
  }
}

variable "project_name" {
  description = "Name of the project, used as a prefix for all resources"
  type        = string
  default     = "durable-code"

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]*$", var.project_name))
    error_message = "Project name must start with a letter and contain only lowercase letters, numbers, and hyphens."
  }
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "aws_region" {
  description = "AWS region for resource deployment"
  type        = string
  default     = "us-west-2"
}

# Networking Variables
variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "az_count" {
  description = "Number of availability zones to use"
  type        = number
  default     = 2

  validation {
    condition     = var.az_count >= 1 && var.az_count <= 6
    error_message = "AZ count must be between 1 and 6."
  }
}

variable "enable_nat_gateway" {
  description = "Whether to create NAT Gateways for private subnets"
  type        = bool
  default     = true
}

# Domain and DNS Configuration
variable "domain_name" {
  description = "Primary domain name for the application"
  type        = string
  default     = ""
}

variable "create_route53_zone" {
  description = "Whether to create a Route53 hosted zone"
  type        = bool
  default     = false
}

variable "apex_zone_id" {
  description = "Route53 hosted zone ID for the apex domain (e.g., durableaicoding.net) where delegation records should be created"
  type        = string
  default     = ""
}

# Security Variables (for base security groups)
variable "enable_waf" {
  description = "Enable AWS WAF for additional security (increases cost)"
  type        = bool
  default     = false
}

# Logging Configuration
variable "log_retention_days" {
  description = "CloudWatch log retention in days by environment"
  type        = map(number)
  default = {
    dev     = 7
    staging = 14
    prod    = 30
  }
}

# Tags
variable "additional_tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {}
}

# Observability Configuration
variable "enable_observability" {
  description = "Enable Grafana observability stack resources (S3, IAM, security groups)"
  type        = bool
  default     = false
}