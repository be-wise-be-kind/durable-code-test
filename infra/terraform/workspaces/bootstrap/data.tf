# Purpose: Data source definitions for bootstrap workspace
# Scope: AWS account and region information

# Data source for current AWS account
data "aws_caller_identity" "current" {}

# Data source for current AWS region
data "aws_region" "current" {}
