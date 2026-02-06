#!/bin/bash
# Purpose: Deploy application containers to AWS ECS with automated image building and service updates
# Scope: Docker image building, ECR registry operations, ECS task definition updates, and service deployment
# Overview: This script provides a complete deployment workflow for containerized applications
#     to AWS ECS Fargate. It handles Docker image building for both frontend and backend services,
#     authentication with ECR registry, image tagging and pushing, task definition updates with
#     new image references, and ECS service updates to deploy new versions. The script includes
#     error handling, environment variable configuration, and deployment status reporting.
#     Supports multiple environments through ENV variable with automatic resource naming
#     and configuration. Integrates with existing Terraform-managed infrastructure including
#     ECR repositories, ECS clusters, and service configurations.
# Dependencies: Docker, AWS CLI, jq, ECR repositories, ECS cluster and services
# Usage: ENV=dev ./deploy-app.sh or ENV=staging ./deploy-app.sh
# Environment: Supports dev, staging, and prod environments with environment-specific configurations
# Related: Links to ECS service configurations, ECR repository policies, and CI/CD pipeline documentation
# Implementation: Uses Docker multi-stage builds, ECR lifecycle policies, and zero-downtime ECS deployments

set -e

# Configuration
AWS_REGION="us-west-2"

# Dynamically retrieve AWS account ID (security best practice - no hardcoded credentials)
echo "Retrieving AWS account ID..."
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null)
if [ -z "$AWS_ACCOUNT_ID" ] || [ "$AWS_ACCOUNT_ID" = "None" ]; then
  echo "ERROR: Failed to retrieve AWS account ID. Please check your AWS credentials."
  echo "Run 'aws configure' or set AWS_PROFILE environment variable."
  exit 1
fi

ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
ENV="${ENV:-dev}"
TAG="v$(date +%Y%m%d-%H%M%S)"

# Resource naming - matches Terraform infrastructure
# ECR repositories use durableai prefix, ECS resources use durable-code prefix
ECR_PREFIX="durableai"
ECS_PREFIX="durable-code"

# Get deployment timestamp for version display
BUILD_TIMESTAMP=$(date -u +"%Y-%m-%d %H:%M:%S UTC")

# Determine API URL based on environment
if [ "${ENV}" = "dev" ]; then
  # For dev environment, use vanity URL if available, otherwise ALB DNS
  API_URL="${API_URL:-https://dev.durableaicoding.net}"
elif [ "${ENV}" = "staging" ]; then
  API_URL="${API_URL:-https://staging.durableaicoding.net}"
elif [ "${ENV}" = "prod" ]; then
  API_URL="${API_URL:-https://durableaicoding.net}"
else
  # Fallback to ALB DNS for unknown environments
  API_URL="${API_URL:-http://${ECS_PREFIX}-${ENV}-alb.amazonaws.com}"
fi

echo "=== Starting Application Deployment ==="
echo "Environment: ${ENV}"
echo "ECR Registry: ${ECR_REGISTRY}"
echo "Tag: ${TAG}"
echo "Build Timestamp: ${BUILD_TIMESTAMP}"
echo "API URL: ${API_URL}"

# Login to ECR
echo "Logging into ECR..."
if [ -n "${GITHUB_ACTIONS}" ]; then
  # Running in GitHub Actions - use OIDC credentials from environment
  # Unset AWS_PROFILE to prevent it from overriding OIDC credentials
  unset AWS_PROFILE
  echo "Using AWS credentials from GitHub Actions OIDC"
  aws ecr get-login-password --region "${AWS_REGION}" | docker login --username AWS --password-stdin "${ECR_REGISTRY}"
elif [ -n "${AWS_PROFILE}" ]; then
  # Running locally with AWS profile
  echo "Using AWS profile: ${AWS_PROFILE}"
  aws ecr get-login-password --region "${AWS_REGION}" --profile "${AWS_PROFILE}" | docker login --username AWS --password-stdin "${ECR_REGISTRY}"
else
  # Fallback to environment credentials
  echo "Using AWS credentials from environment"
  aws ecr get-login-password --region "${AWS_REGION}" | docker login --username AWS --password-stdin "${ECR_REGISTRY}"
fi

# Build and tag images
echo "Building Docker images..."

