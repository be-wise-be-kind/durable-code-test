# CI/CD Deployment Lessons Learned

**Purpose**: Critical lessons learned documentation from AWS ECS Fargate deployment experience to improve future CI/CD implementations

**Scope**: Real-world deployment challenges, solutions, and requirements for CI/CD pipelines based on actual implementation experience

**Overview**: Comprehensive documentation of critical deployment issues encountered during durable-code application
    deployment to AWS ECS Fargate infrastructure. Covers WebSocket URL generation problems, Docker build context
    issues, ECR image management challenges, service discovery configuration, and ALB routing limitations.
    Provides specific solutions implemented and detailed CI/CD requirements to prevent similar issues in future
    deployments. Essential reference for understanding production deployment complexities and preventive measures.

**Dependencies**: AWS ECS, Fargate, ECR, ALB, Route53, Docker, Terraform, and WebSocket service configurations

**Exports**: Deployment issue analysis, proven solutions, CI/CD requirements, and preventive measures for future implementations

**Related**: DEPLOYMENT_CHECKLIST.md for validation procedures, CICD_PIPELINE_STEPS.md for implementation steps

**Implementation**: Issue documentation with root cause analysis, implemented solutions, and specific CI/CD requirements for prevention

---

## Overview
This document captures critical lessons learned from deploying the durable-code application to AWS ECS Fargate, focusing on issues that must be addressed in CI/CD pipelines for future PRs.

## Critical Deployment Issues and Solutions

### 1. WebSocket URL Generation in Production

**Problem**: Frontend WebSocket connections failed in production due to incorrect URL generation when running behind AWS Application Load Balancer (ALB).

**Root Cause**: The WebSocket service was appending `:8000` port to URLs when detecting production environment (port 80/443), but ALB handles routing internally without exposing backend ports.

**Failed Connection**:
```
ws://durable-code-dev-alb-1541042360.us-west-2.elb.amazonaws.com:8000/api/oscilloscope/stream
```

**Correct Connection**:
```
ws://durable-code-dev-alb-1541042360.us-west-2.elb.amazonaws.com/api/oscilloscope/stream
```

**Solution Applied**:
- Location: `durable-code-app/frontend/src/features/demo/services/websocketService.ts:68`
- Fix: Modified WebSocket URL generation to omit port when running on standard HTTP/HTTPS ports (80/443)

