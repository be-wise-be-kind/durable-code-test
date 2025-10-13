# How to Implement Error Boundaries

## Purpose
Implement React error boundaries using the 3-tier architecture for robust error handling and recovery in React applications.

## Scope
React error boundaries, error handling, component isolation, fallback UI, error recovery

## Overview
This guide shows how to implement React error boundaries using the 3-tier architecture for robust error handling and recovery. Error boundaries provide a way to catch JavaScript errors in component trees, log those errors, and display a fallback UI instead of crashing the entire application.

## Dependencies
- React 16+ with TypeScript
- MinimalErrorBoundary component from src/core/errors/
- ErrorBoundary component for advanced features
- Testing scripts in scripts/ directory

## Prerequisites
- React application with TypeScript
- Understanding of React component lifecycle
- Access to `src/core/errors/` repository

## Quick Start

### 1. Use MinimalErrorBoundary (Recommended)
```tsx
import { MinimalErrorBoundary } from '../core/errors/MinimalErrorBoundary';

function MyComponent() {
  return (
    <MinimalErrorBoundary>
      {/* Component content that might error */}
      <SomeFeatureComponent />
    </MinimalErrorBoundary>
  );
}
```

### 2. Verify Implementation
```bash
# Test the implementation via Docker
docker exec durable-code-frontend-dev node /app/scripts/check-page-content.js

# Or use direct verification
docker exec durable-code-frontend-dev node /app/scripts/test-rendered-content.js
```

## 3-Tier Implementation Guide

### Tier 1: Root Level (main.tsx)
**Purpose**: Catch any app-wide errors that escape other boundaries

```tsx
// main.tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import { MinimalErrorBoundary } from './core/errors/MinimalErrorBoundary';
import { App } from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <MinimalErrorBoundary>
      <App />
    </MinimalErrorBoundary>
  </React.StrictMode>
);
```

**Test after implementation**:
```bash
docker exec durable-code-frontend-dev node /app/scripts/check-page-content.js
```

### Tier 2: Route Level (AppShell.tsx)
**Purpose**: Isolate errors to specific routes

```tsx
// components/AppShell/AppShell.tsx
import { MinimalErrorBoundary } from '../../core/errors/MinimalErrorBoundary';
import { Outlet } from 'react-router-dom';

export function AppShell() {
  return (
    <div className="app-shell">
      <Header />
      <MinimalErrorBoundary>
        <main className="app-content">
          <Outlet />
        </main>
      </MinimalErrorBoundary>
      <Footer />
    </div>
  );
}
```

**Test after implementation**:
```bash
docker exec durable-code-frontend-dev node /app/scripts/check-page-content.js
```

### Tier 3: Component Level
**Purpose**: Isolate errors in high-risk components

```tsx
// features/demo/components/OscilloscopeTab.tsx
import { MinimalErrorBoundary } from '../../../core/errors/MinimalErrorBoundary';

export function OscilloscopeTab() {
  return (
    <MinimalErrorBoundary>
      {/* High-risk WebSocket or data-heavy component */}
      <Oscilloscope />
    </MinimalErrorBoundary>
  );
}
```

**Test after implementation**:
```bash
docker exec durable-code-frontend-dev node /app/scripts/test-rendered-content.js
```

## Using Advanced ErrorBoundary

For components needing custom error handling:

```tsx
import { ErrorBoundary } from '../../core/errors/ErrorBoundary';

function MyAdvancedComponent() {
  return (
    <ErrorBoundary
      fallback={<CustomErrorUI />}
      onError={(error, errorInfo) => {
        console.error('Custom error handler:', error);
        // Send to error tracking service
      }}
    >
      <ComplexFeature />
    </ErrorBoundary>
  );
}
```

## Implementation Checklist

### Phase 1: Root Protection
- [ ] Add MinimalErrorBoundary to main.tsx
- [ ] Test current functionality: `docker exec durable-code-frontend-dev node /app/scripts/check-page-content.js`
- [ ] Verify no regression

### Phase 2: Route Protection
- [ ] Add boundaries to AppShell or main route container
- [ ] Test after each addition: `docker exec durable-code-frontend-dev node /app/scripts/check-page-content.js`
- [ ] Ensure header/footer remain visible during errors

