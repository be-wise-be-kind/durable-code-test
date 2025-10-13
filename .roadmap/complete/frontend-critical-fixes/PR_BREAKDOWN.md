# Frontend Critical Fixes - PR Breakdown

**Purpose**: Detailed implementation breakdown of critical frontend fixes into manageable, atomic pull requests

**Scope**: Complete fix implementation from CSS architecture refactor through comprehensive documentation

**Overview**: Comprehensive breakdown of the Frontend Critical Fixes into 7 manageable, atomic
    pull requests. Each PR is designed to be self-contained, testable, and maintains application functionality
    while incrementally fixing critical issues. Includes detailed implementation steps, file
    structures, testing requirements, and success criteria for each PR.

**Dependencies**: React 18, TypeScript 5, CSS Modules, Zustand, Vite, Vitest

**Exports**: PR implementation plans, file structures, testing strategies, and success criteria for each fix phase

**Related**: AI_CONTEXT.md for review findings, PROGRESS_TRACKER.md for status tracking, TESTING_STRATEGY.md for test plans

**Implementation**: Atomic PR approach with detailed step-by-step fix guidance and comprehensive testing validation

---

## 🚀 PROGRESS TRACKER - MUST BE UPDATED AFTER EACH PR!

### ✅ Completed PRs
- ✅ PR1: CSS Architecture Refactor
- ✅ PR2: WebSocket Memory Leak Fix
- ✅ PR3: React Hook Dependencies Fix
- ✅ PR4: Navigation Race Condition Fix
- ✅ PR5: Component Performance Optimization

### 🎯 NEXT PR TO IMPLEMENT
➡️ **IN PROGRESS: PR6** - Critical System Testing (ErrorBoundary + PerformanceMonitor)

### 📋 Remaining PRs
- 🟡 PR6: Critical System Testing (IN PROGRESS)
- ⬜ PR7: Integration & E2E Testing
- ⬜ PR8: Accessibility Testing
- ⬜ PR9: Coverage Gap Filling
- ⬜ PR10: Documentation Enhancement

**Progress**: 50% Complete (5/10 PRs)

**Note**: Original 7 PRs expanded to 10 PRs for better focus and manageability. PR6 (Testing) was split into PR6-9 (Critical Systems, Integration, A11y, Coverage).

---

## Overview
This document breaks down the critical frontend fixes into manageable, atomic PRs. Each PR is designed to be:
- Self-contained and testable
- Maintains a working application
- Incrementally improves stability and performance
- Revertible if needed

---

## PR1: CSS Architecture Refactor

### Overview
Decompose the 2,686-line monolithic App.css into proper CSS modules, establishing sustainable component architecture.

### Files to Create
```
src/components/Hero/Hero.module.css
src/components/TabNavigation/TabNavigation.module.css
src/components/TabContent/TabContent.module.css
src/components/CardGrid/CardGrid.module.css
src/components/Features/Features.module.css
src/styles/global.css (reduced App.css)
```

### Files to Modify
```
src/App.css → src/styles/global.css
src/components/Hero/Hero.tsx
src/components/TabNavigation/TabNavigation.tsx
src/components/TabContent/TabContent.tsx
src/components/CardGrid/CardGrid.tsx
src/App.tsx
```

### Implementation Steps

#### Step 1: Analyze and Map App.css
```bash
# Create a mapping document
# Lines 1-500: Hero section styles
# Lines 501-900: Navigation styles
# Lines 901-1400: Card styles
# Lines 1401-1900: Tab content
# Lines 1901-2686: Utilities and animations
```

#### Step 2: Create Component Modules
```typescript
// src/components/Hero/Hero.module.css
.hero {
  /* Migrate hero styles from App.css */
  background: var(--gradient-hero);
  padding: var(--space-8) var(--space-4);
}

.heroTitle {
  /* Use design tokens */
  color: var(--color-text-primary);
  font-size: var(--text-4xl);
}
```

