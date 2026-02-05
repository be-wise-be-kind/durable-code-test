# Purpose: Security group for the Grafana observability EC2 instance
# Scope: Network access control for observability stack ports from ALB and ECS services
# Overview: Creates a security group in the main VPC that controls inbound access to the
#     observability EC2 instance. Allows ingress from the ALB security group on ports 3001
#     (Grafana UI) and 12347 (Alloy Faro receiver), and from the ECS tasks security group on
#     ports 4317 (OTLP gRPC), 4318 (OTLP HTTP), and 4040 (Pyroscope push). Permits all egress
#     for S3 access and package downloads. All resources are conditional on the enable_observability
#     feature flag, ensuring zero cost when disabled.
# Dependencies: networking.tf (VPC, ALB SG, ECS tasks SG), variables.tf (enable_observability)
# Exports: Security group ID consumed by runtime workspace EC2 instance
# Configuration: Security group named with project-environment prefix for consistency
# Environment: Same security group rules used across all environments
# Related: networking.tf for ALB/ECS security groups, observability-iam.tf for IAM access
# Implementation: Follows networking.tf security group structure with source SG references

# Security Group for Observability EC2 Instance
resource "aws_security_group" "observability" {
  count = var.enable_observability ? 1 : 0

  name        = "${var.project_name}-${local.environment}-observability-sg"
  description = "Security group for Grafana observability EC2 instance"
  vpc_id      = aws_vpc.main.id

  # Grafana UI - from ALB
  ingress {
    description     = "Grafana UI from ALB"
    from_port       = 3001
    to_port         = 3001
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  # Alloy Faro receiver - from ALB
  ingress {
    description     = "Alloy Faro receiver from ALB"
    from_port       = 12347
    to_port         = 12347
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  # OTLP gRPC - from ECS tasks
  ingress {
    description     = "OTLP gRPC from ECS tasks"
    from_port       = 4317
    to_port         = 4317
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_tasks.id]
  }

  # OTLP HTTP - from ECS tasks
  ingress {
    description     = "OTLP HTTP from ECS tasks"
    from_port       = 4318
    to_port         = 4318
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_tasks.id]
  }

  # Pyroscope push - from ECS tasks
  ingress {
    description     = "Pyroscope push from ECS tasks"
    from_port       = 4040
    to_port         = 4040
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_tasks.id]
  }

  # All outbound traffic (S3, package downloads)
  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(
    local.common_tags,
    var.additional_tags,
    {
      Name      = "${var.project_name}-${local.environment}-observability-sg"
      Type      = "security-group"
      Component = "observability"
      Purpose   = "Network access control for observability EC2 instance"
    }
  )
}
