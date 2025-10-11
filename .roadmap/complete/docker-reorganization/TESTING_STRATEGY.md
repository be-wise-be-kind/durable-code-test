# Docker Directory Reorganization - Testing Strategy

**Purpose**: Comprehensive testing and validation strategy for Docker directory reorganization

**Scope**: All Docker operations, development workflows, CI/CD pipelines, and production deployment processes

**Overview**: Detailed testing strategy for validating the Docker directory reorganization across all phases of
    implementation. Ensures zero regression in functionality while achieving improved organization and maintainability.
    Covers unit testing of individual Docker operations, integration testing of complete workflows, and comprehensive
    validation of development, staging, and production environments.

**Dependencies**: Docker reorganization implementation, existing test infrastructure, CI/CD pipelines, development and deployment workflows

**Exports**: Testing procedures, validation checklists, automated test scripts, and success criteria for each reorganization phase

**Related**: PROGRESS_TRACKER.md for implementation status, PR_BREAKDOWN.md for detailed tasks, AI_CONTEXT.md for reorganization context

**Implementation**: Phase-based validation with automated testing, manual verification procedures, and comprehensive documentation

---

## Testing Overview

The Docker directory reorganization requires comprehensive testing to ensure:
- **Zero Functional Regression**: All existing Docker operations continue to work identically
- **Workflow Preservation**: Developer and deployment workflows remain unchanged
- **Performance Maintenance**: No negative impact on build times or startup performance
- **Documentation Accuracy**: All documentation reflects the new organization correctly

## Testing Phases

### Phase 1: Foundation Testing (PR1)
**Goal**: Validate directory structure creation without disruption

**Automated Tests**:
```bash
#!/bin/bash
# test-phase1.sh - Foundation Testing

echo "🧪 Phase 1: Foundation Testing"

# Test 1: Verify directory structure created
echo "Testing directory structure..."
test -d .docker && echo "✅ .docker directory exists" || echo "❌ .docker directory missing"
test -d .docker/compose && echo "✅ compose directory exists" || echo "❌ compose directory missing"
test -d .docker/dockerfiles && echo "✅ dockerfiles directory exists" || echo "❌ dockerfiles directory missing"
test -d .docker/dockerfiles/backend && echo "✅ backend subdirectory exists" || echo "❌ backend subdirectory missing"
test -d .docker/dockerfiles/frontend && echo "✅ frontend subdirectory exists" || echo "❌ frontend subdirectory missing"
test -d .docker/dockerfiles/linting && echo "✅ linting subdirectory exists" || echo "❌ linting subdirectory missing"

# Test 2: Verify no conflicts with existing files
echo "Testing for conflicts..."
! test -f .docker/README.md || echo "✅ No README conflict"

# Test 3: Verify existing Docker operations unaffected
echo "Testing existing operations..."
make dev >/dev/null 2>&1 && echo "✅ make dev works" || echo "❌ make dev failed"
make dev-stop >/dev/null 2>&1 && echo "✅ make dev-stop works" || echo "❌ make dev-stop failed"
make lint-all >/dev/null 2>&1 && echo "✅ make lint-all works" || echo "❌ make lint-all failed"

echo "Phase 1 testing complete"
```

**Manual Verification**:
- [ ] Directory structure matches documented plan
- [ ] README.md accurately describes organization
- [ ] No interference with current development workflow
- [ ] Documentation is clear and helpful

### Phase 2: File Migration Testing (PR2)
**Goal**: Validate Dockerfile moves with backward compatibility