#### Step 3: Update Component Imports
```typescript
// src/components/Hero/Hero.tsx
import styles from './Hero.module.css';

const Hero: React.FC = () => {
  return (
    <section className={styles.hero}>
      <h1 className={styles.heroTitle}>...</h1>
    </section>
  );
};
```

#### Step 4: Replace Hardcoded Colors
```css
/* Before */
color: #3c2414;
background: linear-gradient(135deg, #f4e8d0 0%, #e8d5b7 100%);

/* After */
color: var(--color-text-primary);
background: var(--gradient-accent);
```

#### Step 5: Create Global Styles
```css
/* src/styles/global.css */
:root {
  /* Design tokens only */
  --color-text-primary: #3c2414;
  --gradient-accent: linear-gradient(135deg, #f4e8d0 0%, #e8d5b7 100%);
}

/* Global resets only */
body {
  margin: 0;
  font-family: var(--font-primary);
}
```

### Testing Requirements
```bash
# Visual regression testing
npm run test:visual

# CSS linting
npm run lint:css

# Component testing
npm run test:components

# Manual QA checklist
- [ ] Hero section appearance unchanged
- [ ] Navigation works correctly
- [ ] Cards display properly
- [ ] Animations smooth
- [ ] Responsive design intact
```

### Success Criteria
- ✅ App.css < 100 lines (global styles only)
- ✅ All components use CSS modules
- ✅ Zero hardcoded colors
- ✅ No visual regressions
- ✅ Stylelint passing

### Rollback Plan
```bash
# If visual regressions detected
git revert HEAD
# Restore App.css from backup
cp App.css.backup src/App.css
```

---

## PR2: WebSocket Memory Leak Fix

### Overview
Fix WebSocket singleton memory leak by implementing proper listener cleanup on component unmount.

### Files to Modify
```
src/hooks/useWebSocket.ts
src/services/WebSocketService.ts
src/hooks/useWebSocket.test.ts (new)
```

### Implementation Steps

#### Step 1: Add Component Tracking
```typescript
// src/services/WebSocketService.ts
class WebSocketService {
  private listeners: Map<string, Map<string, Set<Handler>>>;

  constructor() {
    this.listeners = new Map(); // componentId -> event -> handlers
  }

  addListenerForComponent(
    componentId: string,
    event: string,
    handler: Handler
  ) {
    if (!this.listeners.has(componentId)) {
      this.listeners.set(componentId, new Map());
    }
    const componentListeners = this.listeners.get(componentId)!;

    if (!componentListeners.has(event)) {
      componentListeners.set(event, new Set());
    }
    componentListeners.get(event)!.add(handler);
  }

  removeAllListenersForComponent(componentId: string) {
    const componentListeners = this.listeners.get(componentId);
    if (componentListeners) {
      componentListeners.forEach((handlers, event) => {
        handlers.forEach(handler => {
          this.removeEventListener(event, handler);
        });
      });
      this.listeners.delete(componentId);
    }
  }
}
```

#### Step 2: Update Hook Cleanup
```typescript
// src/hooks/useWebSocket.ts
export const useWebSocket = (url?: string) => {
  const componentId = useRef(generateId());
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;

    return () => {
      mountedRef.current = false;
      // Critical fix: Clean up all listeners for this component
      if (service) {
        service.removeAllListenersForComponent(componentId.current);
      }
    };
  }, []);
};
```

#### Step 3: Add Memory Leak Tests
```typescript
// src/hooks/useWebSocket.test.ts
describe('WebSocket Memory Management', () => {
  it('should clean up listeners on unmount', () => {
    const { unmount } = renderHook(() => useWebSocket());
    const initialListenerCount = getListenerCount();

    // Add some listeners
    act(() => {
      // Trigger listener addition
    });

    unmount();

    expect(getListenerCount()).toBe(initialListenerCount);
  });

  it('should not accumulate listeners on remount', () => {
    const { unmount, rerender } = renderHook(() => useWebSocket());

    // Mount/unmount multiple times
    for (let i = 0; i < 5; i++) {
      rerender();
      unmount();
    }

    expect(getListenerCount()).toBe(0);
  });
});
```