```typescript
} else if (!currentPort || currentPort === 80 || currentPort === 443) {
  // Production mode - no port or standard HTTP/HTTPS ports
  // Don't specify a port (ALB handles routing)
  url = `${protocol}//${host}${WEBSOCKET_CONFIG.ENDPOINT}`;
}
```

**CI/CD Requirements**:
1. **Environment Detection Testing**: Add automated tests that verify WebSocket URL generation in different environments
2. **Load Balancer Testing**: Include integration tests that validate WebSocket connections through ALB
3. **Port Configuration Validation**: Ensure CI/CD validates that production builds don't hardcode backend ports

### 2. Docker Build Context and Permission Issues

**Problem**: Docker builds failed due to `.ruff_cache` permission issues when building from the source directory.

**Root Cause**: Build context included cached files with restrictive permissions that Docker couldn't access.

**Solutions**:
1. **Updated .dockerignore**: Added `.ruff_cache` to prevent inclusion in build context
2. **Clean Build Strategy**: Built from temporary directories with clean file copies
3. **Permission Management**: Ensured Docker build context has proper file permissions

**CI/CD Requirements**:
1. **Clean Build Environment**: Always build Docker images from clean directories
2. **Build Context Validation**: Verify `.dockerignore` excludes cache and temporary files
3. **Permission Checks**: Validate file permissions before Docker builds

### 3. ECR Image Tag Management

**Problem**: ECR repository had immutable tag policy, preventing overwrite of `latest` tags.

**Solution**: Used versioned tags (v2, v3, v4) instead of overwriting `latest`.

**CI/CD Requirements**:
1. **Version Tagging Strategy**: Use semantic versioning or build numbers for Docker tags
2. **Tag Immutability Handling**: Never rely on overwriting existing tags
3. **Image Cleanup**: Implement automated cleanup of old images to manage storage costs

### 4. ECS Deployment and Service Updates

**Problem**: ECS services didn't automatically update when new images were pushed to ECR.

**Solution**: Required explicit Terraform updates to task definitions and service deployments.

**Deployment Process**:
1. Build and push new Docker image with version tag
2. Update Terraform configuration with new image tag
3. Apply Terraform changes to update task definition
4. ECS service automatically deploys new task definition

**CI/CD Requirements**:
1. **Automated Task Definition Updates**: CI/CD must update Terraform configurations with new image tags
2. **Health Check Validation**: Verify new containers pass health checks before deployment completion
3. **Rollback Capability**: Implement automated rollback if deployment health checks fail

### 5. ALB Routing Configuration

**Problem**: Application Load Balancer wasn't configured to route oscilloscope API endpoints to backend service.

**Solution**: Updated ALB listener rules to include `/api/oscilloscope/*` path patterns.

**Limitation Discovered**: AWS ALB listener rules are limited to 5 path patterns per condition.

**ALB Configuration**:
```terraform
condition {
  path_pattern {
    values = ["/api/*", "/health", "/oscilloscope/*"]  # Reduced to fit 5-pattern limit
  }
}
```

**CI/CD Requirements**:
1. **Route Validation**: Verify all API endpoints are properly routed through ALB
2. **Path Pattern Limits**: Ensure ALB rules don't exceed AWS limits (5 patterns per condition)
3. **Integration Testing**: Test all API routes through the load balancer, not just direct backend connections

### 6. Service Discovery Configuration

**Problem**: Frontend couldn't resolve backend service via internal DNS.

**Solution**: Configured AWS Service Discovery with private DNS namespace (`dev.local`).

**Configuration**:
- Backend accessible at: `backend.dev.local:8000`
- Frontend accessible at: `frontend.dev.local:3000`
- Nginx proxy configuration updated to use service discovery DNS

**CI/CD Requirements**:
1. **DNS Resolution Testing**: Validate service-to-service communication via service discovery
2. **Network Configuration**: Ensure all services are deployed to correct subnets with proper security groups
3. **Service Registration**: Verify services properly register with service discovery

## Deployment Pipeline Requirements

### Pre-Deployment Validation
1. **TypeScript Compilation**: Ensure all TypeScript code compiles without errors
2. **Linting**: Run all linting checks (ESLint, Ruff, etc.)
3. **Unit Tests**: Execute full test suite including WebSocket service tests
4. **Build Validation**: Verify Docker images build successfully with clean contexts

### Deployment Steps
1. **Environment Setup**: Configure AWS credentials and Terraform backend
2. **Image Building**: Build Docker images with versioned tags in clean environments
3. **ECR Push**: Push images to ECR with proper authentication
4. **Infrastructure Updates**: Update Terraform configurations with new image tags
5. **Terraform Apply**: Deploy infrastructure changes with proper targeting
6. **Health Verification**: Validate service health and connectivity

### Post-Deployment Validation
1. **Health Check Verification**: Ensure all services pass health checks
2. **Integration Testing**: Test WebSocket connections and API endpoints through ALB
3. **Performance Monitoring**: Verify application performance meets baseline requirements
4. **Rollback Readiness**: Prepare rollback procedures if issues are detected

## Environment-Specific Considerations

### Development Environment
- Use Fargate Spot instances for cost optimization (70% savings)
- Minimal resource allocation (256 CPU, 512 MB memory)
- Relaxed health check intervals
- Basic logging configuration

### Production Environment
- Use standard Fargate for reliability
- Higher resource allocation (512+ CPU, 1024+ MB memory)
- Strict health check intervals
- Comprehensive logging and monitoring
- Auto-scaling configuration
- SSL/TLS termination at ALB level

## Monitoring and Observability

### Required Monitoring
1. **ECS Service Health**: Monitor running task counts and health status
2. **ALB Target Health**: Monitor target group health and response times
3. **Container Logs**: Centralized logging via CloudWatch
4. **Performance Metrics**: Monitor CPU, memory, and network utilization
5. **WebSocket Connections**: Monitor WebSocket connection success rates

### Alerting
1. **Service Degradation**: Alert when services become unhealthy
2. **High Latency**: Alert when response times exceed thresholds
3. **Connection Failures**: Alert when WebSocket connections fail
4. **Resource Exhaustion**: Alert when resources approach limits

## Security Considerations

### Network Security
- Services deployed in private subnets
- Security groups restrict access to necessary ports only
- ALB provides SSL termination and security headers
- No direct internet access to backend services

### Image Security
- Use minimal base images (Alpine Linux)
- Regular security scanning of Docker images
- Non-root user execution in containers
- Secrets management via AWS Systems Manager Parameter Store

## Cost Optimization

### Development Environment
- Fargate Spot instances (70% cost reduction)
- Minimal resource allocation
- Auto-shutdown capabilities
- Limited logging retention (7 days)

### Production Environment
- Right-sized resource allocation
- Auto-scaling based on CPU utilization
- Extended logging retention (30 days)
- Reserved capacity for predictable workloads

## Troubleshooting Guide

### Common Issues
1. **WebSocket Connection Failures**: Check URL generation and ALB routing
2. **Service Discovery Issues**: Verify DNS resolution and security group rules
3. **Container Health Failures**: Check health check configuration and application startup
4. **Resource Constraints**: Monitor CPU and memory utilization
5. **Network Connectivity**: Verify subnet routing and security group rules

### Diagnostic Commands
```bash
# Check ECS service status
aws ecs describe-services --cluster durableai-dev-cluster --services durable-code-dev-frontend

# View container logs
aws logs tail /ecs/durable-code-dev/frontend --follow

# Test ALB health
curl -s http://durable-code-dev-alb-1541042360.us-west-2.elb.amazonaws.com/health

# Test API endpoints
curl -s http://durable-code-dev-alb-1541042360.us-west-2.elb.amazonaws.com/api/oscilloscope/config
```

## Future Improvements

### CI/CD Pipeline Enhancements
1. **Blue-Green Deployments**: Implement zero-downtime deployments
2. **Canary Deployments**: Gradual rollout of new versions
3. **Automated Rollback**: Automatic rollback on health check failures
4. **Multi-Environment Promotion**: Promote changes through dev → staging → prod

### Infrastructure Improvements
1. **CDN Integration**: Add CloudFront for static asset delivery
2. **Database Integration**: Add RDS for persistent data storage
3. **Caching Layer**: Add ElastiCache for improved performance
4. **Backup Strategy**: Implement automated backup and restore procedures

This document should be updated with each deployment to capture new lessons learned and evolving best practices.
