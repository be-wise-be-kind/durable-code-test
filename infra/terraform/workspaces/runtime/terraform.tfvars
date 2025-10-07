# Terraform variables for runtime workspace - dev environment

environment     = "dev"
aws_region      = "us-west-2"
product_domain  = "durableai"
project_name    = "durable-code"

# DNS Configuration
# Set this to enable DNS records pointing to the ALB
domain_name = "durableaicoding.net"

# Container Images
backend_image_tag  = "latest"
frontend_image_tag = "latest"

# Service Ports
backend_port  = 8000
frontend_port = 3000

# Auto-scaling Configuration
enable_autoscaling = true
autoscaling_target_cpu = 70
autoscaling_target_memory = 80

# Feature Flags
enable_container_insights = false
enable_service_discovery  = false
enable_ecs_exec          = true