**Automated Tests**:
```bash
#!/bin/bash
# test-phase2.sh - Dockerfile Migration Testing

echo "🧪 Phase 2: Dockerfile Migration Testing"

# Test 1: Verify files moved correctly
echo "Testing file migrations..."
test -f .docker/dockerfiles/backend/Dockerfile.prod && echo "✅ Backend prod Dockerfile moved" || echo "❌ Backend prod Dockerfile missing"
test -f .docker/dockerfiles/backend/Dockerfile.dev && echo "✅ Backend dev Dockerfile moved" || echo "❌ Backend dev Dockerfile missing"
test -f .docker/dockerfiles/frontend/Dockerfile.prod && echo "✅ Frontend prod Dockerfile moved" || echo "❌ Frontend prod Dockerfile missing"
test -f .docker/dockerfiles/frontend/Dockerfile.dev && echo "✅ Frontend dev Dockerfile moved" || echo "❌ Frontend dev Dockerfile missing"

# Test 2: Verify symbolic links work
echo "Testing symbolic links..."
test -L durable-code-app/backend/Dockerfile && echo "✅ Backend symbolic link exists" || echo "❌ Backend symbolic link missing"
test -L durable-code-app/frontend/Dockerfile && echo "✅ Frontend symbolic link exists" || echo "❌ Frontend symbolic link missing"

# Test 3: Test Docker builds from new locations
echo "Testing Docker builds..."
docker build -f .docker/dockerfiles/backend/Dockerfile.dev durable-code-app/backend/ >/dev/null 2>&1 && echo "✅ Backend dev build works" || echo "❌ Backend dev build failed"
docker build -f .docker/dockerfiles/frontend/Dockerfile.dev durable-code-app/frontend/ >/dev/null 2>&1 && echo "✅ Frontend dev build works" || echo "❌ Frontend dev build failed"

# Test 4: Test Docker builds from old locations (via symlinks)
echo "Testing backward compatibility..."
docker build -f durable-code-app/backend/Dockerfile.dev durable-code-app/backend/ >/dev/null 2>&1 && echo "✅ Backend symlink build works" || echo "❌ Backend symlink build failed"

# Test 5: Test existing workflows
echo "Testing existing workflows..."
make dev >/dev/null 2>&1 && echo "✅ make dev works" || echo "❌ make dev failed"
make dev-stop >/dev/null 2>&1
make lint-all >/dev/null 2>&1 && echo "✅ make lint-all works" || echo "❌ make lint-all failed"

echo "Phase 2 testing complete"
```

**Manual Verification**:
- [ ] All Dockerfiles accessible from new locations
- [ ] Symbolic links function correctly
- [ ] Docker builds succeed from both old and new paths
- [ ] No changes to build context or internal paths needed
- [ ] Development environment starts and functions normally

### Phase 3: Compose Migration Testing (PR3)
**Goal**: Validate compose file moves and path updates

**Automated Tests**:
```bash
#!/bin/bash
# test-phase3.sh - Compose Migration Testing

echo "🧪 Phase 3: Compose Migration Testing"

# Test 1: Verify compose files moved
echo "Testing compose file migrations..."
test -f .docker/compose/dev.yml && echo "✅ dev.yml exists" || echo "❌ dev.yml missing"
test -f .docker/compose/prod.yml && echo "✅ prod.yml exists" || echo "❌ prod.yml missing"
test -f .docker/compose/lint.yml && echo "✅ lint.yml exists" || echo "❌ lint.yml missing"

# Test 2: Verify symbolic links for backward compatibility
echo "Testing compose symbolic links..."
test -L docker-compose.dev.yml && echo "✅ dev symlink exists" || echo "❌ dev symlink missing"
test -L docker-compose.yml && echo "✅ prod symlink exists" || echo "❌ prod symlink missing"
test -L docker-compose.lint.yml && echo "✅ lint symlink exists" || echo "❌ lint symlink missing"

# Test 3: Test compose operations from new locations
echo "Testing compose operations..."
docker-compose -f .docker/compose/dev.yml config >/dev/null 2>&1 && echo "✅ dev.yml config valid" || echo "❌ dev.yml config invalid"
docker-compose -f .docker/compose/lint.yml config >/dev/null 2>&1 && echo "✅ lint.yml config valid" || echo "❌ lint.yml config invalid"

# Test 4: Test compose builds
echo "Testing compose builds..."
docker-compose -f .docker/compose/dev.yml build >/dev/null 2>&1 && echo "✅ dev.yml build works" || echo "❌ dev.yml build failed"
docker-compose -f .docker/compose/lint.yml build >/dev/null 2>&1 && echo "✅ lint.yml build works" || echo "❌ lint.yml build failed"

# Test 5: Test full environment startup
echo "Testing environment startup..."
docker-compose -f .docker/compose/dev.yml up -d >/dev/null 2>&1
sleep 10
curl -f http://localhost:3000 >/dev/null 2>&1 && echo "✅ Frontend accessible" || echo "❌ Frontend not accessible"
curl -f http://localhost:8000/health >/dev/null 2>&1 && echo "✅ Backend accessible" || echo "❌ Backend not accessible"
docker-compose -f .docker/compose/dev.yml down >/dev/null 2>&1

# Test 6: Test linting environment
echo "Testing linting environment..."
docker-compose -f .docker/compose/lint.yml up -d >/dev/null 2>&1
docker-compose -f .docker/compose/lint.yml ps | grep -q "Up" && echo "✅ Linting containers up" || echo "❌ Linting containers failed"
docker-compose -f .docker/compose/lint.yml down >/dev/null 2>&1

echo "Phase 3 testing complete"
```

