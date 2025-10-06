# How to Test Page Content

## Purpose
Verify that React applications render correctly using various testing tools, especially when implementing error boundaries or debugging blank page issues.

## Scope
Page content verification, React app testing, error boundary validation, blank page debugging

## Overview
This guide explains how to verify that React applications render correctly using various testing scripts executed via Docker. These tools are essential for debugging rendering issues, validating error boundary implementations, and ensuring the application loads properly.

## Dependencies
- Docker containers running (via `make dev`)
- Node.js scripts in scripts/ directory
- Frontend container: durable-code-frontend-dev

## Quick Start

### Basic Verification
```bash
# Start development environment
make dev

# Basic page content check via Docker
docker exec durable-code-frontend-dev node /app/scripts/check-page-content.js

# Expected output:
# ✅ SUCCESS: App structure looks correct
```

### Advanced Verification
```bash
# Continuous monitoring
docker exec -it durable-code-frontend-dev node /app/scripts/simple-check.js --watch

# Full page verification
docker exec durable-code-frontend-dev node /app/scripts/test-rendered-content.js
```

## Available Testing Scripts

### 1. check-page-content.js
- **Purpose**: Basic HTML structure verification
- **Speed**: Fast (~1-2 seconds)
- **Scope**: Checks for root div, main script, and Vite client
- **Best for**: Quick verification during development

```bash
docker exec durable-code-frontend-dev node /app/scripts/check-page-content.js

# Output:
# 🔍 Checking page content...
# ✅ Has root div: true
# ✅ Has main script: true
# ✅ Has vite client: true
# ✅ SUCCESS: App structure looks correct
```

### 2. simple-check.js (Watch Mode)
- **Purpose**: Continuous page monitoring
- **Speed**: Checks every 5 seconds
- **Scope**: Monitors for changes in page structure
- **Best for**: Active development

```bash
docker exec -it durable-code-frontend-dev node /app/scripts/simple-check.js --watch

# Output (updates every 5 seconds):
# [11:30:15] Checking...
# ✅ App structure OK
# [11:30:20] Checking...
# ✅ App structure OK
```

### 3. test-rendered-content.js
- **Purpose**: Comprehensive page content verification
- **Speed**: Moderate (~5-10 seconds)
- **Scope**: Full DOM structure and JavaScript execution
- **Best for**: Thorough testing before commits

```bash
docker exec durable-code-frontend-dev node /app/scripts/test-rendered-content.js

# Output:
# Starting comprehensive page test...
# ✓ Checking server response
# ✓ Verifying HTML structure
# ✓ Checking JavaScript execution
# ✓ Validating DOM elements
# ✅ ALL TESTS PASSED
```

### 4. Direct Browser Testing
```bash
# Access the application in browser
open http://localhost:5173  # Or your configured port

# Check browser console for errors
# Press F12 → Console tab
```

## Common Scenarios

### Testing After Error Boundary Implementation
```bash
# 1. Initial baseline check
docker exec durable-code-frontend-dev node /app/scripts/check-page-content.js

# 2. Add error boundary code

# 3. Test immediate impact
docker exec durable-code-frontend-dev node /app/scripts/check-page-content.js

# 4. Start continuous monitoring
docker exec -it durable-code-frontend-dev node /app/scripts/simple-check.js --watch
```

### Debugging Blank Page Issues
```bash
# Quick structure check
docker exec durable-code-frontend-dev node /app/scripts/check-page-content.js

# If structure OK but page blank:
docker exec durable-code-frontend-dev node /app/scripts/test-rendered-content.js

# Check JavaScript errors
# Open browser console (F12) and look for red error messages
```

### Binary Search for Problem Components
```bash
# 1. Baseline check
docker exec durable-code-frontend-dev node /app/scripts/check-page-content.js

# 2. Comment out half the components in App.tsx
# 3. Test again
docker exec durable-code-frontend-dev node /app/scripts/check-page-content.js

# 4. Continue narrowing down until issue is found
```

## Troubleshooting

### Issue: "Container not found" Error
```bash
# Ensure containers are running
make dev

# Verify container name
docker ps | grep frontend
```

