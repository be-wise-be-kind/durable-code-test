# Purpose: Development environment configuration with aggressive cost optimization settings
# Scope: Variable overrides specific to the development environment for infrastructure deployment
# Overview: This file provides environment-specific variable values for the development
#     infrastructure, prioritizing cost savings over performance and availability. Key
#     cost optimizations include Fargate Spot instances (70% cost reduction), auto-shutdown
#     scheduling (66% compute cost savings), minimal resource sizing (256 CPU/512 Memory),
#     and scale-to-zero capabilities during off-hours. All optional security features like
#     WAF, GuardDuty, and enhanced monitoring are disabled to minimize costs. The configuration
#     targets a monthly budget of $10 or less while maintaining a functional development
#     environment for testing and iteration. Auto-shutdown schedules ensure resources only
#     run during business hours on weekdays, with complete shutdown on weekends for maximum
#     cost efficiency.
# Dependencies: Requires variables defined in terraform/variables.tf and backend configuration
# Exports: Environment-specific variable overrides for development infrastructure deployment
# Configuration: Applied via terraform plan/apply -var-file=../environments/dev.tfvars
# Environment: Development environment with cost-optimized settings and aggressive resource scheduling
# Related: Links to staging.tfvars and prod.tfvars for environment comparison
# Implementation: Uses Fargate Spot, auto-shutdown scheduling, and minimal resource allocation for cost optimization

environment = "dev"
aws_region  = "us-west-2"

# Domain Configuration
domain_name         = "dev.durableaicoding.net"
create_route53_zone = true                       # Create hosted zone for dev subdomain
apex_zone_id        = "Z02118692WI9DL3JWAT68"    # durableaicoding.net zone for delegation records

# Cost Optimization Settings
enable_auto_shutdown = true
use_fargate_spot    = true  # 70% cost savings for dev environment
enable_nat_gateway  = true  # Keep NAT Gateway enabled, use scheduled start/stop for cost savings

# Networking (cost optimized for dev)
az_count = 2  # Minimum 2 AZs required for ALB (will increase NAT Gateway costs)

# Minimal resource sizing for dev
fargate_cpu    = 256  # Minimum CPU
fargate_memory = 512  # Minimum memory
desired_count  = 1    # Single instance for dev
min_capacity   = 0    # Allow scale to zero
max_capacity   = 2    # Limited scaling for cost control

# Monitoring (minimal for cost savings)
enable_container_insights = false
budget_amount            = 10.0  # Lower budget for dev

# Security (optional features disabled for cost savings)
enable_waf          = false
enable_guardduty    = false
enable_security_hub = false

# CI/CD Configuration
github_branches = ["develop", "feature/*"]

# HTTPS Configuration
enable_https = true
# Certificate ARN will be dynamically retrieved from ACM

# Additional tags for dev environment
additional_tags = {
  "Environment"     = "Development"
  "CostOptimization" = "Aggressive"
  "AutoShutdown"    = "Enabled"
  "FargateSpot"     = "Enabled"
}
