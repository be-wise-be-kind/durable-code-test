# Docker Linting Separation - AI Context

**Purpose**: AI agent context document for Docker linting separation project to improve development experience and deployment reliability

**Scope**: Docker container architecture refactoring to separate linting toolchains from development and production containers

**Overview**: Comprehensive context document for AI agents working on Docker linting separation project for the
    Durable Code Test application. Addresses development container inefficiencies by separating linting toolchains
    from runtime containers to improve startup times, reduce container sizes, and optimize CI/CD performance.
    Covers current architecture problems, target solutions, implementation strategy, and performance expectations.
    Includes Docker design patterns, security considerations, rollback strategies, and guidance for AI agents
    on container optimization and workflow preservation.

**Dependencies**: Docker, Docker Compose, linting tools (Black, Ruff, ESLint, etc.), Make targets, GitHub Actions

**Exports**: Container architecture patterns, performance optimization strategies, implementation guidance, and CI/CD integration approaches

**Related**: TESTING_STRATEGY.md for validation procedures, IMPLEMENTATION_BREAKDOWN.md for detailed tasks, PROGRESS_TRACKER.md for status

**Implementation**: Phased container separation with performance optimization, testing validation, and development workflow preservation

---

## Overview
This document provides context for AI agents working on the Docker linting separation project for the Durable Code Test application. The goal is to separate linting toolchains from development containers to improve development experience and deployment reliability.

## Project Background
The Durable Code Test application currently uses monolithic development containers that include both runtime dependencies and comprehensive linting toolchains. This approach has served well for development but creates issues:
- **Slow container startup**: Development containers take 2-3 minutes to start due to linting tool installation
- **Bloated deployment images**: Linting tools increase container size and attack surface
- **Mixed concerns**: Runtime and tooling dependencies are intermingled
- **Resource inefficiency**: Linting tools consume memory even when not in use

## Current Architecture Problems

### Development Containers Include Everything
- **Backend Dev Container** (`durable-code-app/backend/Dockerfile.dev`):
  - Poetry with all dev dependencies (~200MB)
  - System tools: shellcheck, TFLint (~50MB)
  - Playwright browsers and dependencies (~50MB)
  - Total linting overhead: ~300MB

- **Frontend Dev Container** (`durable-code-app/frontend/Dockerfile.dev`):
  - All Node.js dev dependencies including ESLint, Prettier, Stylelint
  - HTMLHint installed globally
  - TypeScript compiler and tooling
  - Total linting overhead: ~150MB

### GitHub Actions Inefficiency
Current CI workflow builds full development containers just to run linting, leading to:
- Slower cache warming (more layers to cache)
- Mixed dependency updates (runtime + linting tools)
- Monolithic failure modes (one tool failure affects entire container)

## Target Architecture

### Dedicated Linting Containers
- **Python Linting Container**: Contains only Python linting tools and their dependencies
- **JavaScript Linting Container**: Contains only Node.js linting tools
- **Source Code Volume Mounting**: Linting containers access source code via volumes
- **Parallel Execution**: Multiple linting containers can run simultaneously

### Clean Development Containers
- **Minimal Backend Dev Container**: Only runtime dependencies and development server
- **Minimal Frontend Dev Container**: Only build tools and development server
- **Faster Startup**: 30-50% reduction in container startup time
- **Smaller Memory Footprint**: Reduced runtime memory consumption

### Optimized CI Pipeline
- **Dedicated Linting Workflow**: Uses specialized linting containers
- **Better Caching**: Linting tools cached separately from application dependencies
- **Parallel Execution**: Different linting tasks can run concurrently
- **Fault Isolation**: Linting failures don't affect other CI steps

## Key Architectural Decisions

### Why Separate Containers Instead of Multi-Stage Builds?
**Decision**: Use dedicated containers rather than multi-stage builds within existing Dockerfiles
**Rationale**:
- **Clear Separation**: Linting and runtime concerns are completely isolated
- **Parallel Development**: Multiple developers can run different linting tasks
- **Tool Updates**: Linting tools can be updated independently of application
- **Resource Control**: Can allocate specific resources to linting tasks
- **Debugging**: Easier to debug linting issues in isolation

### Why Docker Compose for Linting?
**Decision**: Use `docker-compose.lint.yml` to orchestrate linting containers
**Rationale**:
- **Familiar Tool**: Team already uses Docker Compose for development
- **Volume Management**: Simplified source code mounting and sharing
- **Network Isolation**: Can isolate linting containers from application network
- **Service Discovery**: Named containers for easy access from Make targets
- **Resource Limits**: Can set memory and CPU limits per linting container

### Why Preserve Existing Make Targets?
**Decision**: Keep all existing `make lint-*` targets working identically
**Rationale**:
- **Zero Disruption**: Developers continue using familiar commands
- **Backward Compatibility**: Existing documentation and scripts continue working
- **Gradual Migration**: Can migrate to new architecture without workflow changes
- **Rollback Safety**: Easy to revert if issues discovered

## Implementation Strategy

### Phase 1: Create Linting Infrastructure
1. **Design Container Architecture**: Dedicated Dockerfiles for each linting ecosystem
2. **Volume Mapping Strategy**: How linting containers access source code
3. **Networking Design**: Isolation and communication patterns
4. **Resource Allocation**: Memory and CPU limits for linting containers

### Phase 2: Integration Layer
1. **Makefile Updates**: Redirect existing targets to use new containers
2. **Parallel Execution**: Run multiple linting tasks simultaneously
3. **Error Handling**: Proper error propagation from containers to make
4. **Performance Optimization**: Minimize container startup overhead