### Phase 3: Component Protection
- [ ] Identify high-risk components (WebSocket, async data, complex state)
- [ ] Add MinimalErrorBoundary to each
- [ ] Test individually

### Phase 4: Verification
```bash
# Basic check
docker exec durable-code-frontend-dev node /app/scripts/check-page-content.js

# Continuous monitoring
docker exec -it durable-code-frontend-dev node /app/scripts/simple-check.js --watch

# Full verification
docker exec durable-code-frontend-dev node /app/scripts/test-rendered-content.js
```

## Common Patterns

### Pattern 1: Async Component Loading
```tsx
const LazyComponent = React.lazy(() => import('./LazyComponent'));

function AsyncFeature() {
  return (
    <MinimalErrorBoundary>
      <Suspense fallback={<Loading />}>
        <LazyComponent />
      </Suspense>
    </MinimalErrorBoundary>
  );
}
```

### Pattern 2: Data Fetching
```tsx
function DataComponent() {
  return (
    <MinimalErrorBoundary>
      {data ? <DataDisplay data={data} /> : <Loading />}
    </MinimalErrorBoundary>
  );
}
```

### Pattern 3: WebSocket Connections
```tsx
function WebSocketFeature() {
  return (
    <MinimalErrorBoundary>
      <WebSocketProvider>
        <RealtimeDisplay />
      </WebSocketProvider>
    </MinimalErrorBoundary>
  );
}
```

## Testing Error Boundaries

### Manual Testing
```tsx
// Temporary error trigger for testing
function TestError() {
  const [shouldError, setShouldError] = useState(false);

  if (shouldError) {
    throw new Error('Test error boundary');
  }

  return (
    <button onClick={() => setShouldError(true)}>
      Trigger Error
    </button>
  );
}
```

### Automated Testing
```bash
# After adding test component
docker exec durable-code-frontend-dev node /app/scripts/test-rendered-content.js

# Should show error boundary UI instead of blank page
```

## Troubleshooting

### Issue: Page Goes Blank After Adding Error Boundary

**Symptoms**: Page content check shows empty root div
```bash
docker exec durable-code-frontend-dev node /app/scripts/check-page-content.js
# Shows: ❌ Has root div: false
```

**Solution**:
1. Use MinimalErrorBoundary instead of ErrorBoundary
2. Check for errors in error boundary itself
3. Verify import paths

### Issue: Error Boundary Not Catching Errors

**Test Process**:
```bash
# 1. Add console.log to error boundary
# 2. Test: docker exec durable-code-frontend-dev node /app/scripts/check-page-content.js
# 3. Check browser console for logs
# 4. Test: docker exec durable-code-frontend-dev node /app/scripts/test-rendered-content.js
# 5. Verify componentDidCatch is called
```

### Issue: Errors in Event Handlers

Error boundaries don't catch errors in:
- Event handlers
- Asynchronous code
- Server-side rendering
- Errors in the error boundary itself

**Solution**: Use try-catch in event handlers:
```tsx
function MyComponent() {
  const handleClick = () => {
    try {
      riskyOperation();
    } catch (error) {
      console.error('Event handler error:', error);
      // Show user-friendly message
    }
  };

  return <button onClick={handleClick}>Click me</button>;
}
```

## Best Practices

1. **Start with MinimalErrorBoundary**
   - Proven stable implementation
   - Minimal overhead
   - Easy to debug

2. **Test incrementally**
   - Add one boundary at a time
   - Test after each addition
   - Use continuous monitoring during development

3. **Layer appropriately**
   - Root: Last resort catch-all
   - Route: Isolate page failures
   - Component: High-risk areas only

4. **Monitor in production**
   - Log errors to tracking service
   - Monitor error boundary triggers
   - Track recovery success rate

## Performance Considerations

- MinimalErrorBoundary has negligible performance impact
- Don't over-wrap components (avoid nesting boundaries)
- Use React.memo() for frequently re-rendered boundaries

## Security Notes

- Don't expose sensitive error details to users
- Sanitize error messages in production
- Log full details server-side only

## Related Documentation

- `.ai/features/error-boundaries.md` - Feature overview
- `.ai/docs/STANDARDS.md#error-boundaries` - Standards and patterns
- `.ai/templates/react-error-boundary.tsx.template` - Template for custom boundaries
- `src/core/errors/` - Error boundary implementations