#### Step 4: Add Performance Monitoring
```typescript
// Monitor memory usage
const memoryMonitor = () => {
  if (performance.memory) {
    console.log('Heap size:', performance.memory.usedJSHeapSize);
  }
};

// Add to hook for dev mode
if (process.env.NODE_ENV === 'development') {
  setInterval(memoryMonitor, 10000);
}
```

### Testing Requirements
```bash
# Unit tests
npm run test src/hooks/useWebSocket.test.ts

# Memory profiling
npm run profile:memory

# Integration tests
npm run test:integration:websocket
```

### Success Criteria
- ✅ No listener accumulation
- ✅ Memory stable over 24 hours
- ✅ All WebSocket tests passing
- ✅ Zero memory leaks in profiler

---

## PR3: React Hook Dependencies Fix

### Overview
Fix stale closures and missing dependencies in React hooks throughout the codebase.

### Files to Modify
```
src/hooks/useOscilloscope.ts
src/hooks/useCanvas.ts
src/hooks/useNavigation.ts
src/components/**/*.tsx (audit all)
.eslintrc.json
```

### Implementation Steps

#### Step 1: Enable Exhaustive Deps Rule
```json
// .eslintrc.json
{
  "rules": {
    "react-hooks/exhaustive-deps": "error"
  }
}
```

#### Step 2: Fix useOscilloscope Stale Closure
```typescript
// src/hooks/useOscilloscope.ts
const resetToDefaults = useCallback(() => {
  setState(prev => ({
    ...prev,
    waveType: DEFAULT_OSCILLOSCOPE_STATE.waveType,
    frequency: DEFAULT_OSCILLOSCOPE_STATE.frequency,
    amplitude: DEFAULT_OSCILLOSCOPE_STATE.amplitude,
    offset: DEFAULT_OSCILLOSCOPE_STATE.offset,
  }));

  // Use functional update to avoid stale state
  setState(currentState => {
    if (isConnected && currentState.isStreaming) {
      sendConfiguration({
        waveType: DEFAULT_OSCILLOSCOPE_STATE.waveType,
        frequency: DEFAULT_OSCILLOSCOPE_STATE.frequency,
        amplitude: DEFAULT_OSCILLOSCOPE_STATE.amplitude,
        offset: DEFAULT_OSCILLOSCOPE_STATE.offset,
      });
    }
    return currentState;
  });
}, [isConnected, sendConfiguration]); // Add all dependencies
```

#### Step 3: Fix useCanvas Dependencies
```typescript
// src/hooks/useCanvas.ts
useEffect(() => {
  if (!canvas) return;

  handleResize();
  startAnimation();

  return () => {
    stopAnimation();
  };
}, [canvas, width, height, autoResize, drawFunction]); // Include all
```

#### Step 4: Audit All Components
```bash
# Find all hooks with potential issues
grep -r "useCallback\|useMemo\|useEffect" src/ | grep -v node_modules

# For each finding, verify dependencies
```

### Testing Requirements
```bash
# ESLint check
npm run lint

# Unit tests for hooks
npm run test:hooks

# Integration tests
npm run test:integration
```

### Success Criteria
- ✅ ESLint exhaustive-deps passing
- ✅ No stale closure bugs
- ✅ All tests passing
- ✅ No functional regressions

---

## PR4: Navigation Race Condition Fix

### Overview
Fix race condition in navigation store by making state and history updates atomic.

### Files to Modify
```
src/stores/navigationStore.ts
src/hooks/useNavigation.ts
src/stores/navigationStore.test.ts (new)
```

### Implementation Steps