**Manual Verification**:
- [ ] All compose files in correct locations with proper names
- [ ] Dockerfile references updated correctly in compose files
- [ ] All services start and communicate properly
- [ ] Environment variables and volumes work correctly
- [ ] Symbolic links provide seamless backward compatibility

### Phase 4: Reference Update Testing (PR4)
**Goal**: Validate all code references use new paths

**Automated Tests**:
```bash
#!/bin/bash
# test-phase4.sh - Reference Update Testing

echo "🧪 Phase 4: Reference Update Testing"

# Test 1: Verify no old references remain
echo "Checking for old references..."
old_refs=$(grep -r "docker-compose\.yml" --exclude-dir=node_modules --exclude-dir=.git . | grep -v ".docker/compose" | wc -l)
test $old_refs -eq 0 && echo "✅ No old compose references" || echo "❌ Found $old_refs old compose references"

dockerfile_refs=$(grep -r "durable-code-app.*Dockerfile" --exclude-dir=node_modules --exclude-dir=.git . | grep -v ".docker" | wc -l)
test $dockerfile_refs -eq 0 && echo "✅ No old Dockerfile references" || echo "❌ Found $dockerfile_refs old Dockerfile references"

# Test 2: Verify Makefile targets work
echo "Testing Makefile targets..."
make dev >/dev/null 2>&1 && echo "✅ make dev works" || echo "❌ make dev failed"
make dev-stop >/dev/null 2>&1
make lint-all >/dev/null 2>&1 && echo "✅ make lint-all works" || echo "❌ make lint-all failed"
make test >/dev/null 2>&1 && echo "✅ make test works" || echo "❌ make test failed"

# Test 3: Verify no symbolic links remain
echo "Checking for symbolic links..."
symlinks=$(find . -type l 2>/dev/null | wc -l)
test $symlinks -eq 0 && echo "✅ No symbolic links remain" || echo "❌ Found $symlinks symbolic links"

# Test 4: Test CI/CD pipeline locally (if possible)
echo "Testing CI/CD pipeline..."
if command -v act >/dev/null 2>&1; then
    act -j lint >/dev/null 2>&1 && echo "✅ CI lint job works" || echo "❌ CI lint job failed"
else
    echo "⚠️ act not available, skipping local CI test"
fi

echo "Phase 4 testing complete"
```

**Manual Verification**:
- [ ] All Makefile targets use new Docker file paths
- [ ] CI/CD workflows reference new paths correctly
- [ ] Deployment scripts updated properly
- [ ] Documentation references new paths
- [ ] No broken symbolic links exist
- [ ] All Docker operations function identically to before

### Phase 5: Final Validation Testing (PR5)
**Goal**: Comprehensive end-to-end validation

**Automated Tests**:
```bash
#!/bin/bash
# test-phase5.sh - Final Validation Testing

echo "🧪 Phase 5: Final Validation Testing"

# Test 1: Complete development workflow
echo "Testing complete development workflow..."
make dev >/dev/null 2>&1 && echo "✅ Development environment starts" || echo "❌ Development environment failed"
sleep 15

# Check services are healthy
curl -f http://localhost:3000 >/dev/null 2>&1 && echo "✅ Frontend healthy" || echo "❌ Frontend unhealthy"
curl -f http://localhost:8000/health >/dev/null 2>&1 && echo "✅ Backend healthy" || echo "❌ Backend unhealthy"

# Test hot reloading (simulate file change)
echo "Testing hot reloading..."
touch durable-code-app/frontend/src/App.tsx
sleep 5
curl -f http://localhost:3000 >/dev/null 2>&1 && echo "✅ Hot reload works" || echo "❌ Hot reload failed"

make dev-stop >/dev/null 2>&1

# Test 2: Complete linting workflow
echo "Testing complete linting workflow..."
make lint-all >/dev/null 2>&1 && echo "✅ All linting passes" || echo "❌ Linting failed"

# Test 3: Production build workflow
echo "Testing production build workflow..."
docker-compose -f .docker/compose/prod.yml build >/dev/null 2>&1 && echo "✅ Production build works" || echo "❌ Production build failed"

# Test 4: Testing workflow
echo "Testing testing workflow..."
make test >/dev/null 2>&1 && echo "✅ Test suite passes" || echo "❌ Tests failed"

# Test 5: Documentation accuracy
echo "Testing documentation..."
test -f .docker/README.md && echo "✅ Docker README exists" || echo "❌ Docker README missing"
grep -q "compose/" .docker/README.md && echo "✅ README mentions compose" || echo "❌ README missing compose info"
grep -q "dockerfiles/" .docker/README.md && echo "✅ README mentions dockerfiles" || echo "❌ README missing dockerfiles info"

# Test 6: File organization validation
echo "Validating file organization..."
docker_files_in_root=$(find . -maxdepth 1 -name "docker-compose*.yml" -o -name "Dockerfile*" | wc -l)
test $docker_files_in_root -eq 0 && echo "✅ No Docker files in root" || echo "❌ Found $docker_files_in_root Docker files in root"

docker_files_organized=$(find .docker -name "*.yml" -o -name "Dockerfile*" | wc -l)
test $docker_files_organized -gt 0 && echo "✅ Docker files organized ($docker_files_organized files)" || echo "❌ No Docker files in .docker/"

echo "Phase 5 testing complete"
```

