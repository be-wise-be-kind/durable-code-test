# CI/CD Pipeline Implementation Steps

**Purpose**: Detailed implementation guide for GitHub Actions CI/CD pipeline with concrete workflows and deployment automation

**Scope**: Complete CI/CD pipeline setup including build, test, deployment, and validation stages for AWS ECS infrastructure

**Overview**: Comprehensive implementation guide providing concrete GitHub Actions workflows for automated
    CI/CD pipeline setup. Covers build and test stages, Docker image creation, deployment automation,
    health checks, and rollback procedures. Includes specific YAML configurations, environment variables,
    secrets management, and integration with AWS services. Based on lessons learned from durable-code
    deployment experience and optimized for ECS Fargate deployments with proper error handling.

**Dependencies**: GitHub Actions, AWS CLI, Docker, Terraform, ECR repositories, ECS cluster, and OIDC authentication

**Exports**: Complete GitHub Actions workflow files, deployment scripts, environment configurations, and validation procedures

**Related**: DEPLOYMENT_CHECKLIST.md for validation steps, CICD_DEPLOYMENT_LESSONS.md for implementation lessons

**Implementation**: Step-by-step workflow creation with testing validation, environment-specific configurations, and automated deployment integration

---

## Overview
This document provides concrete implementation steps for setting up CI/CD pipelines based on lessons learned from the durable-code deployment.

## GitHub Actions Workflow Structure

### 1. Build and Test Stage
```yaml
name: Build and Test
on:
  pull_request:
    branches: [main, develop]
  push:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      # Frontend tests
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: durable-code-app/frontend/package-lock.json

      - name: Install frontend dependencies
        working-directory: ./durable-code-app/frontend
        run: npm ci

      - name: Run frontend linting
        working-directory: ./durable-code-app/frontend
        run: npm run lint

      - name: Run frontend type checking
        working-directory: ./durable-code-app/frontend
        run: npm run type-check

      - name: Run frontend tests
        working-directory: ./durable-code-app/frontend
        run: npm test

      - name: Test frontend build
        working-directory: ./durable-code-app/frontend
        run: npm run build

      # Backend tests
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install backend dependencies
        working-directory: ./durable-code-app/backend
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run backend linting
        working-directory: ./durable-code-app/backend
        run: ruff check .

      - name: Run backend type checking
        working-directory: ./durable-code-app/backend
        run: mypy .

      - name: Run backend tests
        working-directory: ./durable-code-app/backend
        run: pytest
```

### 2. Docker Build Stage
```yaml
  build-images:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' || github.ref == 'refs/heads/develop'
    outputs:
      frontend-tag: ${{ steps.meta.outputs.frontend-tag }}
      backend-tag: ${{ steps.meta.outputs.backend-tag }}
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-west-2

      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2

      - name: Generate image tags
        id: meta
        run: |
          TIMESTAMP=$(date +%Y%m%d-%H%M%S)
          FRONTEND_TAG="${{ github.sha }}-${TIMESTAMP}"
          BACKEND_TAG="${{ github.sha }}-${TIMESTAMP}"
          echo "frontend-tag=${FRONTEND_TAG}" >> $GITHUB_OUTPUT
          echo "backend-tag=${BACKEND_TAG}" >> $GITHUB_OUTPUT

      # Build frontend with clean context
      - name: Create clean frontend build context
        run: |
          mkdir -p /tmp/frontend-build
          cp -r durable-code-app/frontend/* /tmp/frontend-build/
          # Ensure .dockerignore excludes cache directories
          echo "node_modules" >> /tmp/frontend-build/.dockerignore
          echo ".ruff_cache" >> /tmp/frontend-build/.dockerignore
          echo "*.log" >> /tmp/frontend-build/.dockerignore
          echo ".env*" >> /tmp/frontend-build/.dockerignore

      - name: Build frontend Docker image
        working-directory: /tmp/frontend-build
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          FRONTEND_TAG: ${{ steps.meta.outputs.frontend-tag }}
        run: |
          docker build -t $ECR_REGISTRY/durableai-dev-frontend:$FRONTEND_TAG .
          docker push $ECR_REGISTRY/durableai-dev-frontend:$FRONTEND_TAG

      # Build backend with clean context
      - name: Create clean backend build context
        run: |
          mkdir -p /tmp/backend-build
          cp -r durable-code-app/backend/* /tmp/backend-build/
          echo "__pycache__" >> /tmp/backend-build/.dockerignore
          echo ".ruff_cache" >> /tmp/backend-build/.dockerignore
          echo "*.pyc" >> /tmp/backend-build/.dockerignore
          echo ".env*" >> /tmp/backend-build/.dockerignore

      - name: Build backend Docker image
        working-directory: /tmp/backend-build
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          BACKEND_TAG: ${{ steps.meta.outputs.backend-tag }}
        run: |
          docker build -t $ECR_REGISTRY/durableai-dev-backend:$BACKEND_TAG .
          docker push $ECR_REGISTRY/durableai-dev-backend:$BACKEND_TAG
```

