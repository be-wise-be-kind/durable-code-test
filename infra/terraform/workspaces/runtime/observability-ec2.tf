# Purpose: EC2 instance for self-hosted Grafana observability stack in private subnet
# Scope: AMI lookup, EC2 instance with Docker/Compose bootstrap and stack deployment, conditional on enable_observability flag
# Overview: Defines the observability EC2 instance running in a private subnet with Amazon Linux 2023.
#     The instance hosts the Grafana observability stack (Grafana, Mimir, Loki, Tempo, Pyroscope, Alloy)
#     via Docker Compose. User data bootstraps Docker and Docker Compose, writes all component configs,
#     and starts the full stack. Config files are read from infra/observability/ and injected via
#     templatefile at plan time, with S3 bucket name and region interpolated into storage backend
#     configs. The instance uses an IAM instance profile from the base workspace for S3 access and
#     SSM connectivity, and a dedicated security group controlling inbound traffic from the ALB.
#     All resources are conditional on the enable_observability feature flag, ensuring zero cost when
#     disabled. IMDSv2 is enforced with hop limit 2 to allow Docker containers to access instance
#     metadata for S3 credential retrieval. The instance type is configurable per environment.
# Dependencies: Base workspace outputs (instance profile, security group), VPC private subnets, config files in infra/observability/
# Exports: EC2 instance ID and private IP for ALB target group attachment and operational access
# Configuration: Instance type via observability_instance_type map variable, feature flag via enable_observability
# Environment: Same instance type (t3.medium) across dev/staging/prod for consistent observability performance
# Related: observability-alb.tf for ALB routing, infra/observability/ for component configs
# Implementation: Single EC2 instance with templatefile user_data deploying full Grafana stack via Docker Compose

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

# Render storage backend configs with S3 bucket and region
locals {
  observability_config_path = "${path.module}/../../../observability"

  mimir_config = var.enable_observability ? templatefile(
    "${local.observability_config_path}/mimir/mimir.yml.tftpl",
    {
      s3_bucket  = local.observability_bucket_name
      aws_region = var.aws_region
    }
  ) : ""

  loki_config = var.enable_observability ? templatefile(
    "${local.observability_config_path}/loki/loki.yml.tftpl",
    {
      s3_bucket  = local.observability_bucket_name
      aws_region = var.aws_region
    }
  ) : ""

  tempo_config = var.enable_observability ? templatefile(
    "${local.observability_config_path}/tempo/tempo.yml.tftpl",
    {
      s3_bucket  = local.observability_bucket_name
      aws_region = var.aws_region
    }
  ) : ""

  pyroscope_config = var.enable_observability ? templatefile(
    "${local.observability_config_path}/pyroscope/pyroscope.yml.tftpl",
    {
      s3_bucket  = local.observability_bucket_name
      aws_region = var.aws_region
    }
  ) : ""
}

# Observability EC2 Instance
resource "aws_instance" "observability" {
  count = var.enable_observability ? 1 : 0

  ami                         = data.aws_ami.al2023[0].id
  instance_type               = lookup(var.observability_instance_type, var.environment, "t3.medium")
  subnet_id                   = tolist(data.aws_subnets.public.ids)[0]
  associate_public_ip_address    = true
  iam_instance_profile           = local.observability_instance_profile
  vpc_security_group_ids         = [local.observability_security_group_id]
  user_data_replace_on_change    = true

  root_block_device {
    volume_size           = 30
    volume_type           = "gp3"
    encrypted             = true
    delete_on_termination = true
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 2
    instance_metadata_tags      = "enabled"
  }

  user_data_base64 = base64gzip(templatefile(
    "${local.observability_config_path}/user-data.sh.tftpl",
    {
      docker_compose                 = file("${local.observability_config_path}/docker-compose.yml")
      grafana_admin_password         = var.grafana_admin_password
      grafana_ini                    = file("${local.observability_config_path}/grafana/grafana.ini")
      grafana_datasources            = file("${local.observability_config_path}/grafana/datasources.yml")
      grafana_dashboard_provisioning = file("${local.observability_config_path}/grafana/dashboard-provisioning.yml")
      mimir_config                   = local.mimir_config
      loki_config                    = local.loki_config
      tempo_config                   = local.tempo_config
      pyroscope_config               = local.pyroscope_config
      alloy_config                   = file("${local.observability_config_path}/alloy/config.alloy")
    }
  ))

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
