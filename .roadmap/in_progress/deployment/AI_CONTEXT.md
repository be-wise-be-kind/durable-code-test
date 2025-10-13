# AWS Deployment Infrastructure - AI Context

**Purpose**: AI agent context document for AWS deployment infrastructure implementation and management for the Durable Code Test application

**Scope**: AWS ECS Fargate deployment architecture, Terraform infrastructure management, and CI/CD automation guidance for AI agents

**Overview**: Comprehensive context document providing AI agents with essential information for working on AWS
    deployment infrastructure. Covers ECS Fargate container orchestration, Terraform infrastructure as code
    patterns, cost optimization strategies, and deployment workflows. Includes architectural decisions,
    constraint definitions, file structure guidance, and common operational tasks. Designed to enable AI
    agents to effectively contribute to deployment infrastructure while following established patterns and
    maintaining cost efficiency targets.

**Dependencies**: AWS services (ECS, ECR, ALB, Route53, ACM, CloudWatch), Terraform, Docker, GitHub Actions

**Exports**: AI agent guidance for deployment infrastructure, architectural patterns, cost optimization strategies, and operational procedures

**Related**: PR_BREAKDOWN.md for implementation tasks, PROGRESS_TRACKER.md for current status, deployment workflow documents

**Implementation**: Context-driven guidance with specific examples, constraints, and patterns for AI agent infrastructure development

---

## Overview
This document provides context for AI agents working on the AWS deployment infrastructure for the Durable Code Test application. The deployment uses AWS ECS Fargate for container orchestration, with Terraform for infrastructure as code.

## Project Background
The Durable Code Test application is a full-stack React/FastAPI application currently running locally with Docker Compose. We're deploying it to AWS for production use with a focus on:
- Cost efficiency (~$35-60/month target)
- Minimal operational overhead (serverless containers)
- Scalability for future growth
- Security best practices
- CI/CD automation

## Current Application Structure
- **Frontend**: React with TypeScript, Vite build system
- **Backend**: FastAPI with Python 3.11, Poetry for dependencies
- **Containerization**: Multi-stage Dockerfiles for both services
- **Local Development**: Docker Compose with hot reload
- **Monorepo Structure**: Frontend and backend in same repository

## Target AWS Architecture

### Core Services
- **ECS Fargate**: Serverless container hosting
- **ECR**: Container registry for Docker images
- **ALB**: Application Load Balancer for routing
- **Route53**: DNS management
- **ACM**: SSL certificate management
- **CloudWatch**: Logging and monitoring

### Cost Optimization Strategy
- **Scheduled Infrastructure**: Automatic destroy/create cycles
- **Lambda Automation**: Start at 8 AM, stop at 8 PM on weekdays
- **Weekend Shutdown**: Complete infrastructure teardown Friday evening to Monday morning
- **Manual Override**: Tag-based override for keeping resources running
- **Result**: ~85% cost reduction vs 24/7 operation

### Deployment Strategy
- **Infrastructure as Code**: Terraform for all AWS resources
- **CI/CD**: GitHub Actions with OIDC for passwordless deployment
- **Environments**: dev, staging, production
- **Blue/Green Deployments**: Zero-downtime updates

## Key Decisions Made

### Why ECS Fargate?
- No server management required
- Works with existing Docker setup
- Supports docker-compose.yml
- Cost-effective for small applications
- Easy to scale when needed

### Why Terraform?
- Version controlled infrastructure
- Reproducible environments
- State management
- Module reusability
- Industry standard IaC tool

### Why GitHub Actions with OIDC?
- No long-lived AWS credentials
- Native GitHub integration
- Free for public repositories
- Supports matrix builds
- Easy secret management

## File Structure
```
infra/
├── terraform/
│   ├── main.tf           # Provider and backend config
│   ├── ecs.tf            # ECS cluster and services
│   ├── networking.tf     # VPC and security groups
│   ├── alb.tf            # Load balancer config
│   ├── ecr.tf            # Container registries
│   ├── iam.tf            # Roles and policies
│   ├── variables.tf      # Input variables
│   └── outputs.tf        # Output values
└── environments/
    ├── dev.tfvars
    ├── staging.tfvars
    └── prod.tfvars
```

## Development Workflow
1. Developer pushes code to GitHub
2. GitHub Actions runs tests
3. Docker images built and pushed to ECR
4. ECS service updated with new task definition
5. ALB performs health checks
6. Traffic shifted to new containers
7. Old containers terminated

## Important Constraints
- **Budget**: Keep monthly costs under $60
- **Security**: All traffic must be HTTPS in production
- **Availability**: Single region is acceptable (us-west-2)
- **Database**: No database required initially
- **Storage**: No persistent storage needed yet

## Common Tasks

### Adding New Environment Variables
- Update task definition in `ecs.tf`
- Add to GitHub Secrets
- Update `.env.example`

### Scaling Application
- Adjust `desired_count` in ECS service
- Update Fargate task size if needed
- Consider adding auto-scaling policies

### Updating Infrastructure
- Make changes in Terraform files
- Run `terraform plan` to preview
- Apply changes with `terraform apply`
- Commit changes to git

## Troubleshooting Guide

### Container Won't Start
- Check CloudWatch logs
- Verify health check endpoints
- Ensure correct port mappings
- Check environment variables

### High Costs
- Review Fargate task sizes
- Check data transfer costs
- Optimize container images
- Use spot instances for dev

### Deployment Failures
- Check GitHub Actions logs
- Verify AWS permissions
- Ensure ECR repositories exist
- Check task definition syntax

## References
- [AWS ECS Best Practices](https://docs.aws.amazon.com/AmazonECS/latest/bestpracticesguide/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [GitHub Actions OIDC](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services)

## Notes for AI Agents
- Always check existing Terraform state before making changes
- Use consistent naming conventions (kebab-case for resources)
- Add helpful comments in Terraform files
- Ensure all resources are tagged for cost tracking
- Test infrastructure changes in dev environment first
- Document any manual steps required
- Keep security group rules as restrictive as possible