### 3. Deploy Stage
```yaml
  deploy:
    needs: build-images
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    environment: development
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-west-2

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ~1.0

      - name: Update Terraform configuration with new image tags
        working-directory: ./infra/terraform
        env:
          FRONTEND_TAG: ${{ needs.build-images.outputs.frontend-tag }}
          BACKEND_TAG: ${{ needs.build-images.outputs.backend-tag }}
        run: |
          # Update frontend image tag in ecs.tf
          sed -i "s|image = \"\${aws_ecr_repository.frontend.repository_url}:.*\"|image = \"\${aws_ecr_repository.frontend.repository_url}:${FRONTEND_TAG}\"|" ecs.tf
          # Update backend image tag in ecs.tf
          sed -i "s|image = \"\${aws_ecr_repository.backend.repository_url}:.*\"|image = \"\${aws_ecr_repository.backend.repository_url}:${BACKEND_TAG}\"|" ecs.tf

      - name: Terraform Init
        working-directory: ./infra/terraform
        run: terraform init

      - name: Terraform Plan
        working-directory: ./infra/terraform
        run: |
          terraform plan \
            -var="environment=dev" \
            -var="deployment_scope=runtime" \
            -target=aws_ecs_task_definition.frontend \
            -target=aws_ecs_task_definition.backend \
            -target=aws_ecs_service.frontend \
            -target=aws_ecs_service.backend

      - name: Terraform Apply
        working-directory: ./infra/terraform
        run: |
          terraform apply \
            -var="environment=dev" \
            -var="deployment_scope=runtime" \
            -target=aws_ecs_task_definition.frontend \
            -target=aws_ecs_task_definition.backend \
            -target=aws_ecs_service.frontend \
            -target=aws_ecs_service.backend \
            -auto-approve
```

### 4. Health Check and Validation Stage
```yaml
  validate:
    needs: deploy
    runs-on: ubuntu-latest
    steps:
      - name: Wait for deployment to complete
        run: sleep 60

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-west-2

      - name: Check ECS service health
        run: |
          # Wait for services to become stable
          aws ecs wait services-stable \
            --cluster durableai-dev-cluster \
            --services durable-code-dev-frontend durable-code-dev-backend

      - name: Validate health endpoints
        run: |
          # Get ALB DNS name
          ALB_DNS=$(aws elbv2 describe-load-balancers \
            --names durable-code-dev-alb \
            --query 'LoadBalancers[0].DNSName' \
            --output text)

          # Test health endpoint
          curl -f "http://${ALB_DNS}/health" || exit 1

          # Test API endpoints
          curl -f "http://${ALB_DNS}/api/oscilloscope/config" || exit 1

          # Test WebSocket info endpoint
          curl -f "http://${ALB_DNS}/api/oscilloscope/stream/info" || exit 1

      - name: Check ALB target health
        run: |
          # Get target group ARNs
          FRONTEND_TG=$(aws elbv2 describe-target-groups \
            --names durable-code-dev-frontend-tg \
            --query 'TargetGroups[0].TargetGroupArn' \
            --output text)

          BACKEND_TG=$(aws elbv2 describe-target-groups \
            --names durable-code-dev-backend-tg \
            --query 'TargetGroups[0].TargetGroupArn' \
            --output text)

          # Check target health
          aws elbv2 describe-target-health --target-group-arn $FRONTEND_TG
          aws elbv2 describe-target-health --target-group-arn $BACKEND_TG
```

## Rollback Pipeline
```yaml
name: Rollback Deployment
on:
  workflow_dispatch:
    inputs:
      frontend-tag:
        description: 'Frontend image tag to rollback to'
        required: true
      backend-tag:
        description: 'Backend image tag to rollback to'
        required: true

jobs:
  rollback:
    runs-on: ubuntu-latest
    environment: development
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-west-2

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ~1.0

      - name: Rollback Terraform configuration
        working-directory: ./infra/terraform
        env:
          FRONTEND_TAG: ${{ github.event.inputs.frontend-tag }}
          BACKEND_TAG: ${{ github.event.inputs.backend-tag }}
        run: |
          sed -i "s|image = \"\${aws_ecr_repository.frontend.repository_url}:.*\"|image = \"\${aws_ecr_repository.frontend.repository_url}:${FRONTEND_TAG}\"|" ecs.tf
          sed -i "s|image = \"\${aws_ecr_repository.backend.repository_url}:.*\"|image = \"\${aws_ecr_repository.backend.repository_url}:${BACKEND_TAG}\"|" ecs.tf

      - name: Apply rollback
        working-directory: ./infra/terraform
        run: |
          terraform init
          terraform apply \
            -var="environment=dev" \
            -var="deployment_scope=runtime" \
            -target=aws_ecs_task_definition.frontend \
            -target=aws_ecs_task_definition.backend \
            -target=aws_ecs_service.frontend \
            -target=aws_ecs_service.backend \
            -auto-approve
```

