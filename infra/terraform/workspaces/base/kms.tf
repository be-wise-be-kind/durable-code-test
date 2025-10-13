# Base Infrastructure - KMS Keys for Encryption at Rest
# Purpose: Provides customer-managed encryption keys for CloudWatch Logs and ECR repositories
# Scope: KMS keys with automatic rotation, aliases for easy reference, and policies for service integration
# Overview: This file creates KMS keys to enable encryption at rest for sensitive data storage.
#     CloudWatch Logs encryption protects application logs from unauthorized access at rest.
#     ECR encryption protects container images stored in repositories. All keys have automatic
#     rotation enabled for security best practices, and aliases provide stable references across
#     environments. Key policies grant necessary permissions to AWS services while maintaining
#     least privilege access.
# Dependencies: networking.tf (provides data.aws_caller_identity.current)
# Exports: KMS key ARNs and aliases for use by CloudWatch and ECR resources
# Configuration: Automatic key rotation enabled, 30-day deletion window for safety
# Security: Keys are customer-managed, policies follow least privilege, rotation enabled
# Related: Runtime workspace uses logs key for CloudWatch log groups, ECR repositories use ECR key
# Implementation: Separate keys for logs and ECR to enable independent access control and lifecycle

# KMS key for CloudWatch Logs encryption
resource "aws_kms_key" "logs" {
  description             = "${var.project_name}-${local.environment}-logs-encryption"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "Allow CloudWatch Logs"
        Effect = "Allow"
        Principal = {
          Service = "logs.${var.aws_region}.amazonaws.com"
        }
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:CreateGrant",
          "kms:DescribeKey"
        ]
        Resource = "*"
        Condition = {
          ArnLike = {
            "kms:EncryptionContext:aws:logs:arn" = "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:*"
          }
        }
      }
    ]
  })

  tags = merge(
    local.common_tags,
    var.additional_tags,
    {
      Name      = "${var.project_name}-${local.environment}-logs-key"
      Component = "kms"
      Purpose   = "Encryption key for CloudWatch Logs"
    }
  )
}

# KMS alias for CloudWatch Logs key
resource "aws_kms_alias" "logs" {
  name          = "alias/${var.project_name}-${local.environment}-logs"
  target_key_id = aws_kms_key.logs.key_id
}

# KMS key for ECR encryption
resource "aws_kms_key" "ecr" {
  description             = "${var.project_name}-${local.environment}-ecr-encryption"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  tags = merge(
    local.common_tags,
    var.additional_tags,
    {
      Name      = "${var.project_name}-${local.environment}-ecr-key"
      Component = "kms"
      Purpose   = "Encryption key for ECR repositories"
    }
  )
}

# KMS alias for ECR key
resource "aws_kms_alias" "ecr" {
  name          = "alias/${var.project_name}-${local.environment}-ecr"
  target_key_id = aws_kms_key.ecr.key_id
}
