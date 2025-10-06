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
AWS_ACCOUNT_ID="449870229058"
ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
ENV="${ENV:-dev}"
TAG="v$(date +%Y%m%d-%H%M%S)"

# Get deployment timestamp for version display
BUILD_TIMESTAMP=$(date -u +"%Y-%m-%d %H:%M:%S UTC")

echo "=== Starting Application Deployment ==="
echo "Environment: ${ENV}"
echo "ECR Registry: ${ECR_REGISTRY}"
echo "Tag: ${TAG}"
echo "Build Timestamp: ${BUILD_TIMESTAMP}"

# Login to ECR
echo "Logging into ECR..."
if [ -n "${GITHUB_ACTIONS}" ]; then
  # Running in GitHub Actions - use OIDC credentials from environment
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
docker build -t "durableai-${ENV}-frontend:${TAG}" \
  -f .docker/dockerfiles/Dockerfile.frontend \
  --target prod \
  --build-arg BUILD_TIMESTAMP="${BUILD_TIMESTAMP}" \
  .
docker tag "durableai-${ENV}-frontend:${TAG}" "${ECR_REGISTRY}/durableai-${ENV}-frontend:${TAG}"

# Backend
echo "Building backend..."
docker build -t "durableai-${ENV}-backend:${TAG}" \
  -f .docker/dockerfiles/Dockerfile.backend \
  --target prod \
  .
docker tag "durableai-${ENV}-backend:${TAG}" "${ECR_REGISTRY}/durableai-${ENV}-backend:${TAG}"

# Push images to ECR
echo "Pushing images to ECR..."
docker push "${ECR_REGISTRY}/durableai-${ENV}-frontend:${TAG}"
docker push "${ECR_REGISTRY}/durableai-${ENV}-backend:${TAG}"

echo "=== Registering New Task Definitions ==="
echo "Creating new task definitions with updated images..."

# Set AWS CLI profile flag if needed
AWS_PROFILE_FLAG=""
if [ -z "${GITHUB_ACTIONS}" ] && [ -n "${AWS_PROFILE}" ]; then
  AWS_PROFILE_FLAG="--profile ${AWS_PROFILE}"
fi

# Get current task definitions and update image tags
echo "Fetching current frontend task definition..."
aws ecs describe-task-definition \
  --task-definition "durableai-${ENV}-frontend" \
  --region "${AWS_REGION}" \
  ${AWS_PROFILE_FLAG} \
  --query 'taskDefinition' \
  --output json > /tmp/frontend-task-def.json

# Update the image tag, ensure port 3000, and fix health check in the task definition
jq ".containerDefinitions[0].image = \"${ECR_REGISTRY}/durableai-${ENV}-frontend:${TAG}\" | .containerDefinitions[0].portMappings[0].containerPort = 3000 | .containerDefinitions[0].portMappings[0].hostPort = 3000 | .containerDefinitions[0].healthCheck.command = [\"CMD-SHELL\", \"curl -f http://localhost:3000/ || exit 1\"] | del(.taskDefinitionArn, .revision, .status, .requiresAttributes, .compatibilities, .registeredAt, .registeredBy)" /tmp/frontend-task-def.json > /tmp/frontend-task-def-new.json

echo "Registering new frontend task definition..."
FRONTEND_TASK_ARN=$(aws ecs register-task-definition \
  --cli-input-json file:///tmp/frontend-task-def-new.json \
  --region "${AWS_REGION}" \
  ${AWS_PROFILE_FLAG} \
  --query 'taskDefinition.taskDefinitionArn' \
  --output text)

echo "Fetching current backend task definition..."
aws ecs describe-task-definition \
  --task-definition "durableai-${ENV}-backend" \
  --region "${AWS_REGION}" \
  ${AWS_PROFILE_FLAG} \
  --query 'taskDefinition' \
  --output json > /tmp/backend-task-def.json

# Update the image tag in the task definition
jq ".containerDefinitions[0].image = \"${ECR_REGISTRY}/durableai-${ENV}-backend:${TAG}\" | del(.taskDefinitionArn, .revision, .status, .requiresAttributes, .compatibilities, .registeredAt, .registeredBy)" /tmp/backend-task-def.json > /tmp/backend-task-def-new.json

echo "Registering new backend task definition..."
BACKEND_TASK_ARN=$(aws ecs register-task-definition \
  --cli-input-json file:///tmp/backend-task-def-new.json \
  --region "${AWS_REGION}" \
  ${AWS_PROFILE_FLAG} \
  --query 'taskDefinition.taskDefinitionArn' \
  --output text)

echo "=== Updating ECS Services ==="
echo "Updating services with new task definitions..."

# Update ECS services to use the new task definitions
echo "Updating frontend service with new task definition..."
aws ecs update-service \
  --cluster "durableai-${ENV}-cluster" \
  --service "durableai-${ENV}-frontend" \
  --task-definition "${FRONTEND_TASK_ARN}" \
  --force-new-deployment \
  --region "${AWS_REGION}" \
  ${AWS_PROFILE_FLAG} \
  --output json > /dev/null

echo "Updating backend service with new task definition..."
aws ecs update-service \
  --cluster "durableai-${ENV}-cluster" \
  --service "durableai-${ENV}-backend" \
  --task-definition "${BACKEND_TASK_ARN}" \
  --force-new-deployment \
  --region "${AWS_REGION}" \
  ${AWS_PROFILE_FLAG} \
  --output json > /dev/null

echo "=== Deployment Complete ==="
echo "Images pushed successfully to ECR"
echo "ECS services updated to use tag: ${TAG}"
echo ""
echo "The services are now redeploying. Check the ECS console for deployment status."
echo "To access the application, check the ALB DNS name:"
echo ""
aws elbv2 describe-load-balancers --names "durableai-${ENV}-alb" ${AWS_PROFILE_FLAG} --query 'LoadBalancers[0].DNSName' --output text
