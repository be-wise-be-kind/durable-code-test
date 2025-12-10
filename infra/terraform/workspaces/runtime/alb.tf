# Runtime Infrastructure - Application Load Balancer
# Moved to runtime workspace for cost optimization - can be destroyed nightly

# Application Load Balancer (expensive - moved to runtime for cost optimization)
resource "aws_lb" "main" {
  name               = "${var.project_name}-${local.environment}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [data.aws_security_group.alb.id]
  subnets            = data.aws_subnets.public.ids

  enable_deletion_protection       = local.environment == "prod" ? true : false
  enable_http2                     = true
  enable_cross_zone_load_balancing = false # Cost optimization - avoid cross-AZ charges

  # Access logs enabled for all environments for security monitoring
  # Critical for incident response, compliance, and debugging
  access_logs {
    bucket  = aws_s3_bucket.alb_logs.bucket
    enabled = true
    prefix  = "alb"
  }

  tags = merge(
    local.common_tags,
    var.additional_tags,
    {
      Name = "${var.project_name}-${local.environment}-alb"
      Type = "ApplicationLoadBalancer"
    }
  )
}

# S3 bucket for ALB access logs (all environments for security)
resource "aws_s3_bucket" "alb_logs" {
  bucket        = "${var.project_name}-${local.environment}-alb-logs-${data.aws_caller_identity.current.account_id}"
  force_destroy = true

  tags = merge(
    local.common_tags,
    var.additional_tags,
    {
      Name    = "${var.project_name}-${local.environment}-alb-logs"
      Purpose = "ALB-AccessLogs"
    }
  )
}

# S3 bucket lifecycle configuration for log retention
resource "aws_s3_bucket_lifecycle_configuration" "alb_logs" {
  bucket = aws_s3_bucket.alb_logs.id

  rule {
    id     = "expire-old-logs"
    status = "Enabled"

    filter {} # Required even if empty

    expiration {
      days = lookup(var.log_retention_days, var.environment, 7)
    }
  }
}

# S3 bucket public access block
resource "aws_s3_bucket_public_access_block" "alb_logs" {
  bucket = aws_s3_bucket.alb_logs.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Data source for ELB service account
data "aws_elb_service_account" "main" {}

# S3 bucket policy for ALB access logs
resource "aws_s3_bucket_policy" "alb_logs" {
  bucket = aws_s3_bucket.alb_logs.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "ALBAccessLogsWrite"
        Effect = "Allow"
        Principal = {
          AWS = data.aws_elb_service_account.main.arn
        }
        Action   = "s3:PutObject"
        Resource = "${aws_s3_bucket.alb_logs.arn}/*"
      },
      {
        Sid    = "AWSLogDeliveryWrite"
        Effect = "Allow"
        Principal = {
          Service = "delivery.logs.amazonaws.com"
        }
        Action   = "s3:PutObject"
        Resource = "${aws_s3_bucket.alb_logs.arn}/*"
        Condition = {
          StringEquals = {
            "s3:x-amz-acl" = "bucket-owner-full-control"
          }
        }
      },
      {
        Sid    = "AWSLogDeliveryAclCheck"
        Effect = "Allow"
        Principal = {
          Service = "delivery.logs.amazonaws.com"
        }
        Action   = "s3:GetBucketAcl"
        Resource = aws_s3_bucket.alb_logs.arn
      }
    ]
  })

  depends_on = [aws_s3_bucket_public_access_block.alb_logs]
}