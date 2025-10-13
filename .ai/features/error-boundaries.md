# Error Boundaries Feature

**Purpose**: Comprehensive React error boundary system implementing 3-tier architecture for error isolation and recovery

**Scope**: React application error handling, component isolation, error recovery mechanisms, application stability

**Overview**: Complete React error boundary system that implements a 3-tier architecture to isolate errors
    and provide recovery mechanisms throughout the application. Ensures that component errors do not
    crash the entire application while providing users with graceful error handling and recovery
    options. Includes root-level, route-level, and component-level error boundaries for comprehensive
    error isolation and user experience protection.

**Dependencies**: React error boundary patterns, error recovery mechanisms, user interface components

**Exports**: Error boundary components, error isolation patterns, recovery mechanisms, stability frameworks

**Related**: React component guidelines, error handling standards, application stability patterns

**Implementation**: 3-tier error boundary architecture, graceful error recovery, component isolation strategies

---

## Error Boundary System Overview

Comprehensive 3-tier error boundary architecture that isolates errors and provides recovery mechanisms to prevent application crashes.

## Architecture

### 3-Tier Error Boundary System
1. **Root Level** (`main.tsx`) - Catches app-wide errors and prevents complete application crashes
2. **Route Level** (`AppShell.tsx`) - Isolates errors to specific pages/routes
3. **Component Level** (`HomePage.tsx`, etc.) - Isolates errors in specific features like tab content

### Core Components

#### MinimalErrorBoundary
- **Location**: `src/core/errors/MinimalErrorBoundary.tsx`
- **Purpose**: Stable, lightweight error boundary for production use
- **Features**: Simple error catching with basic UI fallback
- **Recommended**: Use this for most implementations due to stability

#### ErrorBoundary (Advanced)
- **Location**: `src/core/errors/ErrorBoundary.tsx`
- **Purpose**: Full-featured error boundary with recovery mechanisms
- **Features**: Retry logic, reset functionality, error logging, auto-recovery
- **Note**: More complex, use when advanced features are needed

#### Global Error Handling
- **Location**: `main.tsx` (simplified implementation)
- **Purpose**: Catch unhandled errors and promise rejections
- **Features**: Error storm protection, global error logging
- **Security**: Prevents DoS-like error cascades

## File Structure

```
src/core/errors/
├── MinimalErrorBoundary.tsx      # Recommended stable implementation
├── ErrorBoundary.tsx             # Advanced error boundary with recovery
├── ErrorBoundary.types.ts        # TypeScript interfaces
├── ErrorFallback.tsx             # Error UI components
├── ErrorFallback.module.css      # Error UI styling
├── ErrorLogger.ts               # Structured error logging
├── GlobalErrorHandler.ts        # Window-level error capture
├── SimpleErrorBoundary.tsx      # Basic implementation
└── index.ts                     # Barrel exports
```

## Implementation Patterns

### 1. Root Level Implementation
```tsx
// main.tsx
import { MinimalErrorBoundary } from './core/errors/MinimalErrorBoundary';

createRoot(rootElement).render(
  <StrictMode>
    <MinimalErrorBoundary>
      <AppProviders>
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </AppProviders>
    </MinimalErrorBoundary>
  </StrictMode>,
);
```

### 2. Route Level Implementation
```tsx
// AppShell.tsx
import { MinimalErrorBoundary } from '../../core/errors/MinimalErrorBoundary';

<Routes>
  <Route
    path="/"
    element={
      <MinimalErrorBoundary>
        <HomePage />
      </MinimalErrorBoundary>
    }
  />
</Routes>
```

### 3. Component Level Implementation
```tsx
// HomePage.tsx or any component
import { MinimalErrorBoundary } from '../../core/errors/MinimalErrorBoundary';

<MinimalErrorBoundary>
  <Suspense fallback={<LoadingSpinner />}>
    <ActiveTabComponent />
  </Suspense>
</MinimalErrorBoundary>
```

## Testing and Verification

### Testing Tools
- `node scripts/test-rendered-content.js` - Simple HTTP-based content verification
- `scripts/simple-check.js` - Container-based quick verification
- `scripts/check-page-content.js` - Comprehensive Playwright verification