#### Step 1: Implement Atomic Updates
```typescript
// src/stores/navigationStore.ts
interface NavigationState {
  activeTab: TabName;
  tabHistory: TabName[];
  isNavigating: boolean; // Add navigation lock
}

const useNavigationStore = create<NavigationState>((set, get) => ({
  activeTab: 'Repository',
  tabHistory: ['Repository'],
  isNavigating: false,

  setActiveTab: (tab: TabName) => {
    const state = get();

    // Prevent duplicate navigation
    if (state.activeTab === tab || state.isNavigating) {
      return;
    }

    // Atomic update
    set({
      activeTab: tab,
      tabHistory: [...state.tabHistory, tab],
      isNavigating: true,
    });

    // Update history after state
    window.history.pushState(null, '', `#${tab}`);

    // Release lock
    setTimeout(() => {
      set({ isNavigating: false });
    }, 0);
  },
}));
```

#### Step 2: Add Navigation Guards
```typescript
// src/hooks/useNavigation.ts
const useNavigation = () => {
  const { activeTab, setActiveTab, isNavigating } = useNavigationStore();

  const navigate = useCallback((tab: TabName) => {
    if (isNavigating) {
      console.warn('Navigation in progress, ignoring request');
      return;
    }
    setActiveTab(tab);
  }, [isNavigating, setActiveTab]);

  return { activeTab, navigate, isNavigating };
};
```

#### Step 3: Add Race Condition Tests
```typescript
// src/stores/navigationStore.test.ts
describe('Navigation Race Conditions', () => {
  it('should prevent rapid duplicate navigation', async () => {
    const store = useNavigationStore.getState();

    // Rapid navigation attempts
    store.setActiveTab('Planning');
    store.setActiveTab('Planning');
    store.setActiveTab('Planning');

    // Should only navigate once
    expect(store.tabHistory.filter(t => t === 'Planning').length).toBe(1);
  });

  it('should maintain state-history sync', async () => {
    const store = useNavigationStore.getState();

    store.setActiveTab('Building');

    expect(store.activeTab).toBe('Building');
    expect(window.location.hash).toBe('#Building');
  });
});
```

### Testing Requirements
```bash
# Unit tests
npm run test src/stores/navigationStore.test.ts

# E2E navigation tests
npm run test:e2e:navigation
```

### Success Criteria
- ✅ No duplicate navigation
- ✅ State and history in sync
- ✅ Rapid navigation handled gracefully
- ✅ All navigation tests passing

---

## PR5: Component Performance Optimization

### Overview
Add memoization and optimization to prevent unnecessary re-renders.

### Files to Modify
```
src/components/Button/Button.tsx
src/components/DemoTab/DemoTab.tsx
src/components/OscilloscopeCanvas/OscilloscopeCanvas.tsx
src/contexts/OscilloscopeContext.tsx (new)
```

### Implementation Steps

#### Step 1: Memoize Button Component
```typescript
// src/components/Button/Button.tsx
const Button: React.FC<ButtonProps> = React.memo(({
  variant = 'primary',
  size = 'medium',
  fullWidth = false,
  isLoading = false,
  className,
  children,
  ...props
}) => {
  const classNames = useMemo(() => [
    styles.button,
    styles[variant],
    styles[size],
    fullWidth && styles.fullWidth,
    isLoading && styles.loading,
    className,
  ]
    .filter(Boolean)
    .join(' '), [variant, size, fullWidth, isLoading, className]);

  return (
    <button className={classNames} disabled={isLoading} {...props}>
      {isLoading ? <Spinner /> : children}
    </button>
  );
});
```

#### Step 2: Implement Context for Prop Drilling
```typescript
// src/contexts/OscilloscopeContext.tsx
const OscilloscopeContext = createContext<OscilloscopeContextType | null>(null);

export const OscilloscopeProvider: React.FC<{ children: ReactNode }> = ({
  children
}) => {
  const oscilloscope = useOscilloscope();

  return (
    <OscilloscopeContext.Provider value={oscilloscope}>
      {children}
    </OscilloscopeContext.Provider>
  );
};

