# Base Infrastructure - VPC Flow Logs for Network Traffic Monitoring
# Purpose: Enable comprehensive network traffic logging for security monitoring and troubleshooting
# Scope: VPC Flow Logs with CloudWatch integration, IAM roles for log delivery
# Overview: This file creates VPC Flow Logs to capture information about IP traffic going to and from
#     network interfaces in the VPC. Flow logs help monitor network traffic patterns, troubleshoot
#     connectivity issues, and detect security threats. Logs are delivered to CloudWatch Logs with
#     KMS encryption for security. The configuration includes an IAM role with minimal permissions
#     for the VPC Flow Logs service to write to CloudWatch. All traffic (ACCEPT and REJECT) is
#     logged for comprehensive visibility.
# Dependencies: networking.tf (VPC), kms.tf (encryption key for logs)
# Exports: CloudWatch log group ARN, Flow Log ID for monitoring and operations
# Configuration: Captures ALL traffic (accepted and rejected) with CloudWatch destination
# Security: Logs encrypted with KMS, IAM role follows least privilege principle
# Related: Runtime workspace may add additional flow logs for ephemeral resources
# Implementation: Uses CloudWatch Logs for centralized log management and analysis

# CloudWatch Log Group for VPC Flow Logs
resource "aws_cloudwatch_log_group" "vpc_flow_logs" {
  name              = "/aws/vpc/${var.project_name}-${local.environment}"
  retention_in_days = lookup(var.log_retention_days, var.environment, 7)
  kms_key_id        = aws_kms_key.logs.arn

  tags = merge(
    local.common_tags,
    var.additional_tags,
    {
      Name      = "${var.project_name}-${local.environment}-vpc-flow-logs"
      Component = "vpc-flow-logs"
      Purpose   = "Network traffic logging for security and troubleshooting"
    }
  )
}

# IAM Role for VPC Flow Logs
resource "aws_iam_role" "vpc_flow_logs" {
  name = "${var.project_name}-${local.environment}-vpc-flow-logs"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "vpc-flow-logs.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = merge(
    local.common_tags,
    var.additional_tags,
    {
      Name      = "${var.project_name}-${local.environment}-vpc-flow-logs-role"
      Component = "vpc-flow-logs"
      Purpose   = "IAM role for VPC Flow Logs service"
    }
  )
}

# IAM Policy for VPC Flow Logs
resource "aws_iam_role_policy" "vpc_flow_logs" {
  name = "${var.project_name}-${local.environment}-vpc-flow-logs"
  role = aws_iam_role.vpc_flow_logs.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams"
        ]
        Resource = [
          aws_cloudwatch_log_group.vpc_flow_logs.arn,
          "${aws_cloudwatch_log_group.vpc_flow_logs.arn}:*"
        ]
      }
    ]
  })
}

# VPC Flow Log
resource "aws_flow_log" "main" {
  iam_role_arn    = aws_iam_role.vpc_flow_logs.arn
  log_destination = aws_cloudwatch_log_group.vpc_flow_logs.arn
  traffic_type    = "ALL"
  vpc_id          = aws_vpc.main.id

  tags = merge(
    local.common_tags,
    var.additional_tags,
    {
      Name      = "${var.project_name}-${local.environment}-vpc-flow-log"
      Component = "vpc-flow-logs"
      Purpose   = "Capture all network traffic for security monitoring"
    }
  )
}
