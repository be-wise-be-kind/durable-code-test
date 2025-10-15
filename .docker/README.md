# Docker Configuration Organization

## Overview
This directory contains all Docker-related configuration files for the durable-code-test project, organized by purpose and environment for improved maintainability and discoverability.

## Benefits of This Organization
- **Improved Discoverability**: All Docker files in logical, predictable locations
- **Reduced Clutter**: Cleaner project root directory
- **Better Maintenance**: Easier to find and update Docker configurations
- **Standard Practices**: Follows industry conventions for Docker project organization
- **Clear Separation**: Development, production, and tooling configurations clearly separated

## Directory Structure

### `compose/`
Docker Compose orchestration files:
- `app.yml` - Complete development environment with hot reloading
- `test.yml` - Testing environment with test containers

### `dockerfiles/`
Container definitions organized by component:

#### `backend/`
- `Dockerfile.dev` - Backend development container with debugging tools
- `Dockerfile.prod` - Optimized backend container for production deployment

#### `frontend/`
- `Dockerfile.dev` - Frontend development container with hot reloading
- `Dockerfile.prod` - Optimized frontend container with static file serving

#### `testing/`
- `Dockerfile.playwright` - End-to-end testing with Playwright browser automation

#### `deployment/`
- `Dockerfile.simple-backend` - Simplified backend container for specific deployment scenarios

## Usage Examples

### Development Environment
```bash
# Start complete development environment
make dev

# Start specific services
docker-compose -f .docker/compose/dev.yml up backend-dev frontend-dev

# Stop development environment
make dev-stop
```

### Linting and Code Quality
```bash
# Run all linting checks (uses poetry and npm, not Docker)
just lint

# Run specific linting
just lint python
just lint frontend
```

### Production Builds
```bash
# Build production containers
docker-compose -f .docker/compose/prod.yml build

# Deploy to production
make deploy  # Uses production containers
```

## Migration History
This organization was implemented through a systematic migration:
1. ✅ Directory structure created
2. ✅ Dockerfiles moved to organized subdirectories
3. ✅ Compose files moved and renamed descriptively
4. ✅ All references updated throughout codebase
5. ✅ Documentation completed and validated

## Troubleshooting

### Common Issues
**Issue**: Docker build fails with "Dockerfile not found"
**Solution**: Ensure you're using the correct path: `.docker/dockerfiles/[component]/Dockerfile.[env]`

**Issue**: Compose file can't find Dockerfile
**Solution**: Check that dockerfile paths in compose files are relative to compose file location

**Issue**: Make targets not working
**Solution**: Verify Makefile has been updated to use new Docker file paths

### Getting Help
- Check this README for path examples
- Verify file exists: `ls -la .docker/dockerfiles/[component]/`
- Test Docker build manually: `docker build -f .docker/dockerfiles/[component]/Dockerfile.[env] .`