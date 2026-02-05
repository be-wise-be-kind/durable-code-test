# Purpose: S3 storage for Grafana observability stack data (metrics, logs, traces, profiles)
# Scope: Persistent object storage for all 4 observability pillars with lifecycle management
# Overview: Creates an S3 bucket with prefix-based separation for Mimir (metrics), Loki (logs),
#     Tempo (traces), and Pyroscope (profiles) data. Includes server-side encryption with AES256,
#     public access blocking, environment-specific lifecycle rules for data retention, and disabled
#     versioning (time-series data does not require version history). All resources are conditional
#     on the enable_observability feature flag, ensuring zero cost when disabled.
# Dependencies: networking.tf (data.aws_caller_identity.current), variables.tf (enable_observability, log_retention_days)
# Exports: Bucket name and ARN consumed by observability-iam.tf and runtime workspace
# Configuration: Lifecycle retention varies by environment via log_retention_days variable
# Environment: dev (7d retention), staging (14d), prod (30d)
# Related: observability-iam.tf for access policies, observability-security.tf for network access
# Implementation: Uses AES256 (SSE-S3) encryption for simplicity, prefix-based lifecycle rules per pillar

# S3 Bucket for Observability Data
resource "aws_s3_bucket" "observability" {
  count = var.enable_observability ? 1 : 0

  bucket = "${var.project_name}-${local.environment}-observability-${data.aws_caller_identity.current.account_id}"

  tags = merge(
    local.common_tags,
    var.additional_tags,
    {
      Name      = "${var.project_name}-${local.environment}-observability"
      Type      = "storage"
      Component = "observability"
      Purpose   = "S3 storage for Grafana observability stack data"
    }
  )
}

# Block All Public Access
resource "aws_s3_bucket_public_access_block" "observability" {
  count = var.enable_observability ? 1 : 0

  bucket = aws_s3_bucket.observability[0].id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Server-Side Encryption (AES256 / SSE-S3)
resource "aws_s3_bucket_server_side_encryption_configuration" "observability" {
  count = var.enable_observability ? 1 : 0

  bucket = aws_s3_bucket.observability[0].id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Disable Versioning (time-series data, not documents)
resource "aws_s3_bucket_versioning" "observability" {
  count = var.enable_observability ? 1 : 0

  bucket = aws_s3_bucket.observability[0].id

  versioning_configuration {
    status = "Disabled"
  }
}

# Lifecycle Rules - One Per Pillar Prefix
resource "aws_s3_bucket_lifecycle_configuration" "observability" {
  count = var.enable_observability ? 1 : 0

  bucket = aws_s3_bucket.observability[0].id

  rule {
    id     = "mimir-retention"
    status = "Enabled"

    filter {
      prefix = "mimir/"
    }

    expiration {
      days = lookup(var.log_retention_days, var.environment, 7)
    }
  }

  rule {
    id     = "loki-retention"
    status = "Enabled"

    filter {
      prefix = "loki/"
    }

    expiration {
      days = lookup(var.log_retention_days, var.environment, 7)
    }
  }

  rule {
    id     = "tempo-retention"
    status = "Enabled"

    filter {
      prefix = "tempo/"
    }

    expiration {
      days = lookup(var.log_retention_days, var.environment, 7)
    }
  }

  rule {
    id     = "pyroscope-retention"
    status = "Enabled"

    filter {
      prefix = "pyroscope/"
    }

    expiration {
      days = lookup(var.log_retention_days, var.environment, 7)
    }
  }
}
