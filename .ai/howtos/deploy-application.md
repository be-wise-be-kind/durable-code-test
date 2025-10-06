# How to Deploy Application

**Purpose**: Comprehensive guide for deploying the application to production environments

**Scope**: Production deployment, environment configuration, monitoring, verification procedures

**Overview**: Step-by-step deployment guide covering production image building, environment setup,
    service orchestration, and verification procedures. Includes deployment best practices,
    monitoring configuration, rollback procedures, and troubleshooting approaches for reliable
    production deployments across different environments and infrastructure configurations.

**Dependencies**: Docker containers, production environment, monitoring tools, deployment automation

**Exports**: Deployment workflows, production configuration, monitoring procedures, verification steps

**Related**: Infrastructure management, production monitoring, environment configuration

**Implementation**: Make-based deployment automation, Docker orchestration, production monitoring

---

## Quick Deployment

### AWS ECS Deployment (Current Production Setup)

```bash
# 1. Ensure infrastructure is deployed first
make infra-up SCOPE=all ENV=dev AUTO=true

# 2. Deploy application containers to ECS
make deploy

# 3. Verify deployment
make deploy-check

# 4. Access application
# Via ALB DNS: http://durableai-dev-alb-<id>.us-west-2.elb.amazonaws.com
# Via Custom Domain: https://dev.durableaicoding.net
```

**What `make deploy` does**:
1. Builds Docker images for frontend (port 3000) and backend (port 8000)
2. Authenticates with AWS ECR registry
3. Tags and pushes images to ECR with timestamp tags
4. Fetches current ECS task definitions
5. Updates task definitions with new image tags
6. Triggers ECS service updates with new task definitions
7. ECS performs rolling deployment with zero downtime

### Local Development Deployment

```bash
# Build development images
make build

# Start local environment
make start

# Verify deployment
make status
curl http://localhost:8000/health
```

## Production Build Process

### Build Production Images
```bash
make build
```
**What it does**:
1. Builds optimized Docker images for all services
2. Uses multi-stage builds for minimal image size
3. Applies production optimizations
4. Validates build success

### Build Verification
```bash
# Check built images
docker images | grep durable-code-test

# Verify image sizes
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"

# Test image functionality
docker run --rm durable-code-test-frontend:latest npm run build
```

## Production Environment

### Start Production Services
```bash
make start
```
**Services Started**:
- **Frontend**: Optimized React build on `http://localhost:3000`
- **Backend**: FastAPI server on `http://localhost:8000`
- **Database**: PostgreSQL (if configured)
- **Reverse Proxy**: Nginx (if configured)

### Production Configuration
**File**: `.docker/compose/prod.yml`
**Features**:
- Production-optimized builds
- Security hardening
- Resource limits
- Health checks
- Restart policies

### Environment Variables
**Production `.env`**:
```env
# Production settings
NODE_ENV=production
DEBUG=false
LOG_LEVEL=info

# Security settings
SECRET_KEY=your-production-secret
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database
DATABASE_URL=postgresql://user:pass@db:5432/durable_code_prod

# External services
REDIS_URL=redis://redis:6379/0
```

## Deployment Strategies

### Docker Compose Deployment
```bash
# Pull latest images
docker-compose pull

# Deploy with zero downtime
docker-compose up -d --no-deps --build frontend
docker-compose up -d --no-deps --build backend

# Verify deployment
docker-compose ps
```

### Production Checklist
- [ ] Environment variables configured
- [ ] SSL certificates installed
- [ ] Database migrations applied
- [ ] Static files served correctly
- [ ] Health checks passing
- [ ] Monitoring configured
- [ ] Backup strategy implemented

## Cloud Deployment

### AWS ECS Deployment (Current Setup)

**Architecture**:
- **Infrastructure**: Managed by Terraform in 3 workspaces (bootstrap, base, runtime)
- **Container Registry**: AWS ECR for Docker images
- **Compute**: ECS Fargate for serverless containers
- **Load Balancer**: Application Load Balancer with path-based routing
- **DNS**: Route53 with ACM SSL certificates
- **Networking**: VPC with public/private subnets, NAT gateways

**Port Configuration**:
- Frontend container: Port 3000
- Backend container: Port 8000
- ALB routes `/api/*` → Backend (8000)
- ALB routes `/*` → Frontend (3000)

