# Runtime Infrastructure - AWS WAF for DDoS Protection and Rate Limiting
# Purpose: Deploy AWS WAF with rate limiting and managed rule sets for application security
# Scope: WAF Web ACL, rate limiting rules, AWS managed rules, CloudWatch logging
# Overview: This file creates an AWS WAF Web ACL to protect the Application Load Balancer from
#     common web exploits and DDoS attacks. The configuration includes rate limiting (2000 requests
#     per 5 minutes per IP) to prevent abuse, AWS Managed Core Rule Set for OWASP Top 10 protection,
#     and Known Bad Inputs rule set for common attack patterns. All WAF events are logged to
#     CloudWatch for security monitoring and incident response. The WAF is associated with the ALB
#     to inspect all incoming HTTP/HTTPS traffic before it reaches the application.
# Dependencies: alb.tf (Application Load Balancer), base workspace KMS key for log encryption
# Exports: WAF Web ACL ID, ARN, and CloudWatch log group for monitoring
# Configuration: Rate limit 2000 req/5min, AWS managed rules for OWASP protection
# Security: Blocks excessive requests, protects against common exploits, comprehensive logging
# Related: ALB in alb.tf, CloudWatch metrics for WAF rule hits
# Implementation: Regional WAF for ALB protection, metrics enabled for all rules

# AWS WAF Web ACL
resource "aws_wafv2_web_acl" "main" {
  name  = "${var.project_name}-${local.environment}-waf"
  scope = "REGIONAL"

  default_action {
    allow {}
  }

  # Rate limiting rule - Block IPs exceeding request threshold
  rule {
    name     = "rate-limit"
    priority = 1

    action {
      block {}
    }

    statement {
      rate_based_statement {
        limit              = 2000
        aggregate_key_type = "IP"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${var.project_name}-${local.environment}-rate-limit"
      sampled_requests_enabled   = true
    }
  }

  # AWS Managed Rules - Core Rule Set (OWASP Top 10 protection)
  rule {
    name     = "aws-managed-core-rules"
    priority = 2

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${var.project_name}-${local.environment}-core-rules"
      sampled_requests_enabled   = true
    }
  }

  # AWS Managed Rules - Known Bad Inputs (common attack patterns)
  rule {
    name     = "aws-managed-bad-inputs"
    priority = 3

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesKnownBadInputsRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${var.project_name}-${local.environment}-bad-inputs"
      sampled_requests_enabled   = true
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "${var.project_name}-${local.environment}-waf"
    sampled_requests_enabled   = true
  }

  tags = merge(
    local.common_tags,
    var.additional_tags,
    {
      Name      = "${var.project_name}-${local.environment}-waf"
      Component = "waf"
      Purpose   = "DDoS protection and rate limiting for ALB"
    }
  )
}

# Associate WAF with Application Load Balancer
resource "aws_wafv2_web_acl_association" "main" {
  resource_arn = aws_lb.main.arn
  web_acl_arn  = aws_wafv2_web_acl.main.arn
}

# CloudWatch Log Group for WAF
resource "aws_cloudwatch_log_group" "waf" {
  name              = "/aws/wafv2/${var.project_name}-${local.environment}"
  retention_in_days = lookup(var.log_retention_days, var.environment, 7)
  kms_key_id        = data.terraform_remote_state.base.outputs.kms_logs_key_arn

  tags = merge(
    local.common_tags,
    var.additional_tags,
    {
      Name      = "${var.project_name}-${local.environment}-waf-logs"
      Component = "waf"
      Purpose   = "WAF event logging for security monitoring"
    }
  )
}

# WAF Logging Configuration
resource "aws_wafv2_web_acl_logging_configuration" "main" {
  resource_arn            = aws_wafv2_web_acl.main.arn
  log_destination_configs = [aws_cloudwatch_log_group.waf.arn]
}