### Verification Process
1. **Start development**: `just dev`
2. **Basic check**: `docker exec durable-code-frontend-dev node /app/scripts/check-page-content.js`
3. **Content verification**: `docker exec durable-code-frontend-dev node /app/scripts/test-rendered-content.js`
4. **Continuous monitoring**: `docker exec -it durable-code-frontend-dev node /app/scripts/simple-check.js --watch`

## Error Boundary Requirements

### When to Add Error Boundaries
- ✅ **Required**: All route components in AppShell
- ✅ **Required**: Root level in main.tsx
- ✅ **Recommended**: Around lazy-loaded components
- ✅ **Recommended**: Around complex feature components
- ✅ **Recommended**: Around third-party library integrations

### Error Boundary Standards
- Use `MinimalErrorBoundary` by default for stability
- Only use `ErrorBoundary` when advanced features (retry, reset) are needed
- Always test error boundaries with `scripts/check-page-content.js` after implementation
- Ensure error boundaries don't break application functionality
- Include error boundaries in code reviews

## Security and Performance

### Global Error Protection
```tsx
// Simplified global error handling (in main.tsx)
let errorCount = 0;
let lastErrorTime = 0;
const ERROR_THRESHOLD = 5;
const TIME_WINDOW = 60000;

window.addEventListener('error', (event) => {
  // Error storm protection logic
  // Prevents >5 errors per minute
});

window.addEventListener('unhandledrejection', (event) => {
  // Promise rejection handling
  // Catches async errors
});
```

### Performance Considerations
- Error boundaries add minimal overhead
- Global error handlers prevent resource exhaustion
- Error storm protection prevents DoS-like scenarios
- Logging is optimized for production use

## Integration with Other Features

### React Router
- Error boundaries wrap individual routes
- Route-level isolation prevents navigation errors
- Maintains router state during error recovery

### Lazy Loading
- Error boundaries protect against dynamic import failures
- Suspense + ErrorBoundary pattern for robust loading
- Fallback UI for both loading and error states

### Feature Architecture
- Each feature module can have its own error boundaries
- Component-level isolation within features
- Consistent error handling patterns across features

## Development Guidelines

### Code Generation Templates
- Use `react-error-boundary.tsx.template` for new error boundaries
- Follow existing patterns in `src/core/errors/`
- Include TypeScript types for all error boundary props

### Testing Requirements
- Test error boundaries with intentional errors
- Verify recovery mechanisms work correctly
- Ensure error boundaries don't interfere with normal operation
- Use page content verification tools during development

### Best Practices
1. **Start Simple**: Use MinimalErrorBoundary first
2. **Test Early**: Verify with `scripts/check-page-content.js` immediately
3. **Isolate Errors**: Implement at multiple levels for better isolation
4. **Monitor**: Use continuous verification during development
5. **Document**: Include error boundary usage in component documentation

## Common Issues and Solutions

### Issue: Blank Page After Adding Error Boundaries
- **Cause**: Complex error boundary implementation breaking React rendering
- **Solution**: Use MinimalErrorBoundary instead of ErrorBoundary
- **Verification**: Test with `scripts/check-page-content.js` after each change

### Issue: Global Error Handler Breaking App
- **Cause**: setupGlobalErrorHandling function complexity
- **Solution**: Use simplified inline global error handlers
- **Example**: See main.tsx implementation

### Issue: Error Boundaries Not Catching Errors
- **Cause**: Error boundaries only catch errors in child components
- **Solution**: Ensure error boundaries are placed above the components that might error
- **Testing**: Deliberately trigger errors to verify boundaries work

## Migration Guide

### Adding Error Boundaries to Existing Components
1. Import MinimalErrorBoundary
2. Wrap the component with the error boundary
3. Test with `docker exec durable-code-frontend-dev node /app/scripts/check-page-content.js`
4. Verify functionality is preserved
5. Update documentation

### Template Usage
```tsx
import { MinimalErrorBoundary } from '../core/errors/MinimalErrorBoundary';

function YourComponent() {
  return (
    <MinimalErrorBoundary>
      {/* Your existing component content */}
    </MinimalErrorBoundary>
  );
}
```

## Related Documentation
- `.ai/howto/implement-error-boundaries.md` - Step-by-step implementation guide
- `.ai/howto/test-page-content.md` - Page verification guide
- `.ai/templates/react-error-boundary.tsx.template` - Code generation template
- `src/core/errors/` - Implementation examples