export const useOscilloscopeContext = () => {
  const context = useContext(OscilloscopeContext);
  if (!context) {
    throw new Error('useOscilloscopeContext must be used within provider');
  }
  return context;
};
```

#### Step 3: Optimize Canvas Rendering
```typescript
// src/components/OscilloscopeCanvas/OscilloscopeCanvas.tsx
const OscilloscopeCanvas: React.FC<Props> = React.memo(({ data }) => {
  const prevDataRef = useRef<Float32Array>(new Float32Array(0));

  const shouldRedraw = useMemo(() => {
    if (data.length !== prevDataRef.current.length) return true;

    // Sample-based comparison for performance
    const sampleStep = Math.max(1, Math.floor(data.length / 100));
    for (let i = 0; i < data.length; i += sampleStep) {
      if (data[i] !== prevDataRef.current[i]) return true;
    }
    return false;
  }, [data]);

  useEffect(() => {
    if (shouldRedraw) {
      // Perform canvas redraw
      prevDataRef.current = data;
    }
  }, [shouldRedraw, data]);
});
```

### Testing Requirements
```bash
# Performance profiling
npm run profile:components

# Render count tests
npm run test:render-counts

# Performance benchmarks
npm run benchmark:components
```

### Success Criteria
- ✅ 50% reduction in re-renders
- ✅ React DevTools shows optimization
- ✅ Performance metrics improved
- ✅ No functional regressions

---

## PR6: Critical System Testing

### Overview
Add comprehensive tests for ErrorBoundary and PerformanceMonitor - the two critical production systems with ZERO test coverage.

### Rationale for Split
The original PR6 was too large, trying to cover unit tests, integration tests, accessibility tests, and coverage analysis all in one PR. This focused PR targets only the most critical gap: untested error handling and performance monitoring systems that are essential for production stability.

### Files to Create
```
src/core/errors/__tests__/ErrorBoundary.test.tsx
src/core/errors/__tests__/ErrorFallback.test.tsx
src/core/performance/__tests__/PerformanceMonitor.test.ts
src/core/performance/__tests__/usePerformanceMetrics.test.ts
src/test-utils/render.tsx
```

### Implementation Steps

#### Step 1: Create Test Utilities
```typescript
// src/test-utils/render.tsx
import { render, RenderOptions } from '@testing-library/react';
import { ErrorBoundary } from '@/components/ErrorBoundary';

export const renderWithProviders = (
  ui: React.ReactElement,
  options?: RenderOptions
) => {
  const AllProviders: React.FC<{ children: ReactNode }> = ({ children }) => (
    <ErrorBoundary>
      <OscilloscopeProvider>
        {children}
      </OscilloscopeProvider>
    </ErrorBoundary>
  );

  return render(ui, { wrapper: AllProviders, ...options });
};
```

#### Step 2: Test WebSocket Reconnection
```typescript
// src/hooks/useWebSocket.test.ts
describe('WebSocket Reconnection', () => {
  it('should reconnect on connection loss', async () => {
    const { result } = renderHook(() => useWebSocket('ws://test'));

    // Simulate connection loss
    act(() => {
      mockWebSocket.close();
    });

    // Wait for reconnection
    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });
  });
});
```

#### Step 3: Test Error Boundaries
```typescript
// src/components/ErrorBoundary/ErrorBoundary.test.tsx
describe('ErrorBoundary Recovery', () => {
  it('should recover from errors', () => {
    const ThrowError = () => {
      throw new Error('Test error');
    };

    const { getByText, rerender } = render(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>
    );

    expect(getByText(/Something went wrong/)).toBeInTheDocument();

    // Test recovery
    fireEvent.click(getByText('Try Again'));

    rerender(
      <ErrorBoundary>
        <div>Recovered</div>
      </ErrorBoundary>
    );

    expect(getByText('Recovered')).toBeInTheDocument();
  });
});
```

### Testing Requirements
```bash
# Run new tests
cd durable-code-app/frontend
npm test -- src/core/errors/__tests__
npm test -- src/core/performance/__tests__

