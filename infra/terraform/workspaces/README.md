# Terraform Workspaces

This directory contains Terraform workspace configurations for separating base (persistent) and runtime (ephemeral) infrastructure.

## Documentation

For comprehensive documentation on Terraform workspaces, including:
- Architecture overview
- Quick start guide
- Resource separation strategy
- Cost optimization approach
- Common operations
- Troubleshooting

See: [.ai/howto/terraform-workspaces.md](../../../.ai/howto/terraform-workspaces.md)

## Directory Structure

```
workspaces/
├── bootstrap/      # Bootstrap workspace (OIDC, IAM, S3 state, DynamoDB locks)
├── base/           # Base infrastructure workspace (VPC, ECR, Route53, ACM, KMS)
├── runtime/        # Runtime infrastructure workspace (ECS, ALB, NAT, WAF, DNS)
└── README.md       # This file
```

## Quick Commands

```bash
# Initialize workspaces
just infra init base
just infra init runtime

# Plan changes
just infra plan base
just infra plan runtime

# Deploy
just infra up base
just infra up runtime

# Check status
just infra status
```