# Frontend
echo "Building frontend..."
docker build -t "${ECR_PREFIX}-${ENV}-frontend:${TAG}" \
  -f .docker/dockerfiles/Dockerfile.frontend \
  --target prod \
  --build-arg BUILD_TIMESTAMP="${BUILD_TIMESTAMP}" \
  --build-arg API_URL="${API_URL}" \
  .
docker tag "${ECR_PREFIX}-${ENV}-frontend:${TAG}" "${ECR_REGISTRY}/${ECR_PREFIX}-${ENV}-frontend:${TAG}"

# Backend
echo "Building backend..."
docker build -t "${ECR_PREFIX}-${ENV}-backend:${TAG}" \
  -f .docker/dockerfiles/Dockerfile.backend \
  --target prod \
  .
docker tag "${ECR_PREFIX}-${ENV}-backend:${TAG}" "${ECR_REGISTRY}/${ECR_PREFIX}-${ENV}-backend:${TAG}"

# Push images to ECR (versioned tags for auditability, latest for infra recovery)
echo "Pushing images to ECR..."
docker push "${ECR_REGISTRY}/${ECR_PREFIX}-${ENV}-frontend:${TAG}"
docker push "${ECR_REGISTRY}/${ECR_PREFIX}-${ENV}-backend:${TAG}"

# Tag and push 'latest' so Terraform task definitions referencing :latest always resolve
docker tag "${ECR_REGISTRY}/${ECR_PREFIX}-${ENV}-frontend:${TAG}" "${ECR_REGISTRY}/${ECR_PREFIX}-${ENV}-frontend:latest"
docker tag "${ECR_REGISTRY}/${ECR_PREFIX}-${ENV}-backend:${TAG}" "${ECR_REGISTRY}/${ECR_PREFIX}-${ENV}-backend:latest"
docker push "${ECR_REGISTRY}/${ECR_PREFIX}-${ENV}-frontend:latest"
docker push "${ECR_REGISTRY}/${ECR_PREFIX}-${ENV}-backend:latest"

echo "=== Registering New Task Definitions ==="
echo "Creating new task definitions with updated images..."

# Determine AWS CLI profile usage
USE_PROFILE=false
if [ -z "${GITHUB_ACTIONS}" ] && [ -n "${AWS_PROFILE}" ]; then
  USE_PROFILE=true
fi

# Get current task definitions and update image tags
echo "Fetching current frontend task definition..."
if [ "${USE_PROFILE}" = true ]; then
  aws ecs describe-task-definition \
    --task-definition "${ECS_PREFIX}-${ENV}-frontend" \
    --region "${AWS_REGION}" \
    --profile "${AWS_PROFILE}" \
    --query 'taskDefinition' \
    --output json > /tmp/frontend-task-def.json
else
  aws ecs describe-task-definition \
    --task-definition "${ECS_PREFIX}-${ENV}-frontend" \
    --region "${AWS_REGION}" \
    --query 'taskDefinition' \
    --output json > /tmp/frontend-task-def.json
fi

# Update the image tag, ensure port 3000, and fix health check in the task definition
jq ".containerDefinitions[0].image = \"${ECR_REGISTRY}/${ECR_PREFIX}-${ENV}-frontend:${TAG}\" | .containerDefinitions[0].portMappings[0].containerPort = 3000 | .containerDefinitions[0].portMappings[0].hostPort = 3000 | .containerDefinitions[0].healthCheck.command = [\"CMD-SHELL\", \"curl -f http://localhost:3000/ || exit 1\"] | del(.taskDefinitionArn, .revision, .status, .requiresAttributes, .compatibilities, .registeredAt, .registeredBy)" /tmp/frontend-task-def.json > /tmp/frontend-task-def-new.json

echo "Registering new frontend task definition..."
if [ "${USE_PROFILE}" = true ]; then
  FRONTEND_TASK_ARN=$(aws ecs register-task-definition \
    --cli-input-json file:///tmp/frontend-task-def-new.json \
    --region "${AWS_REGION}" \
    --profile "${AWS_PROFILE}" \
    --query 'taskDefinition.taskDefinitionArn' \
    --output text)
else
  FRONTEND_TASK_ARN=$(aws ecs register-task-definition \
    --cli-input-json file:///tmp/frontend-task-def-new.json \
    --region "${AWS_REGION}" \
    --query 'taskDefinition.taskDefinitionArn' \
    --output text)