**Performance Testing**:
```bash
#!/bin/bash
# performance-test.sh - Performance Validation

echo "🚀 Performance Testing"

# Measure development environment startup time
echo "Measuring development startup time..."
start_time=$(date +%s)
make dev >/dev/null 2>&1
end_time=$(date +%s)
startup_time=$((end_time - start_time))
echo "Development startup time: ${startup_time}s"

# Wait for services to be ready
sleep 15

# Test response times
echo "Testing response times..."
frontend_time=$(curl -o /dev/null -s -w '%{time_total}' http://localhost:3000)
backend_time=$(curl -o /dev/null -s -w '%{time_total}' http://localhost:8000/health)
echo "Frontend response time: ${frontend_time}s"
echo "Backend response time: ${backend_time}s"

make dev-stop >/dev/null 2>&1

# Measure linting execution time
echo "Measuring linting execution time..."
start_time=$(date +%s)
make lint-all >/dev/null 2>&1
end_time=$(date +%s)
lint_time=$((end_time - start_time))
echo "Linting execution time: ${lint_time}s"

echo "Performance testing complete"
```

## Integration Testing Strategy

### End-to-End Workflow Testing
```bash
#!/bin/bash
# integration-test.sh - Complete Integration Testing

echo "🔄 Integration Testing"

# Test complete developer workflow
echo "Testing developer workflow..."

# 1. Start development environment
make dev
sleep 15

# 2. Verify all services running
docker-compose -f .docker/compose/dev.yml ps

# 3. Test application functionality
curl -f http://localhost:3000 && echo "✅ Frontend accessible"
curl -f http://localhost:8000/health && echo "✅ Backend healthy"

# 4. Test linting integration
make lint-all && echo "✅ Linting passes"

# 5. Test with code changes
echo "// Test comment" >> durable-code-app/frontend/src/App.tsx
sleep 5
curl -f http://localhost:3000 && echo "✅ Hot reload works"

# 6. Clean shutdown
make dev-stop

# Test production deployment workflow
echo "Testing production workflow..."

# 1. Build production images
docker-compose -f .docker/compose/prod.yml build

# 2. Test production startup
docker-compose -f .docker/compose/prod.yml up -d
sleep 10

# 3. Verify production services
curl -f http://localhost:80 && echo "✅ Production frontend works"
curl -f http://localhost:8000/health && echo "✅ Production backend works"

# 4. Clean shutdown
docker-compose -f .docker/compose/prod.yml down

echo "Integration testing complete"
```

### CI/CD Pipeline Testing

**GitHub Actions Validation**:
```yaml
# .github/workflows/test-docker-reorganization.yml
name: Test Docker Reorganization

on:
  pull_request:
    paths:
      - '.docker/**'
      - 'Makefile*'
      - 'docker-compose*.yml'

jobs:
  test-reorganization:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Test Development Environment
        run: |
          make dev
          sleep 15
          curl -f http://localhost:3000
          curl -f http://localhost:8000/health
          make dev-stop

      - name: Test Linting
        run: make lint-all

      - name: Test Production Builds
        run: docker-compose -f .docker/compose/prod.yml build

      - name: Validate File Organization
        run: |
          # Should find no Docker files in root
          [ $(find . -maxdepth 1 -name "docker-compose*.yml" -o -name "Dockerfile*" | wc -l) -eq 0 ]
          # Should find Docker files in .docker/
          [ $(find .docker -name "*.yml" -o -name "Dockerfile*" | wc -l) -gt 0 ]
```

