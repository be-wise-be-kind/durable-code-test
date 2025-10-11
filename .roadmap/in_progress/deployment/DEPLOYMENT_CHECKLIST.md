# Deployment Checklist for CI/CD

**Purpose**: Comprehensive deployment validation checklist for CI/CD pipeline ensuring reliable and consistent deployments

**Scope**: Complete deployment process from pre-deployment validation through post-deployment verification and troubleshooting

**Overview**: Systematic checklist covering all critical deployment phases including code quality validation,
    Docker build preparation, environment setup, infrastructure updates, service deployment, and post-deployment
    validation. Provides specific commands, troubleshooting procedures, and rollback strategies for AWS ECS
    deployments. Includes detailed validation steps for health checks, API endpoints, WebSocket connections,
    and performance verification to ensure successful deployment completion.

**Dependencies**: AWS CLI, Docker, Terraform, Make targets, ECS services, ALB configuration, and CloudWatch logging

**Exports**: Step-by-step deployment procedures, validation commands, troubleshooting guidelines, and rollback procedures

**Related**: CICD_PIPELINE_STEPS.md for detailed implementation, CICD_DEPLOYMENT_LESSONS.md for lessons learned

**Implementation**: Checklist-based validation process with specific commands and success criteria for each deployment phase

---

## Pre-Deployment Validation ✅

### Code Quality
- [ ] All TypeScript compiles without errors
- [ ] All linting passes (ESLint, Ruff, etc.)
- [ ] Unit tests pass including WebSocket service tests
- [ ] Integration tests validate API endpoints
- [ ] No hardcoded backend ports in production builds

### Docker Build Preparation
- [ ] `.dockerignore` updated to exclude cache directories (`.ruff_cache`, `node_modules`)
- [ ] Build context is clean (no permission issues)
- [ ] Docker images build successfully from clean directories
- [ ] Image tags use versioning (avoid overwriting `latest`)

## Deployment Process 🚀

### 1. Environment Setup
- [ ] AWS credentials configured (`AWS_PROFILE=terraform-deploy`)
- [ ] Terraform backend accessible
- [ ] ECR repositories exist and accessible

### 2. Build and Push Images
- [ ] Build frontend image with clean context
- [ ] Build backend image with clean context
- [ ] Tag images with version numbers (e.g., `v4`, `v5`)
- [ ] Push images to ECR successfully
- [ ] Verify images exist in ECR console

### 3. Infrastructure Updates
- [ ] Update `ecs.tf` with new image tags
- [ ] Verify ALB routing includes all required endpoints
- [ ] Check ALB path patterns don't exceed 5 per condition
- [ ] Apply Terraform changes to task definitions and services

### 4. Service Deployment
```bash
# Update ECS services
terraform apply -var="environment=dev" -var="deployment_scope=runtime" \
  -target=aws_ecs_task_definition.frontend \
  -target=aws_ecs_task_definition.backend \
  -target=aws_ecs_service.frontend \
  -target=aws_ecs_service.backend \
  -auto-approve
```

## Post-Deployment Validation ✅

### Health Checks
- [ ] ECS services show running tasks
- [ ] ALB target groups show healthy targets
- [ ] Container health checks pass
- [ ] Service discovery DNS resolves correctly

### API Validation
- [ ] Health endpoint responds: `GET /health`
- [ ] API endpoints accessible: `GET /api/oscilloscope/config`
- [ ] WebSocket connections work (correct URL without port)
- [ ] All application features functional

### Performance Verification
- [ ] Response times within acceptable limits
- [ ] WebSocket connections establish successfully
- [ ] No errors in CloudWatch logs
- [ ] Resource utilization within expected ranges

## Troubleshooting Commands 🔧

```bash
# Check ECS service status
aws ecs describe-services --cluster durableai-dev-cluster --services durable-code-dev-frontend durable-code-dev-backend

# View container logs
aws logs tail /ecs/durable-code-dev/frontend --follow
aws logs tail /ecs/durable-code-dev/backend --follow

# Test ALB endpoints
curl -s "http://durable-code-dev-alb-1541042360.us-west-2.elb.amazonaws.com/health"
curl -s "http://durable-code-dev-alb-1541042360.us-west-2.elb.amazonaws.com/api/oscilloscope/config"

# Check ALB target health
aws elbv2 describe-target-health --target-group-arn arn:aws:elasticloadbalancing:us-west-2:449870229058:targetgroup/durable-code-dev-frontend-tg/85a05d3d7b03cb76
```

## Rollback Procedures 🔄

### If Deployment Fails
1. **Revert Terraform Configuration**
   - Change image tags back to previous working version
   - Apply Terraform changes to roll back

2. **Quick Health Check**
   ```bash
   # Verify rollback succeeded
   curl -s "http://durable-code-dev-alb-1541042360.us-west-2.elb.amazonaws.com/health"
   ```

3. **Investigation**
   - Check CloudWatch logs for errors
   - Verify service discovery configuration
   - Check security group rules
   - Validate WebSocket URL generation

## Common Issues and Solutions 🛠️

### WebSocket Connection Failures
- **Symptom**: Frontend can't connect to WebSocket
- **Check**: WebSocket URL generation (should omit port for ALB)
- **Fix**: Ensure production builds use ALB hostname without `:8000`

### Service Discovery Issues
- **Symptom**: Services can't resolve each other
- **Check**: DNS resolution within containers
- **Fix**: Verify services registered in correct namespace (`dev.local`)

### ALB Routing Problems
- **Symptom**: API endpoints return 404
- **Check**: ALB listener rules include required path patterns
- **Fix**: Add missing patterns, ensure under 5 patterns per condition

### Container Health Check Failures
- **Symptom**: Tasks fail to start or become unhealthy
- **Check**: Health check endpoints and container startup
- **Fix**: Verify health check paths and container port configuration

## Environment-Specific Notes 📋

### Development Environment
- Uses Fargate Spot for cost savings
- Minimal resource allocation
- Relaxed health check intervals
- 7-day log retention

### Production Environment (Future)
- Uses standard Fargate for reliability
- Higher resource allocation
- Strict health check intervals
- 30-day log retention
- Auto-scaling enabled
- SSL/TLS termination

## Success Criteria ✨

Deployment is successful when:
- ✅ All services show healthy in ECS console
- ✅ ALB target groups show healthy targets
- ✅ Frontend loads successfully in browser
- ✅ Oscilloscope WebSocket connects and streams data
- ✅ All API endpoints respond correctly
- ✅ No errors in CloudWatch logs
- ✅ Application performance meets baseline

## Documentation Updates 📝

After successful deployment:
- [ ] Update deployment version in documentation
- [ ] Record any new lessons learned
- [ ] Update troubleshooting guides if needed
- [ ] Document any configuration changes made
