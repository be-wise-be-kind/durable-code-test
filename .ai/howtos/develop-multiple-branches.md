# How to Develop Multiple Branches Simultaneously

**Purpose**: Enable parallel development on multiple git branches without port conflicts
**Scope**: Docker development environment configuration for multi-branch workflows
**Created**: 2025-01-21
**Author**: DevOps Team
**Version**: 1.0

---

## Overview

This guide explains how to run multiple development environments simultaneously for different git branches on the same machine. Each branch automatically gets unique port assignments to prevent conflicts.

## How It Works

### Automatic Port Assignment

When you switch branches and run the development environment, ports are automatically calculated based on the branch name:

- **Main/master/develop branches**: Always use default ports (Frontend: 5173, Backend: 8000)
- **Feature branches**: Get unique ports based on a hash of the branch name
  - Frontend: 5173 + offset (e.g., 5174-6173)
  - Backend: 8000 + offset (e.g., 8001-9000)

The same branch always gets the same ports, making URLs predictable and bookmarkable.

### Port Calculation

The system uses a deterministic hash function on the branch name to calculate port offsets:
1. Branch name is normalized (lowercase, special chars replaced with dashes)
2. Hash is calculated using `cksum` for cross-platform consistency
3. Offset is derived (0-999 range) and added to base ports
4. Main branches always get offset 0 (default ports)

## Quick Start

### 1. Check Your Branch's Ports

```bash
# See ports for current branch
make branch-ports

# See all port assignments
make port-status
```

### 2. Start Development Environment

```bash
# Ports are automatically assigned based on branch
make dev

# Or with browser launch
make launch
```

### 3. Access Your Services

The Makefile will display the correct URLs when starting:
- Frontend URL: `http://localhost:[FRONTEND_PORT]`
- Backend URL: `http://localhost:[BACKEND_PORT]`
- API Docs: `http://localhost:[BACKEND_PORT]/docs`

## Common Workflows

### Running Multiple Branches

```bash
# Terminal 1 - Main branch
git checkout main
make dev
# Running on default ports: 5173, 8000

# Terminal 2 - Feature branch
git checkout feat/new-feature
make dev
# Running on calculated ports: e.g., 5234, 8061

# Check all running environments
make port-status
```

### Switching Between Branches

```bash
# Stop current branch's containers
make dev-stop

# Switch branch
git checkout other-branch

# Start new branch's containers with its ports
make dev
```

### Finding Active Ports

```bash
# Show all active port mappings
make show-ports

# Show detailed container status
make status
```

## Port Management Commands

| Command | Description |
|---------|------------|
| `make port-status` | Show port assignments for all branches |
| `make branch-ports` | Display ports for current branch |
| `make show-ports` | Show all active port mappings |
| `make status` | Show container status with ports |

## Troubleshooting

### Port Already in Use

If you get a port conflict error:

1. Check if another branch is using the port:
   ```bash
   make port-status
   ```

2. Stop conflicting containers:
   ```bash
   make dev-stop
   # Or stop specific branch
   docker stop durable-code-backend-[branch-name]-dev
   docker stop durable-code-frontend-[branch-name]-dev
   ```

3. If a non-Docker process is using the port:
   ```bash
   # Find process using port (Linux/Mac)
   lsof -i :PORT_NUMBER

   # Kill process if needed
   kill -9 PID
   ```

### Finding Your Branch's URLs

After starting the environment, URLs are displayed. You can also retrieve them:

```bash
# Get URLs for current branch
./scripts/get-branch-ports.sh "$(git branch --show-current)" urls
```

### Container Names

Containers are named with the branch included:
- Backend: `durable-code-backend-[branch-name]-dev`
- Frontend: `durable-code-frontend-[branch-name]-dev`

This makes it easy to identify which containers belong to which branch.

## Advanced Usage

### Manual Port Calculation

You can manually check port assignments:

```bash
# Check ports for any branch
./scripts/get-branch-ports.sh "branch-name" plain

# Get JSON output for scripting
./scripts/get-branch-ports.sh "branch-name" json

# Get export statements
./scripts/get-branch-ports.sh "branch-name" export
```

### Environment Variables

The following environment variables are automatically set:
- `FRONTEND_PORT`: Calculated frontend port
- `BACKEND_PORT`: Calculated backend port
- `BRANCH_NAME`: Sanitized branch name

### Custom Port Ranges

To modify port ranges, edit `scripts/get-branch-ports.sh`:
- `FRONTEND_BASE`: Base frontend port (default: 5173)
- `BACKEND_BASE`: Base backend port (default: 8000)
- Offset range: 0-999 (can be adjusted)

## Best Practices

1. **Always check ports before starting**: Run `make port-status` to see what's running
2. **Stop environments when switching**: Use `make dev-stop` before changing branches
3. **Bookmark branch URLs**: Since ports are deterministic, you can bookmark each branch's URLs
4. **Use make commands**: They handle port calculation automatically
5. **Clean up unused containers**: Run `make clean` periodically to remove orphaned containers

## Benefits

- **No manual configuration**: Ports are calculated automatically
- **Predictable URLs**: Same branch always gets same ports
- **Parallel development**: Work on multiple features simultaneously
- **Easy collaboration**: Share branch-specific URLs with teammates
- **Prevents conflicts**: Each branch gets unique ports

## Examples

### Example Port Assignments

| Branch Name | Frontend Port | Backend Port |
|------------|---------------|--------------|
| main | 5173 | 8000 |
| develop | 5173 | 8000 |
| feat/user-auth | 5234 | 8061 |
| fix/api-bug | 5892 | 8719 |
| feature/new-ui | 5456 | 8283 |

### Complete Workflow Example

```bash
# Start working on a feature
git checkout -b feat/awesome-feature
make dev
# Ports assigned: 5234, 8061

# Open browser to frontend
open http://localhost:5234

# In another terminal, work on a bugfix
git checkout -b fix/urgent-bug
make dev
# Ports assigned: 5892, 8719

# Check what's running
make port-status

# Switch back to feature
cd ../project-feat
make dev-stop
git checkout feat/awesome-feature
make dev

# Clean up when done
make clean
```

## Related Documentation

- [Docker Execution Standards](../docs/DOCKER_EXECUTION_STANDARDS.md)
- [Development Setup](./setup-development.md)
- [Running Tests](./run-tests.md)