# Coverage for critical systems
npm run test:coverage -- src/core/errors
npm run test:coverage -- src/core/performance
```

### Success Criteria
- ✅ ErrorBoundary >90% coverage
- ✅ PerformanceMonitor >90% coverage
- ✅ All error recovery paths tested (reset, retry, auto-recovery)
- ✅ All performance threshold scenarios tested
- ✅ Zero flaky tests
- ✅ CI/CD pipeline green

---

## PR7: Integration & E2E Testing

### Overview
Test component interactions and data flow across system boundaries. Focus on WebSocket reconnection scenarios, navigation + browser history integration, and racing game lifecycle testing.

### Rationale
Integration tests catch bugs that unit tests miss by testing the seams between systems. This PR focuses on testing how components work together rather than in isolation.

### Files to Create/Enhance
```
src/features/demo/services/__tests__/websocketService.integration.test.ts (enhance existing)
src/store/__tests__/navigationStore.integration.test.ts (enhance existing)
src/features/racing/__tests__/integration.test.ts (new)
src/test-utils/providers.tsx (new)
src/test-utils/mocks.ts (new)
```

### Implementation Steps

#### Step 1: Create Comprehensive Test Providers
```typescript
// src/test-utils/providers.tsx
import { ReactNode } from 'react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ErrorBoundary } from '@/core/errors';

export const TestProviders: React.FC<{ children: ReactNode }> = ({ children }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return (
    <BrowserRouter>
      <QueryClientProvider client={queryClient}>
        <ErrorBoundary>
          {children}
        </ErrorBoundary>
      </QueryClientProvider>
    </BrowserRouter>
  );
};
```

#### Step 2: WebSocket Reconnection Integration Tests
```typescript
// Enhance src/features/demo/services/__tests__/websocketService.integration.test.ts
describe('WebSocket Integration - Reconnection Scenarios', () => {
  it('should automatically reconnect after connection loss', async () => {
    const service = new WebSocketService();
    await service.connect();

    // Simulate network disruption
    simulateNetworkDisruption();

    // Should attempt reconnection
    await waitFor(() => {
      expect(service.isConnected()).toBe(true);
    }, { timeout: 5000 });
  });

  it('should handle multiple rapid disconnections gracefully', async () => {
    // Test connection resilience under stress
  });
});
```

#### Step 3: Navigation Integration Tests
```typescript
// Enhance src/store/__tests__/navigationStore.integration.test.ts
describe('Navigation Integration - Browser History', () => {
  it('should sync navigation state with browser history', () => {
    const { result } = renderHook(() => useNavigation(), {
      wrapper: TestProviders,
    });

    act(() => {
      result.current.navigate('Planning');
    });

    expect(window.location.hash).toBe('#Planning');
    expect(result.current.activeTab).toBe('Planning');
  });

  it('should handle browser back button correctly', () => {
    // Test browser history integration
  });
});
```

#### Step 4: Racing Game Lifecycle Integration
```typescript
// src/features/racing/__tests__/integration.test.ts
describe('Racing Game Integration', () => {
  it('should handle complete game lifecycle', () => {
    const { result } = renderHook(() => useRacingGame());

    // Start game
    act(() => {
      result.current.startGame();
    });
    expect(result.current.isRunning).toBe(true);

    // Pause game
    act(() => {
      result.current.pauseGame();
    });
    expect(result.current.isPaused).toBe(true);

    // Reset game
    act(() => {
      result.current.resetGame();
    });
    expect(result.current.isRunning).toBe(false);
  });

  it('should integrate physics with rendering correctly', () => {
    // Test physics engine + render loop integration
  });
});
```

### Testing Requirements
```bash
# Run integration tests
cd durable-code-app/frontend
npm test -- --testNamePattern="Integration"