**Deployment Script** (`infra/scripts/deploy-app.sh`):
```bash
# The script handles:
# 1. ECR authentication
# 2. Docker image building (frontend & backend)
# 3. Image tagging with timestamp (v20231204-143022)
# 4. Pushing to ECR repositories
# 5. Updating ECS task definitions
# 6. Triggering service updates

# Manual deployment
ENV=dev ./infra/scripts/deploy-app.sh

# Or use make target
make deploy
```

**Resource Naming Convention**:
- Cluster: `durableai-${ENV}-cluster`
- Services: `durableai-${ENV}-frontend`, `durableai-${ENV}-backend`
- ECR Repos: `durableai-${ENV}-frontend`, `durableai-${ENV}-backend`
- ALB: `durableai-${ENV}-alb`
- Target Groups: `durableai-${ENV}-frontend-tg`, `durableai-${ENV}-backend-tg`

**Environment Variables** (Injected by Terraform):
- Frontend: `ENVIRONMENT`, `BACKEND_URL=http://${alb_dns}/api`
- Backend: `ENVIRONMENT`, `PORT=8000`

**Health Checks**:
- Frontend: `GET /` (port 3000) - 200-299 response
- Backend: `GET /health` (port 8000) - 200-299 response
- ALB performs continuous health monitoring

**State Management**:
- Bootstrap state: `s3://durable-code-terraform-state/bootstrap/dev/terraform.tfstate`
- Base state: `s3://durable-code-terraform-state/base/dev/terraform.tfstate`
- Runtime state: `s3://durable-code-terraform-state/runtime/dev/terraform.tfstate`
- Runtime uses `terraform_remote_state` to reference base outputs (VPC, subnets, security groups)

**Service Discovery**:
Frontend doesn't use AWS Service Discovery - it communicates with backend via the ALB DNS name passed as `BACKEND_URL` environment variable. This ensures:
- No internal DNS dependencies
- Works with ALB path-based routing
- Simplified networking (no service mesh needed)

**Troubleshooting Deployment**:
```bash
# Check ECS service status
aws ecs describe-services --cluster durableai-dev-cluster --services durableai-dev-frontend durableai-dev-backend

# View task logs
aws logs tail /ecs/durableai-dev-frontend --follow
aws logs tail /ecs/durableai-dev-backend --follow

# Check target group health
aws elbv2 describe-target-health --target-group-arn <tg-arn>

# Force new deployment (if stuck)
aws ecs update-service --cluster durableai-dev-cluster --service durableai-dev-frontend --force-new-deployment
```

### Google Cloud Platform
**Cloud Run Deployment**:
```bash
# Build and push to GCR
gcloud builds submit --tag gcr.io/PROJECT-ID/durable-code-test-frontend
gcloud builds submit --tag gcr.io/PROJECT-ID/durable-code-test-backend

# Deploy to Cloud Run
gcloud run deploy frontend --image gcr.io/PROJECT-ID/durable-code-test-frontend --platform managed
gcloud run deploy backend --image gcr.io/PROJECT-ID/durable-code-test-backend --platform managed
```

### Azure Deployment
**Container Instances**:
```bash
# Create resource group
az group create --name durable-code-test --location eastus

# Deploy container group
az container create --resource-group durable-code-test --file .docker/compose/prod.yml
```

## Database Deployment

### Production Database Setup
```bash
# Run database migrations
docker exec -it durable-code-test-backend-1 alembic upgrade head

# Create database backup
docker exec -it durable-code-test-db-1 pg_dump -U postgres durable_code > backup.sql

# Restore database
docker exec -i durable-code-test-db-1 psql -U postgres durable_code < backup.sql
```

### Database Configuration
**Production Settings**:
```yaml
# .docker/compose/prod.yml
services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: durable_code_prod
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
```

## SSL/TLS Configuration

### Nginx Reverse Proxy
**Configuration**: `nginx.conf`
```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/ssl/certs/yourdomain.com.crt;
    ssl_certificate_key /etc/ssl/private/yourdomain.com.key;

    location / {
        proxy_pass http://frontend:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Let's Encrypt SSL
```bash
# Install Certbot
apt-get install certbot

# Generate certificate
certbot certonly --webroot -w /var/www/html -d yourdomain.com

# Auto-renewal
crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## Monitoring and Logging

