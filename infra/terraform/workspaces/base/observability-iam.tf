# Purpose: IAM role and instance profile for the Grafana observability EC2 instance
# Scope: Identity and access management for observability stack S3 access and SSM connectivity
# Overview: Creates an IAM role with EC2 assume-role trust policy, an instance profile for EC2
#     attachment, an inline S3 policy granting read/write access to the observability bucket, and
#     an SSM managed policy attachment for Session Manager access. The S3 policy follows least
#     privilege with bucket-level list permissions and object-level CRUD operations. All resources
#     are conditional on the enable_observability feature flag, ensuring zero cost when disabled.
# Dependencies: observability-storage.tf (S3 bucket ARN), variables.tf (enable_observability)
# Exports: Instance profile name/ARN and role ARN consumed by runtime workspace EC2 instance
# Configuration: IAM resources named with project-environment prefix for consistency
# Environment: Same role used across all environments with environment-specific bucket access
# Related: observability-storage.tf for S3 bucket, vpc-flow-logs.tf for IAM pattern reference
# Implementation: Follows vpc-flow-logs.tf IAM structure; uses inline policy for S3, managed policy for SSM

# IAM Role for Observability EC2 Instance
resource "aws_iam_role" "observability" {
  count = var.enable_observability ? 1 : 0

  name = "${var.project_name}-${local.environment}-observability"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = merge(
    local.common_tags,
    var.additional_tags,
    {
      Name      = "${var.project_name}-${local.environment}-observability-role"
      Component = "observability"
      Purpose   = "IAM role for observability EC2 instance"
    }
  )
}

# Instance Profile for EC2 Attachment
resource "aws_iam_instance_profile" "observability" {
  count = var.enable_observability ? 1 : 0

  name = "${var.project_name}-${local.environment}-observability"
  role = aws_iam_role.observability[0].name

  tags = merge(
    local.common_tags,
    var.additional_tags,
    {
      Name      = "${var.project_name}-${local.environment}-observability-instance-profile"
      Component = "observability"
      Purpose   = "Instance profile for observability EC2 instance"
    }
  )
}

# S3 Access Policy for Observability Bucket
resource "aws_iam_role_policy" "observability_s3" {
  count = var.enable_observability ? 1 : 0

  name = "${var.project_name}-${local.environment}-observability-s3"
  role = aws_iam_role.observability[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket",
          "s3:GetBucketLocation"
        ]
        Resource = aws_s3_bucket.observability[0].arn
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = "${aws_s3_bucket.observability[0].arn}/*"
      }
    ]
  })
}

# SSM Managed Policy for Session Manager Access
resource "aws_iam_role_policy_attachment" "observability_ssm" {
  count = var.enable_observability ? 1 : 0

  role       = aws_iam_role.observability[0].name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}