### Issue: "Script not found" Error
```bash
# Check if script exists in container
docker exec durable-code-frontend-dev ls /app/scripts/

# Ensure you're using the correct path (/app/scripts/)
```

### Issue: Page Loads but Shows Blank
```bash
# Check JavaScript execution
docker exec durable-code-frontend-dev node /app/scripts/test-rendered-content.js

# Look for specific errors in browser console
# Common causes:
# - Error boundary swallowing errors
# - Missing MinimalErrorBoundary
# - Component throw errors
```

### Issue: Tests Pass but Page Still Blank
```bash
# Check browser console for runtime errors
# These might not be caught by static tests

# Test with minimal App.tsx:
# 1. Replace App.tsx with minimal content
# 2. Test: docker exec durable-code-frontend-dev node /app/scripts/check-page-content.js
# 3. Gradually add components back
```

## Error Boundary Testing Workflow

### Step 1: Establish Baseline
```bash
docker exec durable-code-frontend-dev node /app/scripts/check-page-content.js
# Should pass before adding error boundaries
```

### Step 2: Add MinimalErrorBoundary to main.tsx
```bash
# After adding MinimalErrorBoundary wrapper
docker exec durable-code-frontend-dev node /app/scripts/check-page-content.js
```

### Step 3: Add Route-Level Boundaries
```bash
# After adding boundaries to AppShell.tsx
docker exec durable-code-frontend-dev node /app/scripts/check-page-content.js
```

### Step 4: Test Component-Level Boundaries
```bash
# After adding boundaries to individual components
docker exec durable-code-frontend-dev node /app/scripts/test-rendered-content.js
```

## Advanced Debugging

### Using Browser DevTools
```javascript
// In browser console (F12):
// Check if React loaded
window.React

// Check root element
document.getElementById('root')

// Check for error boundary state
document.querySelectorAll('[data-error-boundary]')
```

### Custom Debug Script
```bash
# Create a custom debug script
cat << 'EOF' > debug-page.js
const http = require('http');

http.get('http://localhost:5173', (res) => {
  let data = '';
  res.on('data', chunk => data += chunk);
  res.on('end', () => {
    console.log('Has root div:', data.includes('id="root"'));
    console.log('Has scripts:', data.includes('<script'));
    console.log('Page length:', data.length);
  });
});
EOF

# Run it in container
docker cp debug-page.js durable-code-frontend-dev:/tmp/
docker exec durable-code-frontend-dev node /tmp/debug-page.js
```

## Performance Monitoring
```bash
# Time the checks
time docker exec durable-code-frontend-dev node /app/scripts/check-page-content.js

# Monitor multiple times
for i in {1..5}; do
  echo "Check $i:"
  time docker exec durable-code-frontend-dev node /app/scripts/check-page-content.js
  sleep 2
done
```

## CI/CD Integration

### GitHub Actions
```yaml
- name: Test Page Content
  run: |
    docker exec durable-code-frontend-dev node /app/scripts/check-page-content.js || echo "Page content verification failed"
```

### Pre-commit Hook
```bash
#!/bin/bash
# Add to .git/hooks/pre-commit
docker exec durable-code-frontend-dev node /app/scripts/check-page-content.js || {
  echo "Page content verification failed"
  exit 1
}
```

## Key Points

### Common Issues and Solutions
- **Blank page with no errors**: Usually MinimalErrorBoundary missing
- **Page loads then goes blank**: Component-level error
- **Partial content visible**: Route-level error boundary issue
- **Console errors but page works**: Non-critical errors, check ErrorBoundary logs

### Performance Expectations
- `check-page-content.js`: ~1-2 seconds (HTTP only)
- `test-rendered-content.js`: ~5-10 seconds (Full browser)
- `simple-check.js --watch`: Continuous (5-second intervals)

### Best Practices
1. Use `check-page-content.js` for quick development feedback
2. Use `test-rendered-content.js` for comprehensive testing
3. Use `simple-check.js --watch` during active development
4. Always check browser console for runtime errors
5. Test after each error boundary addition

## Related Documentation
- `.ai/features/error-boundaries.md` - Error boundary implementation details
- `.ai/howto/implement-error-boundaries.md` - Step-by-step implementation guide
- `.ai/docs/DOCKER_EXECUTION_STANDARDS.md` - Docker execution patterns