### Health Monitoring
```bash
# Application health checks
curl http://localhost:8000/health
curl http://localhost:3000/health

# Container health
docker ps --format "table {{.Names}}\t{{.Status}}"

# Resource usage
docker stats --no-stream
```

### Log Management
```bash
# View application logs
docker-compose logs -f frontend
docker-compose logs -f backend

# Log rotation
docker-compose logs --tail=100 frontend

# Export logs
docker-compose logs frontend > frontend.log
```

### Monitoring Stack
**Prometheus + Grafana**:
```yaml
# docker-compose.monitoring.yml
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    ports:
      - "3001:3000"
```

## Performance Optimization

### Production Optimizations
**Frontend**:
- Code splitting and lazy loading
- Asset compression (gzip/brotli)
- CDN integration
- Bundle size optimization

**Backend**:
- Database connection pooling
- Caching (Redis)
- Request rate limiting
- Response compression

### Caching Strategy
```yaml
# Redis cache
services:
  redis:
    image: redis:7-alpine
    restart: unless-stopped
    command: redis-server --appendonly yes
```

### Load Balancing
**Nginx Load Balancer**:
```nginx
upstream backend {
    server backend1:8000;
    server backend2:8000;
    server backend3:8000;
}

upstream frontend {
    server frontend1:3000;
    server frontend2:3000;
}
```

## Security Hardening

### Production Security
**Environment**:
```env
# Security settings
SECRET_KEY=strong-random-secret-key
ALLOWED_HOSTS=yourdomain.com
CORS_ALLOWED_ORIGINS=https://yourdomain.com

# Database security
DB_PASSWORD=strong-database-password
DB_SSL_MODE=require
```

**Docker Security**:
```yaml
# .docker/compose/prod.yml
services:
  frontend:
    security_opt:
      - no-new-privileges:true
    read_only: true
    user: "1000:1000"
```

### Firewall Configuration
```bash
# UFW firewall rules
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw deny 8000/tcp   # Block direct backend access
ufw enable
```

## Backup and Recovery

### Database Backup
```bash
# Automated backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker exec durable-code-test-db-1 pg_dump -U postgres durable_code > backup_$DATE.sql
aws s3 cp backup_$DATE.sql s3://your-backup-bucket/
```

### Application Backup
```bash
# Backup configuration
tar -czf config_backup.tar.gz .env .docker/compose/prod.yml nginx.conf

# Backup user uploads
docker cp durable-code-test-backend-1:/app/uploads ./uploads_backup
```

### Disaster Recovery
```bash
# Restore from backup
docker exec -i durable-code-test-db-1 psql -U postgres -d durable_code < backup.sql

# Rebuild and redeploy
make clean
make build
make start
```

## CI/CD Integration

### GitHub Actions Deployment
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to production
        run: |
          make build
          make start
```

### Automated Deployment
```bash
# Deploy script
#!/bin/bash
set -e

echo "Starting deployment..."
git pull origin main
make build
make start
make status

echo "Deployment complete!"
```

## Troubleshooting

### Common Deployment Issues

**Port Conflicts**:
```bash
# Check port usage
netstat -tulpn | grep :8000

# Kill conflicting processes
sudo fuser -k 8000/tcp
```

**Image Build Failures**:
```bash
# Clean Docker cache
docker system prune -a

# Check disk space
df -h

# Increase Docker memory limit
```

**Database Connection Issues**:
```bash
# Check database status
docker exec -it durable-code-test-db-1 pg_isready

# Test connection
docker exec -it durable-code-test-backend-1 python -c "import psycopg2; print('DB OK')"
```

### Performance Issues
```bash
# Monitor resource usage
htop
docker stats

# Check application logs
docker-compose logs --tail=50 backend | grep ERROR

# Database performance
docker exec -it durable-code-test-db-1 psql -U postgres -c "SELECT * FROM pg_stat_activity;"
```

## Rollback Strategy

### Quick Rollback
```bash
# Stop current deployment
make stop

# Rollback to previous images
docker tag durable-code-test-frontend:previous durable-code-test-frontend:latest
docker tag durable-code-test-backend:previous durable-code-test-backend:latest

# Start with previous version
make start
```

### Database Rollback
```bash
# Restore database from backup
docker exec -i durable-code-test-db-1 psql -U postgres -d durable_code < backup_previous.sql

# Run migration rollback if needed
docker exec -it durable-code-test-backend-1 alembic downgrade -1
```