## Environment-Specific Configurations

### Development Environment Variables
```yaml
env:
  ENVIRONMENT: dev
  AWS_DEFAULT_REGION: us-west-2
  ECR_REGISTRY: 449870229058.dkr.ecr.us-west-2.amazonaws.com
  ECS_CLUSTER: durableai-dev-cluster
  FRONTEND_SERVICE: durable-code-dev-frontend
  BACKEND_SERVICE: durable-code-dev-backend
```

### Required Secrets
```yaml
# Add these secrets to GitHub repository settings
AWS_ACCESS_KEY_ID: <terraform-deploy-user-access-key>
AWS_SECRET_ACCESS_KEY: <terraform-deploy-user-secret-key>
```

## Makefile Integration
Update `Makefile` to support CI/CD operations:

```makefile
# CI/CD targets
.PHONY: ci-build-frontend ci-build-backend ci-deploy ci-validate

ci-build-frontend:
	@echo "Building frontend for CI/CD"
	mkdir -p /tmp/frontend-build
	cp -r durable-code-app/frontend/* /tmp/frontend-build/
	cd /tmp/frontend-build && docker build -t $(ECR_REGISTRY)/durableai-dev-frontend:$(TAG) .
	docker push $(ECR_REGISTRY)/durableai-dev-frontend:$(TAG)

ci-build-backend:
	@echo "Building backend for CI/CD"
	mkdir -p /tmp/backend-build
	cp -r durable-code-app/backend/* /tmp/backend-build/
	cd /tmp/backend-build && docker build -t $(ECR_REGISTRY)/durableai-dev-backend:$(TAG) .
	docker push $(ECR_REGISTRY)/durableai-dev-backend:$(TAG)

ci-deploy:
	@echo "Deploying to ECS"
	cd infra/terraform && \
	terraform apply \
		-var="environment=$(ENV)" \
		-var="deployment_scope=runtime" \
		-target=aws_ecs_task_definition.frontend \
		-target=aws_ecs_task_definition.backend \
		-target=aws_ecs_service.frontend \
		-target=aws_ecs_service.backend \
		-auto-approve

ci-validate:
	@echo "Validating deployment"
	aws ecs wait services-stable --cluster $(ECS_CLUSTER) --services $(FRONTEND_SERVICE) $(BACKEND_SERVICE)
	@ALB_DNS=$$(aws elbv2 describe-load-balancers --names durable-code-dev-alb --query 'LoadBalancers[0].DNSName' --output text); \
	curl -f "http://$$ALB_DNS/health" && \
	curl -f "http://$$ALB_DNS/api/oscilloscope/config"
```

## Branch Strategy Integration

### Main Branch (Production)
- Triggers full CI/CD pipeline
- Deploys to production environment
- Requires approval for deployment
- Comprehensive health checks

### Develop Branch (Development)
- Triggers CI/CD pipeline
- Deploys to development environment
- Automated deployment
- Basic health checks

### Feature Branches
- Runs tests and builds only
- No deployment
- Optional preview deployments

## Monitoring and Alerting Integration

### CloudWatch Integration
```yaml
  - name: Setup CloudWatch monitoring
    run: |
      aws logs create-log-group --log-group-name /ecs/durable-code-dev/deployment || true
      aws logs put-log-events \
        --log-group-name /ecs/durable-code-dev/deployment \
        --log-stream-name $(date +%Y-%m-%d) \
        --log-events timestamp=$(date +%s000),message="Deployment completed for ${GITHUB_SHA}"
```

### Slack Notifications
```yaml
  - name: Notify deployment status
    uses: 8398a7/action-slack@v3
    with:
      status: ${{ job.status }}
      channel: '#deployments'
      text: 'Deployment ${{ job.status }} for commit ${{ github.sha }}'
    env:
      SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}
    if: always()
```

This pipeline structure ensures all the lessons learned are captured and automated for future deployments!