fi

echo "Fetching current backend task definition..."
if [ "${USE_PROFILE}" = true ]; then
  aws ecs describe-task-definition \
    --task-definition "${ECS_PREFIX}-${ENV}-backend" \
    --region "${AWS_REGION}" \
    --profile "${AWS_PROFILE}" \
    --query 'taskDefinition' \
    --output json > /tmp/backend-task-def.json
else
  aws ecs describe-task-definition \
    --task-definition "${ECS_PREFIX}-${ENV}-backend" \
    --region "${AWS_REGION}" \
    --query 'taskDefinition' \
    --output json > /tmp/backend-task-def.json
fi

# Update the image tag in the task definition
jq ".containerDefinitions[0].image = \"${ECR_REGISTRY}/${ECR_PREFIX}-${ENV}-backend:${TAG}\" | del(.taskDefinitionArn, .revision, .status, .requiresAttributes, .compatibilities, .registeredAt, .registeredBy)" /tmp/backend-task-def.json > /tmp/backend-task-def-new.json

echo "Registering new backend task definition..."
if [ "${USE_PROFILE}" = true ]; then
  BACKEND_TASK_ARN=$(aws ecs register-task-definition \
    --cli-input-json file:///tmp/backend-task-def-new.json \
    --region "${AWS_REGION}" \
    --profile "${AWS_PROFILE}" \
    --query 'taskDefinition.taskDefinitionArn' \
    --output text)
else
  BACKEND_TASK_ARN=$(aws ecs register-task-definition \
    --cli-input-json file:///tmp/backend-task-def-new.json \
    --region "${AWS_REGION}" \
    --query 'taskDefinition.taskDefinitionArn' \
    --output text)
fi

echo "=== Updating ECS Services ==="
echo "Updating services with new task definitions..."

# Update ECS services to use the new task definitions
echo "Updating frontend service with new task definition..."
if [ "${USE_PROFILE}" = true ]; then
  aws ecs update-service \
    --cluster "${ECS_PREFIX}-${ENV}-cluster" \
    --service "${ECS_PREFIX}-${ENV}-frontend" \
    --task-definition "${FRONTEND_TASK_ARN}" \
    --force-new-deployment \
    --region "${AWS_REGION}" \
    --profile "${AWS_PROFILE}" \
    --output json > /dev/null
else
  aws ecs update-service \
    --cluster "${ECS_PREFIX}-${ENV}-cluster" \
    --service "${ECS_PREFIX}-${ENV}-frontend" \
    --task-definition "${FRONTEND_TASK_ARN}" \
    --force-new-deployment \
    --region "${AWS_REGION}" \
    --output json > /dev/null
fi

echo "Updating backend service with new task definition..."
if [ "${USE_PROFILE}" = true ]; then
  aws ecs update-service \
    --cluster "${ECS_PREFIX}-${ENV}-cluster" \
    --service "${ECS_PREFIX}-${ENV}-backend" \
    --task-definition "${BACKEND_TASK_ARN}" \
    --force-new-deployment \
    --region "${AWS_REGION}" \
    --profile "${AWS_PROFILE}" \
    --output json > /dev/null
else
  aws ecs update-service \
    --cluster "${ECS_PREFIX}-${ENV}-cluster" \
    --service "${ECS_PREFIX}-${ENV}-backend" \
    --task-definition "${BACKEND_TASK_ARN}" \
    --force-new-deployment \
    --region "${AWS_REGION}" \
    --output json > /dev/null
fi

echo "=== Deployment Complete ==="
echo "Images pushed successfully to ECR"
echo "ECS services updated to use tag: ${TAG}"
echo ""
echo "The services are now redeploying. Check the ECS console for deployment status."
echo "To access the application, check the ALB DNS name:"
echo ""
if [ "${USE_PROFILE}" = true ]; then
  aws elbv2 describe-load-balancers --names "${ECS_PREFIX}-${ENV}-alb" --profile "${AWS_PROFILE}" --query 'LoadBalancers[0].DNSName' --output text
else
  aws elbv2 describe-load-balancers --names "${ECS_PREFIX}-${ENV}-alb" --query 'LoadBalancers[0].DNSName' --output text
fi