## Test Data and Scenarios

### Test Scenarios by User Type

#### Developer Scenarios
1. **New Developer Onboarding**:
   - Clone repository
   - Run `make dev`
   - Verify all services start
   - Make code changes
   - Verify hot reloading works

2. **Daily Development Workflow**:
   - Start development environment
   - Run linting checks
   - Execute tests
   - Stop environment cleanly

3. **Debugging Container Issues**:
   - Access container logs
   - Execute commands in containers
   - Inspect container configuration

#### DevOps Scenarios
1. **Deployment Pipeline**:
   - Build production images
   - Deploy to staging environment
   - Run integration tests
   - Deploy to production

2. **Infrastructure Updates**:
   - Update Docker configurations
   - Rebuild containers
   - Validate no downtime

#### Maintenance Scenarios
1. **Docker File Updates**:
   - Modify Dockerfile
   - Test builds work correctly
   - Verify no regressions

2. **Dependency Updates**:
   - Update base images
   - Update package dependencies
   - Validate functionality preserved

## Success Criteria

### Functional Success
- ✅ All existing Docker operations work identically
- ✅ Development workflow unchanged for developers
- ✅ CI/CD pipelines pass without modification
- ✅ Production deployment process unchanged
- ✅ All make targets function correctly

### Organizational Success
- ✅ All Docker files in `.docker/` directory
- ✅ Clear, logical file organization
- ✅ Zero Docker files in project root
- ✅ Descriptive compose file names
- ✅ Proper subdirectory organization

### Documentation Success
- ✅ Comprehensive `.docker/README.md`
- ✅ Updated development setup guides
- ✅ Accurate file path references
- ✅ Troubleshooting information available
- ✅ Clear usage examples

### Performance Success
- ✅ No regression in startup times
- ✅ No regression in build times
- ✅ No regression in response times
- ✅ Efficient Docker layer caching maintained

## Risk Mitigation Testing

### Rollback Testing
```bash
#!/bin/bash
# rollback-test.sh - Test rollback procedures

echo "🔄 Testing rollback procedures"

# Simulate rollback scenario
git stash push -m "Test rollback"

# Test that old structure still works if restored
git checkout HEAD~1  # Go back one commit
make dev && echo "✅ Rollback scenario works" || echo "❌ Rollback scenario failed"
make dev-stop

# Return to current state
git checkout -
git stash pop

echo "Rollback testing complete"
```

### Failure Recovery Testing
- Test Docker daemon failures
- Test network connectivity issues
- Test storage/volume mount problems
- Test container resource constraints

## Monitoring and Alerting

### Key Metrics to Monitor
- **Development Environment Startup Time**: Should remain consistent
- **Docker Build Duration**: Should not increase significantly
- **CI/CD Pipeline Duration**: Should maintain current performance
- **Container Resource Usage**: Should remain within acceptable bounds

### Alerting Scenarios
- Failed Docker builds
- Development environment startup failures
- CI/CD pipeline regressions
- Unexpected file path errors

## Documentation Testing

### Documentation Validation Checklist
- [ ] All file paths in documentation are correct
- [ ] All example commands work as documented
- [ ] Troubleshooting steps resolve common issues
- [ ] Setup instructions are complete and accurate
- [ ] Architecture documentation matches implementation

### Automated Documentation Testing
```bash
#!/bin/bash
# doc-test.sh - Test documentation accuracy

echo "📚 Testing documentation accuracy"

# Extract and test commands from README
grep -o '`[^`]*`' .docker/README.md | sed 's/`//g' | while read cmd; do
    if echo "$cmd" | grep -q "docker\|make"; then
        echo "Testing: $cmd"
        eval "$cmd --help" >/dev/null 2>&1 && echo "✅ Command valid" || echo "❌ Command invalid: $cmd"
    fi
done

echo "Documentation testing complete"
```

This comprehensive testing strategy ensures the Docker directory reorganization is implemented safely, thoroughly validated, and maintains all existing functionality while achieving the organizational benefits.