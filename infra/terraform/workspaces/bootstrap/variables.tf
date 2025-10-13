# Purpose: Variable definitions for bootstrap workspace
# Scope: Input variables for GitHub Actions authentication infrastructure
# Overview: Defines minimal variables required for the bootstrap workspace

variable "project_name" {
  description = "Name of the project, used as a prefix for all resources"
  type        = string
  default     = "durable-code"

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]*$", var.project_name))
    error_message = "Project name must start with a letter and contain only lowercase letters, numbers, and hyphens."
  }
}

variable "product_domain" {
  description = "Product domain identifier for resource naming"
  type        = string
  default     = "durableai"

  validation {
    condition     = can(regex("^[a-z][a-z0-9]*$", var.product_domain))
    error_message = "Product domain must start with a letter and contain only lowercase letters and numbers."
  }
}

variable "aws_region" {
  description = "AWS region for resource deployment"
  type        = string
  default     = "us-west-2"
}