# Run with coverage
npm run test:coverage -- --testNamePattern="Integration"
```

### Success Criteria
- ✅ WebSocket reconnection tested in multiple scenarios
- ✅ Navigation + browser history fully integrated and tested
- ✅ Racing game lifecycle fully tested
- ✅ Reusable test providers created
- ✅ Zero flaky integration tests
- ✅ All integration tests pass in CI/CD

---

## PR8: Accessibility Testing

### Overview
Ensure the application is accessible, keyboard navigable, and screen reader compatible. Focus on critical interactive components.

### Rationale
Accessibility is essential for production applications but often overlooked. This focused PR ensures the app meets WCAG guidelines.

### Files to Create
```
src/components/common/Button/__tests__/Button.a11y.test.tsx
src/components/tabs/__tests__/TabNavigation.a11y.test.tsx
src/core/errors/__tests__/ErrorFallback.a11y.test.tsx
src/test-utils/a11y-helpers.ts
```

### Implementation Steps

#### Step 1: Create A11y Test Helpers
```typescript
// src/test-utils/a11y-helpers.ts
import { render } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';

expect.extend(toHaveNoViolations);

export const testA11y = async (ui: React.ReactElement) => {
  const { container } = render(ui);
  const results = await axe(container);
  expect(results).toHaveNoViolations();
};

export const testKeyboardNavigation = (
  element: HTMLElement,
  expectedKeys: string[]
) => {
  expectedKeys.forEach(key => {
    fireEvent.keyDown(element, { key });
    // Verify expected behavior
  });
};
```

#### Step 2: Button A11y Tests
```typescript
// src/components/common/Button/__tests__/Button.a11y.test.tsx
describe('Button Accessibility', () => {
  it('should have no a11y violations', async () => {
    await testA11y(<Button>Click me</Button>);
  });

  it('should be keyboard accessible', () => {
    const onClick = vi.fn();
    const { getByRole } = render(<Button onClick={onClick}>Click</Button>);
    const button = getByRole('button');

    fireEvent.keyDown(button, { key: 'Enter' });
    expect(onClick).toHaveBeenCalled();

    fireEvent.keyDown(button, { key: ' ' });
    expect(onClick).toHaveBeenCalledTimes(2);
  });

  it('should have proper ARIA attributes when loading', () => {
    const { getByRole } = render(<Button isLoading>Save</Button>);
    expect(getByRole('button')).toHaveAttribute('aria-busy', 'true');
  });
});
```

#### Step 3: Tab Navigation A11y Tests
```typescript
// src/components/tabs/__tests__/TabNavigation.a11y.test.tsx
describe('Tab Navigation Accessibility', () => {
  it('should support keyboard navigation', () => {
    const { getAllByRole } = render(<TabNavigation />);
    const tabs = getAllByRole('tab');

    // Arrow key navigation
    fireEvent.keyDown(tabs[0], { key: 'ArrowRight' });
    expect(tabs[1]).toHaveFocus();
  });

  it('should have proper ARIA roles and labels', () => {
    const { getByRole } = render(<TabNavigation />);
    expect(getByRole('tablist')).toBeInTheDocument();
  });
});
```

### Testing Requirements
```bash
# Run a11y tests
cd durable-code-app/frontend
npm test -- --testNamePattern="Accessibility"

# Run with axe-core
npm test -- Button.a11y.test
```

### Success Criteria
- ✅ All interactive components have a11y tests
- ✅ Keyboard navigation fully tested
- ✅ ARIA attributes validated
- ✅ Screen reader compatibility verified
- ✅ Zero a11y violations in axe-core tests

---

## PR9: Coverage Gap Filling

### Overview
Analyze coverage reports and systematically fill gaps to achieve 80%+ overall coverage target.

### Rationale
This is the "cleanup" PR that gets us over the finish line on coverage goals. After testing critical systems (PR6), integration (PR7), and a11y (PR8), we now fill remaining gaps.

### Implementation Steps

#### Step 1: Run Coverage Analysis
```bash
cd durable-code-app/frontend
npm run test:coverage

# Generate detailed HTML report
npm run test:coverage -- --reporter=html

# Open coverage/index.html and identify gaps
```

#### Step 2: Identify Critical Uncovered Branches
Focus on:
- Async operations and error paths
- State mutation edge cases
- Complex conditional logic
- Error handling in catch blocks

#### Step 3: Add Missing Tests
Create tests targeting specific uncovered lines/branches identified in Step 1.

### Testing Requirements
```bash
# Run full coverage
npm run test:coverage

