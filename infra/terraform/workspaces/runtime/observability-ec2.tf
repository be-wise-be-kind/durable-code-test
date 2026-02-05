# Purpose: EC2 instance for self-hosted Grafana observability stack in private subnet
# Scope: AMI lookup, EC2 instance with Docker/Compose bootstrap, conditional on enable_observability flag
# Overview: Defines the observability EC2 instance running in a private subnet with Amazon Linux 2023.
#     The instance hosts the Grafana observability stack (Grafana, Mimir, Loki, Tempo, Pyroscope, Alloy)
#     via Docker Compose. User data bootstraps Docker and Docker Compose installation. The instance uses
#     an IAM instance profile from the base workspace for S3 access and SSM connectivity, and a dedicated
#     security group controlling inbound traffic from the ALB. All resources are conditional on the
#     enable_observability feature flag, ensuring zero cost when disabled. IMDSv2 is enforced for
#     metadata security. The instance type is configurable per environment via a map variable.
# Dependencies: Base workspace outputs (instance profile, security group), VPC private subnets, AMI data source
# Exports: EC2 instance ID and private IP for ALB target group attachment and operational access
# Configuration: Instance type via observability_instance_type map variable, feature flag via enable_observability
# Environment: Same instance type (t3.medium) across dev/staging/prod for consistent observability performance
# Related: observability-alb.tf for ALB routing, base workspace observability-iam.tf and observability-security.tf
# Implementation: Single EC2 instance with Docker Compose, user_data placeholder extended by PR 4

# Amazon Linux 2023 AMI lookup
data "aws_ami" "al2023" {
  count       = var.enable_observability ? 1 : 0
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  filter {
    name   = "architecture"
    values = ["x86_64"]
  }
}

# Observability EC2 Instance
resource "aws_instance" "observability" {
  count = var.enable_observability ? 1 : 0

  ami                    = data.aws_ami.al2023[0].id
  instance_type          = lookup(var.observability_instance_type, var.environment, "t3.medium")
  subnet_id              = tolist(data.aws_subnets.private.ids)[0]
  iam_instance_profile   = local.observability_instance_profile
  vpc_security_group_ids = [local.observability_security_group_id]

  root_block_device {
    volume_size           = 20
    volume_type           = "gp3"
    encrypted             = true
    delete_on_termination = true
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
    instance_metadata_tags      = "enabled"
  }

  user_data = base64encode(<<-USERDATA
    #!/bin/bash
    set -euo pipefail

    # Install Docker
    dnf update -y
    dnf install -y docker
    systemctl enable docker
    systemctl start docker

    # Install Docker Compose plugin
    mkdir -p /usr/local/lib/docker/cli-plugins
    COMPOSE_VERSION="v2.24.5"
    curl -SL "https://github.com/docker/compose/releases/download/$${COMPOSE_VERSION}/docker-compose-linux-x86_64" \
      -o /usr/local/lib/docker/cli-plugins/docker-compose
    chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

    # Verify installations
    docker --version
    docker compose version

    # Create observability directory structure
    mkdir -p /opt/observability
    USERDATA
  )

  tags = merge(
    local.common_tags,
    var.additional_tags,
    {
      Name      = "${var.project_name}-${local.environment}-observability"
      Component = "observability"
      Purpose   = "Grafana observability stack host"
    }
  )

  lifecycle {
    ignore_changes = [ami]
  }
}