### Phase 3: CI/CD Migration
1. **GitHub Actions Updates**: Use dedicated linting containers
2. **Caching Strategy**: Optimize Docker layer caching for linting tools
3. **Parallel Workflows**: Run linting in parallel with other CI tasks
4. **Performance Validation**: Ensure CI performance improves

### Phase 4: Cleanup and Documentation
1. **Remove Linting Tools**: Clean up development containers
2. **Update Documentation**: Reflect new architecture in guides
3. **Performance Validation**: Measure and document improvements
4. **Rollback Procedures**: Document how to revert if needed

## Docker Design Patterns

### Linting Container Design
```dockerfile
# Optimized for tool execution, not runtime
FROM python:3.11-slim
WORKDIR /workspace
# Install only linting tools
RUN pip install black ruff mypy pylint
# Source code mounted at runtime
VOLUME ["/workspace/src"]
CMD ["bash"]
```

### Volume Mounting Strategy
```yaml
# docker-compose.lint.yml
services:
  python-linter:
    build: ./docker/linting/python
    volumes:
      - ./durable-code-app/backend:/workspace/backend
      - ./tools:/workspace/tools
      - ./test:/workspace/test
```

### Make Target Integration
```makefile
# Makefile.lint
lint-python: ## Run Python linting in dedicated container
	docker-compose -f docker-compose.lint.yml run --rm python-linter \
		bash -c "cd /workspace && black --check backend tools"
```

## Performance Expectations

### Development Container Improvements
- **Startup Time**: 30-50% reduction (from 2-3 minutes to 1-2 minutes)
- **Memory Usage**: 20-30% reduction in idle memory consumption
- **Storage**: 450MB reduction in container image size

### CI/CD Pipeline Improvements
- **Cache Efficiency**: Better cache hit rates due to layer separation
- **Parallel Execution**: Multiple linting tasks run concurrently
- **Build Time**: 10-20% reduction in total CI time
- **Resource Usage**: More efficient GitHub Actions runner utilization

### Linting Execution
- **Cold Start**: Slightly slower due to container startup (5-10 seconds)
- **Warm Execution**: Similar or better performance
- **Parallel Capacity**: Multiple linting types can run simultaneously
- **Tool Isolation**: Issues with one tool don't affect others

## Security Considerations

### Container Isolation
- **Network Isolation**: Linting containers don't need network access
- **Filesystem Access**: Read-only access to source code
- **User Permissions**: Run containers with non-root user
- **Resource Limits**: Prevent resource exhaustion attacks

### Production Benefits
- **Reduced Attack Surface**: No linting tools in production containers
- **Smaller Images**: Fewer packages to scan for vulnerabilities
- **Clear Boundaries**: Runtime vs. tooling dependencies are explicit
- **Compliance**: Easier to audit production containers

## Rollback Strategy

### If Issues Discovered
1. **Immediate Rollback**: Revert Makefile.lint to use development containers
2. **GitHub Actions Rollback**: Revert CI workflow to original version
3. **Container Cleanup**: Remove dedicated linting containers
4. **Documentation**: Update docs to reflect rollback

### Rollback Triggers
- **Performance Regression**: If linting becomes significantly slower
- **Reliability Issues**: If containers fail to start consistently
- **Developer Workflow Disruption**: If day-to-day development is impacted
- **CI/CD Failures**: If GitHub Actions become unreliable

## Future Considerations

### Potential Enhancements
- **Pre-built Images**: Push linting containers to registry for faster CI
- **Tool Version Management**: Centralized linting tool version control
- **IDE Integration**: Connect IDEs directly to linting containers
- **Monitoring**: Add metrics for linting container performance

### Scaling Considerations
- **Multi-Project**: Reuse linting containers across multiple projects
- **Tool Standardization**: Establish organization-wide linting standards
- **Resource Optimization**: Fine-tune container resource allocation
- **Automation**: Auto-update linting tools based on project dependencies

## Common Tasks for AI Agents

### Adding New Linting Tool
1. Update appropriate linting Dockerfile (python or js)
2. Add tool configuration to project
3. Update Make target to include new tool
4. Test tool works in container environment
5. Update CI workflow if needed

### Updating Tool Versions
1. Update Dockerfile with new tool version
2. Rebuild linting container
3. Test all linting passes with new version
4. Update any tool-specific configuration
5. Document version change

### Troubleshooting Container Issues
1. Check volume mounts are correct
2. Verify container has proper permissions
3. Test tools work inside container manually
4. Check resource limits aren't exceeded
5. Verify network connectivity if needed

## References
- [Docker Multi-Stage Builds](https://docs.docker.com/develop/dev-best-practices/dockerfile_best-practices/)
- [Docker Compose Volume Mounting](https://docs.docker.com/compose/compose-file/compose-file-v3/#volumes)
- [GitHub Actions Docker Caching](https://docs.github.com/en/actions/using-workflows/caching-dependencies-to-speed-up-workflows)
- [Project Layout Rules](.ai/layout.yaml) - For understanding file organization
- [Docker Execution Standards](.ai/docs/DOCKER_EXECUTION_STANDARDS.md) - For container execution patterns

## Notes for AI Agents
- Always test that existing functionality continues to work
- Use consistent container naming conventions
- Follow existing project patterns for Docker configuration
- Document any performance changes (positive or negative)
- Keep security considerations in mind when designing containers
- Ensure all Make targets continue to work exactly as before
- Test both development and CI environments thoroughly