# Verify thresholds met
npm test -- --coverage --coverageThreshold='{"global":{"branches":80,"functions":80,"lines":80,"statements":80}}'
```

### Success Criteria
- ✅ Overall coverage >80% (branches, functions, lines, statements)
- ✅ All async operations tested
- ✅ All error paths tested
- ✅ All edge cases covered
- ✅ Zero flaky tests
- ✅ Coverage thresholds enforced in CI/CD

---

## PR10: Documentation Enhancement

### Overview
Add comprehensive documentation including JSDoc, examples, and architectural guides.

### Files to Create/Modify
```
src/components/**/*.tsx (add JSDoc)
docs/ARCHITECTURE.md (new)
docs/COMPONENTS.md (new)
CONTRIBUTING.md
README.md
```

### Implementation Steps

#### Step 1: Add Component JSDoc
```typescript
/**
 * Button component with multiple variants and loading states
 *
 * @component
 * @example
 * // Primary button
 * <Button variant="primary" onClick={handleClick}>
 *   Click me
 * </Button>
 *
 * @example
 * // Loading state
 * <Button isLoading>
 *   Saving...
 * </Button>
 */
export const Button: React.FC<ButtonProps> = ({ ... }) => {
```

#### Step 2: Create Architecture Guide
```markdown
# Frontend Architecture

## Overview
This React application uses...

## Component Structure
Components follow a consistent pattern...

## State Management
We use Zustand for global state...

## Styling
CSS Modules provide component isolation...
```

#### Step 3: Add Usage Examples
```typescript
// In each component file, add examples
/**
 * @example
 * const MyComponent = () => {
 *   const { data, isLoading } = useWebSocket('ws://localhost:3000');
 *
 *   if (isLoading) return <Spinner />;
 *
 *   return <DataDisplay data={data} />;
 * };
 */
```

### Testing Requirements
```bash
# Documentation linting
npm run lint:docs

# Example code verification
npm run test:examples

# Documentation build
npm run build:docs
```

### Success Criteria
- ✅ 100% JSDoc coverage
- ✅ All components documented
- ✅ Architecture guide complete
- ✅ Examples working

---

## Implementation Guidelines

### Code Standards
- Maintain TypeScript strict mode
- Follow existing ESLint rules
- Use Prettier for formatting
- Preserve existing patterns

### Testing Requirements
- Unit tests for all changes
- Integration tests for critical paths
- Visual regression tests for UI changes
- Performance benchmarks where applicable

### Documentation Standards
- JSDoc for all public APIs
- Usage examples for components
- Inline comments for complex logic
- README updates for new features

### Security Considerations
- No sensitive data in commits
- Validate all inputs
- Sanitize user content
- Follow OWASP guidelines

### Performance Targets
- Bundle size < 300KB gzipped
- First paint < 1.5s
- Time to interactive < 2.5s
- 60fps animations

## Rollout Strategy

### Phase 1: Critical Stability ✅ COMPLETE
- PR1: CSS Architecture Refactor
- PR2: WebSocket Memory Leak Fix

### Phase 2: Code Quality ✅ COMPLETE
- PR3: React Hook Dependencies Fix
- PR4: Navigation Race Condition Fix

### Phase 3: Optimization ✅ COMPLETE
- PR5: Component Performance Optimization

### Phase 4: Quality Assurance 🟡 IN PROGRESS
- PR6: Critical System Testing ← IN PROGRESS
- PR7: Integration & E2E Testing
- PR8: Accessibility Testing
- PR9: Coverage Gap Filling

### Phase 5: Documentation
- PR10: Documentation Enhancement
- Final review and deployment

## Success Metrics

### Launch Metrics
- All 10 PRs completed (5/10 complete ✅)
- All 7 original critical issues resolved
- Test coverage > 80%
- Zero memory leaks
- Performance targets met

### Ongoing Metrics
- Bug rate reduced by 40%
- Developer velocity improved by 30%
- Code review time reduced by 25%
- User satisfaction maintained