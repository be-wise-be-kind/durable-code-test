# Purpose: Variable definitions for runtime infrastructure workspace configuration
# Scope: Input variables for ECS services, auto-scaling, container configuration, and runtime settings
# Overview: This file defines all input variables required for the runtime infrastructure workspace,
#     which manages ephemeral resources like ECS services, task definitions, and ALB configurations.
#     Variables are organized by category and include sensible defaults optimized for cost and
#     performance. The configuration supports environment-specific overrides through tfvars files,
#     enabling different resource allocations for development, staging, and production environments.
#     Validation rules ensure configuration integrity and prevent invalid resource specifications.
# Dependencies: Used by all runtime workspace resources for configuration
# Exports: Variable values accessible throughout runtime workspace configuration
# Configuration: Override defaults using terraform.tfvars or -var-file parameter
# Environment: Environment-aware defaults for resource sizing and feature flags
# Related: terraform.tfvars.example for configuration template, ecs.tf and alb-listeners.tf for usage
# Implementation: Variables use appropriate types with validation and descriptions

# Environment and Project Configuration
variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-west-2"
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "durableai"
}

variable "product_domain" {
  description = "Product domain for resource naming"
  type        = string
  default     = "durableai"
}

# ECS Configuration
variable "ecs_task_cpu" {
  description = "CPU units for ECS task (256 = 0.25 vCPU)"
  type        = map(string)
  default = {
    dev     = "256"
    staging = "512"
    prod    = "1024"
  }
}

variable "ecs_task_memory" {
  description = "Memory for ECS task in MB"
  type        = map(string)
  default = {
    dev     = "512"
    staging = "1024"
    prod    = "2048"
  }
}

variable "ecs_service_desired_count" {
  description = "Desired number of ECS tasks"
  type        = map(number)
  default = {
    dev     = 1
    staging = 2
    prod    = 3
  }
}

variable "ecs_service_min_count" {
  description = "Minimum number of ECS tasks for auto-scaling"
  type        = map(number)
  default = {
    dev     = 1
    staging = 2
    prod    = 2
  }
}

variable "ecs_service_max_count" {
  description = "Maximum number of ECS tasks for auto-scaling"
  type        = map(number)
  default = {
    dev     = 2
    staging = 4
    prod    = 10
  }
}

# Container Configuration
variable "backend_image_tag" {
  description = "Docker image tag for backend service"
  type        = string
  default     = "latest"
}

variable "frontend_image_tag" {
  description = "Docker image tag for frontend service"
  type        = string
  default     = "latest"
}

variable "backend_port" {
  description = "Port for backend service"
  type        = number
  default     = 8000
}

variable "frontend_port" {
  description = "Port for frontend service"
  type        = number
  default     = 3000 # TODO: Should be 80 for production nginx, but requires target group recreation
}

# Health Check Configuration
variable "health_check_path" {
  description = "Health check paths for services"
  type        = map(string)
  default = {
    backend  = "/health"
    frontend = "/"
  }
}

variable "health_check_interval" {
  description = "Health check interval in seconds"
  type        = number
  default     = 30
}

variable "health_check_timeout" {
  description = "Health check timeout in seconds"
  type        = number
  default     = 5
}

variable "health_check_healthy_threshold" {
  description = "Number of consecutive health check successes required"
  type        = number
  default     = 2
}

variable "health_check_unhealthy_threshold" {
  description = "Number of consecutive health check failures required"
  type        = number
  default     = 3
}

# DNS Configuration
variable "domain_name" {
  description = "Domain name for the application (e.g., durableaicoding.net)"
  type        = string
  default     = ""
}

# Auto-scaling Configuration
variable "enable_autoscaling" {
  description = "Enable ECS service auto-scaling"
  type        = bool
  default     = true
}

variable "autoscaling_target_cpu" {
  description = "Target CPU utilization for auto-scaling"
  type        = number
  default     = 70
}

variable "autoscaling_target_memory" {
  description = "Target memory utilization for auto-scaling"
  type        = number
  default     = 80
}

# Feature Flags
variable "enable_container_insights" {
  description = "Enable Container Insights for ECS cluster"
  type        = bool
  default     = false
}

variable "enable_service_discovery" {
  description = "Enable AWS Service Discovery for internal service communication"
  type        = bool
  default     = false
}

variable "enable_ecs_exec" {
  description = "Enable ECS Exec for debugging"
  type        = bool
  default     = true
}

# Logging Configuration
variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = map(number)
  default = {
    dev     = 7
    staging = 14
    prod    = 30
  }
}

# Networking Configuration
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "az_count" {
  description = "Number of Availability Zones"
  type        = number
  default     = 2
}

variable "enable_nat_gateway" {
  description = "Enable NAT Gateway for private subnet internet access"
  type        = bool
  default     = true
}

# Additional Tags
variable "additional_tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {}
}

# Observability Feature Flags
variable "enable_observability" {
  description = "Enable Grafana observability stack (EC2 instance, ALB routes)"
  type        = bool
  default     = false
}

variable "observability_instance_type" {
  description = "EC2 instance type for observability stack"
  type        = map(string)
  default = {
    dev     = "t3.medium"
    staging = "t3.medium"
    prod    = "t3.medium"
  }
}