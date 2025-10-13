# Security & Quality Remediation - PR Breakdown

**Purpose**: Detailed implementation breakdown of Security & Quality Remediation into manageable, atomic pull requests

**Scope**: Complete remediation from initial security analysis through final validation

**Overview**: Comprehensive breakdown of the Security & Quality Remediation feature into 6 manageable, atomic
    pull requests. Each PR is designed to be self-contained, testable, and maintains application functionality
    while incrementally building toward the complete feature. Includes detailed implementation steps, file
    structures, testing requirements, and success criteria for each PR.

**Dependencies**: 5-agent security analysis completed (67 issues identified)

**Exports**: PR implementation plans, file structures, testing strategies, and success criteria for each development phase

**Related**: AI_CONTEXT.md for feature overview, PROGRESS_TRACKER.md for status tracking

**Implementation**: Atomic PR approach with detailed step-by-step implementation guidance and comprehensive testing validation

---

## 🚀 PROGRESS TRACKER - MUST BE UPDATED AFTER EACH PR!

### ✅ Completed PRs
- ⬜ None yet - Planning phase just completed

### 🎯 NEXT PR TO IMPLEMENT
➡️ **START HERE: PR1** - Python Backend Security Fixes

### 📋 Remaining PRs
- [ ] PR1: Python Backend Security (3-4 days)
- [ ] PR2: Frontend Security (2-3 days)
- [ ] PR3: Python Code Quality (3-4 days)
- [ ] PR4: TypeScript/React Quality (2 days)
- [ ] PR5: AWS Infrastructure Security (3-4 days)
- [ ] PR6: Final Security Evaluation (1 day)

**Progress**: 0% Complete (0/6 PRs)

---

## Overview
This document breaks down the Security & Quality Remediation feature into manageable, atomic PRs. Each PR is designed to be:
- Self-contained and testable
- Maintains a working application
- Incrementally builds toward the complete feature
- Revertible if needed

---

## PR1: Python Backend Security Fixes

**Branch**: `security/python-backend-fixes`
**Priority**: P0 (Critical)
**Estimated Effort**: 3-4 days
**Dependencies**: None

### Scope
Fix 6 critical and high-severity backend security vulnerabilities:
1. Circuit breaker race condition
2. Global random seed manipulation
3. Weak RNG (Mersenne Twister)
4. WebSocket resource exhaustion
5. ReDoS in validation regex
6. Information disclosure in error messages

### Files to Modify
- `durable-code-app/backend/app/core/circuit_breaker.py`
- `durable-code-app/backend/app/security.py`
- `durable-code-app/backend/app/racing.py`
- `durable-code-app/backend/app/oscilloscope.py`
- `durable-code-app/backend/tests/test_circuit_breaker.py` (new)
- `durable-code-app/backend/tests/test_security.py` (new)

### Implementation Steps

#### Step 1: Fix Circuit Breaker Race Condition

**File**: `durable-code-app/backend/app/core/circuit_breaker.py:88-111`

```python
# CURRENT CODE (vulnerable):
async def call(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    async with self.state_manager._lock:
        await self.state_manager.check_state_transition()
        if self.state_manager.state == CircuitBreakerState.OPEN:
            raise ExternalServiceError(...)
    # LOCK RELEASED - RACE CONDITION!
    try:
        result = await self._execute_function(func, *args, **kwargs)
        await self.state_manager.on_success()  # No lock!

# FIXED CODE:
async def call(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    async with self.state_manager._lock:
        await self.state_manager.check_state_transition()
        if self.state_manager.state == CircuitBreakerState.OPEN:
            raise ExternalServiceError(...)

    try:
        result = await self._execute_function(func, *args, **kwargs)
        async with self.state_manager._lock:
            await self.state_manager.on_success()
        return result
    except Exception as e:
        async with self.state_manager._lock:
            await self.state_manager.on_failure()
        raise
```

#### Step 2: Remove Global Random Seed

**File**: `durable-code-app/backend/app/racing.py:29`

```python
# REMOVE THIS LINE:
random.seed(42)

# ADD AT MODULE LEVEL:
import secrets
from dataclasses import dataclass

@dataclass
class TrackGenerator:
    """Track generator with instance-level randomness"""
    _rng: random.Random = None

    def __post_init__(self):
        self._rng = random.Random()
```

#### Step 3: Use Cryptographic RNG

**File**: `durable-code-app/backend/app/racing.py:36,39,83`

Replace all `random.random()`, `random.uniform()`, `random.gauss()` calls:

```python
# BEFORE:
angle = random.uniform(min_angle, max_angle)

# AFTER:
angle = secrets.SystemRandom().uniform(min_angle, max_angle)

# OR create instance method in TrackGenerator:
def _random_uniform(self, a: float, b: float) -> float:
    """Cryptographically secure random float"""
    return secrets.SystemRandom().uniform(a, b)
```

#### Step 4: Add WebSocket Timeouts

**File**: `durable-code-app/backend/app/oscilloscope.py:20-69`

```python
# ADD at top of file:
from contextlib import asynccontextmanager
import asyncio

WEBSOCKET_TIMEOUT = 30.0  # seconds
WEBSOCKET_MAX_MESSAGE_SIZE = 1024 * 1024  # 1MB

@asynccontextmanager
async def websocket_timeout(seconds: float):
    """Timeout context manager for WebSocket operations"""
    try:
        async with asyncio.timeout(seconds):
            yield
    except TimeoutError:
        raise WebSocketDisconnect(code=1000, reason="Operation timeout")

# MODIFY websocket_endpoint function:
@app.websocket("/ws/oscilloscope")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    try:
        async with websocket_timeout(WEBSOCKET_TIMEOUT):
            while True:
                # Existing oscilloscope logic
                await websocket.send_json(data)
                await asyncio.sleep(0.05)
    except WebSocketDisconnect:
        logger.info("Client disconnected")
```

#### Step 5: Add WebSocket Rate Limiting

**File**: `durable-code-app/backend/app/oscilloscope.py` (add new middleware)

```python
from collections import defaultdict
from time import time

class WebSocketRateLimiter:
    """Rate limiter for WebSocket connections"""
    def __init__(self, max_connections_per_ip: int = 5):
        self.connections: dict[str, list[float]] = defaultdict(list)
        self.max_connections = max_connections_per_ip
        self.window = 60.0  # 60 second window

    def check_rate_limit(self, client_ip: str) -> bool:
        """Check if client is within rate limits"""
        now = time()
        # Remove old connections
        self.connections[client_ip] = [
            t for t in self.connections[client_ip]
            if now - t < self.window
        ]

        if len(self.connections[client_ip]) >= self.max_connections:
            return False

        self.connections[client_ip].append(now)
        return True

# Use in websocket endpoint:
rate_limiter = WebSocketRateLimiter()

@app.websocket("/ws/oscilloscope")
async def websocket_endpoint(websocket: WebSocket):
    client_ip = websocket.client.host
    if not rate_limiter.check_rate_limit(client_ip):
        await websocket.close(code=1008, reason="Rate limit exceeded")
        return
    # ... rest of endpoint
```

#### Step 6: Fix ReDoS in Validation

**File**: `durable-code-app/backend/app/security.py:45`

```python
# BEFORE (vulnerable to ReDoS):
PATH_PATTERN = re.compile(r'^(/[a-zA-Z0-9_-]+)+$')

# AFTER (atomic, no backtracking):
PATH_PATTERN = re.compile(r'^(?:/[a-zA-Z0-9_-]+)+$')
```

#### Step 7: Sanitize Error Messages

**File**: `durable-code-app/backend/app/core/exceptions.py`

```python
# ADD new exception handler:
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Sanitize all error messages in production"""
    if settings.ENVIRONMENT == "production":
        # Generic error message
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal error occurred"}
        )
    else:
        # Detailed error in development
        return JSONResponse(
            status_code=500,
            content={
                "detail": str(exc),
                "type": type(exc).__name__
            }
        )
```

### Testing Requirements

#### Unit Tests (create `tests/test_circuit_breaker.py`):
```python
import pytest
import asyncio
from app.core.circuit_breaker import CircuitBreaker

@pytest.mark.asyncio
async def test_circuit_breaker_race_condition():
    """Test that state transitions are atomic"""
    cb = CircuitBreaker(failure_threshold=2)

    # Simulate concurrent failures
    async def failing_operation():
        raise Exception("Simulated failure")

    # Run 10 concurrent operations
    tasks = [cb.call(failing_operation) for _ in range(10)]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # All should fail consistently, no race condition
    assert all(isinstance(r, Exception) for r in results)
    assert cb.state_manager.failure_count == 10  # All counted

@pytest.mark.asyncio
async def test_websocket_timeout():
    """Test WebSocket timeout enforcement"""
    # Test implementation
    pass

def test_random_not_predictable():
    """Test that track generation is not predictable"""
    # Generate two tracks, should be different
    track1 = generate_track()
    track2 = generate_track()
    assert track1 != track2
```

#### Security Tests (create `tests/test_security.py`):
```python
def test_redos_protection():
    """Test ReDoS protection"""
    from app.security import PATH_PATTERN
    import time

    # Malicious input that would cause backtracking
    evil_input = "/" + "a" * 10000 + "!"

    start = time.time()
    result = PATH_PATTERN.match(evil_input)
    duration = time.time() - start

    # Should complete quickly (< 100ms)
    assert duration < 0.1
    assert result is None  # Invalid path

def test_error_message_sanitization():
    """Test that error messages don't leak details in production"""
    # Test implementation
    pass
```

### Success Criteria
- [ ] All circuit breaker state transitions are atomic
- [ ] No global random seed usage
- [ ] All randomness uses `secrets` module
- [ ] WebSocket connections have 30s timeout
- [ ] WebSocket rate limiting active (5 connections per IP per minute)
- [ ] ReDoS regex fixed with atomic groups
- [ ] Error messages sanitized in production
- [ ] All unit tests passing
- [ ] All security tests passing

---

## PR2: Frontend Security Fixes

**Branch**: `security/frontend-fixes`
**Priority**: P0 (Critical)
**Estimated Effort**: 2-3 days
**Dependencies**: None

### Scope
Fix 7 critical and high-severity frontend security issues:
1. XSS via innerHTML
2. Open redirect vulnerability
3. Missing CSP meta tag
4. Production console logging
5. WebSocket URL validation
6. Unvalidated API responses
7. DevTools exposure

### Files to Modify
- `durable-code-app/frontend/src/core/errors/GlobalErrorHandler.ts`
- `durable-code-app/frontend/src/components/common/FeatureCard/FeatureCard.tsx`
- `durable-code-app/frontend/index.html`
- `durable-code-app/frontend/src/utils/logger.ts` (new)
- `durable-code-app/frontend/src/features/racing/types/track.schema.ts` (new)
- `durable-code-app/frontend/src/app/AppProviders.tsx`
- ~20 files with console.log statements

### Implementation Steps

#### Step 1: Install Zod Dependency

```bash
cd durable-code-app/frontend
npm install zod
```

#### Step 2: Replace innerHTML with DOM APIs

**File**: `GlobalErrorHandler.ts:234,284`

```typescript
// BEFORE (XSS vulnerable):
notification.innerHTML = `
  <div>${this.sanitizeErrorMessage(error.message)}</div>
`;

// AFTER (safe):
const notification = document.createElement('div');
notification.id = 'global-error-notification';
notification.style.cssText = `/* existing styles */`;

const icon = document.createElement('span');
icon.textContent = '⚠️';
icon.style.fontSize = '24px';

const messageContainer = document.createElement('div');

const titleDiv = document.createElement('div');
titleDiv.textContent = 'An error occurred';
titleDiv.style.fontWeight = '600';

const errorText = document.createElement('div');
errorText.textContent = this.sanitizeErrorMessage(error.message);
errorText.style.fontSize = '14px';

messageContainer.appendChild(titleDiv);
messageContainer.appendChild(errorText);
notification.appendChild(icon);
notification.appendChild(messageContainer);

document.body.appendChild(notification);
```

#### Step 3: Add URL Validation

**File**: `FeatureCard.tsx:37`

```typescript
const isValidUrl = (url: string): boolean => {
  try {
    const parsed = new URL(url, window.location.origin);
    if (!['http:', 'https:'].includes(parsed.protocol)) {
      return false;
    }
    return true;
  } catch {
    return false;
  }
};

const handleClick = () => {
  if (onClick) {
    onClick();
  } else if (linkHref) {
    if (isValidUrl(linkHref)) {
      if (linkHref.startsWith('/')) {
        navigate(linkHref);
      } else {
        window.location.href = linkHref;
      }
    } else {
      console.error('Invalid or unsafe URL prevented:', linkHref);
    }
  }
};
```

#### Step 4: Add CSP Meta Tag

**File**: `index.html`

```html
<head>
  <meta charset="UTF-8" />
  <meta http-equiv="Content-Security-Policy"
        content="default-src 'self';
                 script-src 'self' 'unsafe-inline' 'unsafe-eval';
                 style-src 'self' 'unsafe-inline';
                 img-src 'self' data: https:;
                 connect-src 'self' ws: wss: http://localhost:* https://localhost:*;
                 font-src 'self' data:;
                 frame-ancestors 'none';
                 base-uri 'self';
                 form-action 'self';">
  <!-- rest of head -->
</head>
```

#### Step 5: Create Environment-Aware Logger

**File**: `src/utils/logger.ts` (new file)

```typescript
type LogLevel = 'debug' | 'info' | 'warn' | 'error';

class SecureLogger {
  private isDevelopment = import.meta.env.DEV;

  debug(...args: unknown[]): void {
    if (this.isDevelopment) {
      console.debug(...args);
    }
  }

  info(...args: unknown[]): void {
    if (this.isDevelopment) {
      console.info(...args);
    }
  }

  warn(...args: unknown[]): void {
    if (this.isDevelopment) {
      console.warn(...args);
    } else {
      this.sendToLoggingService('warn', args);
    }
  }

  error(...args: unknown[]): void {
    if (this.isDevelopment) {
      console.error(...args);
    } else {
      this.sendToLoggingService('error', args);
    }
  }

  private sendToLoggingService(level: LogLevel, args: unknown[]): void {
    // TODO: Implement Sentry/DataDog integration
  }
}

export const logger = new SecureLogger();
```

#### Step 6: Replace All Console Statements

Replace in all ~20 files:
```typescript
// BEFORE:
console.error('[main.tsx] Error:', error);

// AFTER:
import { logger } from '@/utils/logger';
logger.debug('[main.tsx] Error:', error);
```

#### Step 7: Add API Response Validation with Zod

**File**: `src/features/racing/types/track.schema.ts` (new file)

```typescript
import { z } from 'zod';

const Point2DSchema = z.object({
  x: z.number(),
  y: z.number(),
});

const TrackBoundarySchema = z.object({
  outer: z.array(Point2DSchema),
  inner: z.array(Point2DSchema),
});

export const TrackSchema = z.object({
  start_position: Point2DSchema,
  boundaries: TrackBoundarySchema,
  track_width: z.number().min(40).max(200),
  width: z.number().min(400).max(2000),
  height: z.number().min(300).max(1500),
});

export type Track = z.infer<typeof TrackSchema>;
```

**File**: `useRacingGame.ts:115,427`

```typescript
import { TrackSchema } from '../types/track.schema';

// BEFORE:
const trackData: Track = await response.json();
setTrack(trackData);

// AFTER:
const trackData = await response.json();
try {
  const validatedTrack = TrackSchema.parse(trackData);
  setTrack(validatedTrack);
} catch (error) {
  logger.error('Invalid track data received:', error);
  throw new Error('Received invalid track data from server');
}
```

#### Step 8: Disable DevTools in Production

**File**: `AppProviders.tsx:44`

```typescript
{import.meta.env.DEV && (
  <ReactQueryDevtools initialIsOpen={false} />
)}
```

**File**: `appStore.ts:14`, `demoStore.ts`, `navigationStore.ts`

```typescript
const middleware = import.meta.env.DEV ? devtools : (f: any) => f;

export const useAppStore = create<AppState>()(
  middleware(
    (set) => ({ /* ... */ }),
    { name: 'app-store' },
  ),
);
```

### Testing Requirements

#### Unit Tests:
```typescript
describe('URL Validation', () => {
  it('should allow valid HTTP URLs', () => {
    expect(isValidUrl('http://example.com')).toBe(true);
  });

  it('should block javascript: URLs', () => {
    expect(isValidUrl('javascript:alert(1)')).toBe(false);
  });

  it('should block data: URLs', () => {
    expect(isValidUrl('data:text/html,<script>alert(1)</script>')).toBe(false);
  });
});

describe('Logger', () => {
  it('should not log in production', () => {
    // Mock production environment
    // Test implementation
  });
});

describe('Track Schema', () => {
  it('should validate correct track data', () => {
    const valid = { /* valid track */ };
    expect(() => TrackSchema.parse(valid)).not.toThrow();
  });

  it('should reject invalid track data', () => {
    const invalid = { /* invalid track */ };
    expect(() => TrackSchema.parse(invalid)).toThrow();
  });
});
```

#### Security Tests:
```typescript
describe('XSS Protection', () => {
  it('should not execute XSS in error messages', () => {
    const xssPayload = '<img src=x onerror=alert(1)>';
    // Test that payload is displayed as text, not executed
  });
});

describe('CSP', () => {
  it('should have CSP meta tag', () => {
    const csp = document.querySelector('meta[http-equiv="Content-Security-Policy"]');
    expect(csp).toBeTruthy();
  });
});
```

### Success Criteria
- [ ] No innerHTML usage in codebase
- [ ] All URLs validated before navigation
- [ ] CSP meta tag present and valid
- [ ] Zero console logs in production build
- [ ] All API responses validated with Zod
- [ ] DevTools disabled in production
- [ ] All tests passing
- [ ] npm run build succeeds

---

## PR3: Python Code Quality Improvements

**Branch**: `refactor/python-quality`
**Priority**: P1 (High)
**Estimated Effort**: 3-4 days
**Dependencies**: PR1 (for circuit breaker fixes)

### Scope
Refactor Python codebase to improve maintainability:
1. Split racing.py god object (824 lines)
2. Reduce cyclomatic complexity to ≤10
3. Extract magic numbers to constants
4. Create domain types (Point, TrackConfig)
5. Fix broad exception handling
6. Implement State Machine pattern for WebSocket

### Files to Create/Modify
- `durable-code-app/backend/app/racing/` (new package)
  - `__init__.py`
  - `api/routes.py`
  - `domain/generator.py`
  - `geometry/curves.py`
  - `geometry/boundaries.py`
  - `algorithms/smoothing.py`
  - `types.py`
- `durable-code-app/backend/app/oscilloscope.py` (refactor)
- `durable-code-app/backend/tests/racing/` (new tests)

### Implementation Steps

See AI_CONTEXT.md for detailed refactoring patterns.

#### Step 1: Create Domain Types

**File**: `app/racing/types.py` (new)

```python
from dataclasses import dataclass
from typing import List

@dataclass(frozen=True)
class Point:
    """2D point with immutable coordinates"""
    x: float
    y: float

    def distance_to(self, other: 'Point') -> float:
        return ((self.x - other.x)**2 + (self.y - other.y)**2)**0.5

@dataclass(frozen=True)
class TrackConfig:
    """Configuration for track generation"""
    track_width: int = 80
    num_control_points: int = 8
    min_radius: float = 100.0
    smoothing_iterations: int = 3
    boundary_offset: float = 5.0
```

#### Step 2: Split racing.py into Package

Create modular structure - see PR3 section in original roadmap for full details.

#### Step 3: Extract Magic Numbers

```python
# BEFORE:
if distance < 100:
    return False

# AFTER:
MIN_TRACK_RADIUS = 100.0

if distance < MIN_TRACK_RADIUS:
    return False
```

#### Step 4: Implement State Machine for WebSocket

**File**: `app/oscilloscope.py`

```python
from enum import Enum
from dataclasses import dataclass

class WebSocketState(Enum):
    CONNECTING = "connecting"
    CONNECTED = "connected"
    STREAMING = "streaming"
    PAUSED = "paused"
    DISCONNECTING = "disconnecting"
    DISCONNECTED = "disconnected"

class WebSocketStateMachine:
    """State machine for WebSocket lifecycle"""
    def __init__(self):
        self.state = WebSocketState.CONNECTING
        self.transitions = {
            WebSocketState.CONNECTING: [WebSocketState.CONNECTED, WebSocketState.DISCONNECTED],
            WebSocketState.CONNECTED: [WebSocketState.STREAMING, WebSocketState.DISCONNECTING],
            WebSocketState.STREAMING: [WebSocketState.PAUSED, WebSocketState.DISCONNECTING],
            WebSocketState.PAUSED: [WebSocketState.STREAMING, WebSocketState.DISCONNECTING],
            WebSocketState.DISCONNECTING: [WebSocketState.DISCONNECTED],
        }

    def transition_to(self, new_state: WebSocketState) -> None:
        if new_state not in self.transitions[self.state]:
            raise ValueError(f"Invalid transition from {self.state} to {new_state}")
        self.state = new_state
```

### Testing Requirements
- [ ] All functions complexity ≤10
- [ ] No functions >50 lines
- [ ] racing module split into package
- [ ] All magic numbers extracted
- [ ] Domain types created
- [ ] State machine tests passing
- [ ] All original tests still passing

### Success Criteria
- [ ] racing.py no longer exists (split into package)
- [ ] All functions pass complexity checks
- [ ] Domain types used throughout
- [ ] State machine pattern implemented
- [ ] All tests passing

---

## PR4: TypeScript/React Quality Improvements

**Branch**: `refactor/react-quality`
**Priority**: P2 (Medium)
**Estimated Effort**: 2 days
**Dependencies**: PR2 (for error boundaries)

### Scope
Improve React code quality:
1. Split useRacingGame hook (507 lines)
2. Add error boundaries at Suspense
3. Fix direct DOM manipulation
4. Add WebSocket cleanup
5. Fix React keys

### Files to Modify
- `durable-code-app/frontend/src/features/racing/hooks/` (split into 5 files)
- `durable-code-app/frontend/src/pages/HomePage/HomePage.tsx`
- `durable-code-app/frontend/src/features/repository/components/RepositoryTab/RepositoryTab.tsx`
- `durable-code-app/frontend/src/features/demo/services/websocketSingleton.ts`

### Implementation Steps

#### Step 1: Split useRacingGame Hook

Create 4 specialized hooks:
- `useRacingPhysics.ts` - Physics engine
- `useRacingInput.ts` - Input handling
- `useRacingTiming.ts` - Lap timing
- `useRacingAudio.ts` - Sound management

```typescript
// useRacingGame.ts (orchestrator)
export function useRacingGame() {
  const physics = useRacingPhysics(car, track);
  const input = useRacingInput();
  const timing = useRacingTiming(checkpoints);
  const audio = useRacingAudio(events);

  return { physics, input, timing, audio };
}
```

#### Step 2: Add Error Boundaries

**File**: `HomePage.tsx:90`

```typescript
<Suspense fallback={<LoadingSpinner />}>
  <ErrorBoundary FallbackComponent={ErrorFallback}>
    <ActiveTabComponent />
  </ErrorBoundary>
</Suspense>
```

#### Step 3: Fix DOM Manipulation

**File**: `RepositoryTab.tsx:93-122`

Use CSS classes instead of direct style manipulation:

```css
.modal-open {
  overflow: hidden;
  position: fixed;
  width: 100%;
}
```

```typescript
useEffect(() => {
  if (selectedRepoItem) {
    document.body.classList.add('modal-open');
    return () => document.body.classList.remove('modal-open');
  }
}, [selectedRepoItem]);
```

#### Step 4: Add WebSocket Cleanup

**File**: `websocketSingleton.ts`

```typescript
export function disposeWebSocketSingleton(): void {
  if (instance) {
    instance.disconnect();
    instance = null;
  }
}
```

### Testing Requirements
- [ ] All hooks <200 lines
- [ ] Error boundaries at Suspense
- [ ] No direct DOM manipulation
- [ ] WebSocket cleanup working
- [ ] All tests passing

### Success Criteria
- [ ] useRacingGame split into 4 hooks
- [ ] Error boundaries added
- [ ] CSS-based modal styling
- [ ] WebSocket disposal implemented
- [ ] All tests passing

---

## PR5: AWS Infrastructure Security

**Branch**: `security/aws-infrastructure`
**Priority**: P0 (Critical)
**Estimated Effort**: 3-4 days
**Dependencies**: None

### Scope
Harden AWS infrastructure:
1. Remove hardcoded account ID
2. Scope all IAM permissions
3. Add MFA protection
4. Enable ALB logs
5. Add KMS encryption (CloudWatch, ECR)
6. Add VPC Flow Logs
7. Implement Secrets Manager
8. Deploy AWS WAF

### Files to Modify
- `infra/scripts/deploy-app.sh`
- `infra/terraform/workspaces/bootstrap/github-oidc.tf`
- `infra/terraform/workspaces/runtime/alb.tf`
- `infra/terraform/workspaces/runtime/ecs.tf`
- `infra/terraform/workspaces/base/ecr.tf`
- `infra/terraform/workspaces/base/networking.tf`
- `infra/terraform/workspaces/runtime/waf.tf` (new)

### Implementation Steps

See original PR5 roadmap for complete Terraform code examples.

#### Step 1: Remove Hardcoded Account ID

**File**: `deploy-app.sh:22`

```bash
# BEFORE:
AWS_ACCOUNT_ID="449870229058"

# AFTER:
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
```

#### Step 2: Scope IAM Permissions

**File**: `github-oidc.tf:66-106`

```hcl
Resource = [
  "arn:aws:ecr:${var.aws_region}:${data.aws_caller_identity.current.account_id}:repository/${var.project_name}-*"
]
```

#### Step 3-8: See detailed Terraform code in original PR5 document

### Testing Requirements
- [ ] terraform plan succeeds
- [ ] terraform apply succeeds
- [ ] VPC Flow Logs appearing in CloudWatch
- [ ] ALB logs in S3
- [ ] KMS encryption verified
- [ ] WAF rules blocking test traffic

### Success Criteria
- [ ] No hardcoded credentials
- [ ] All IAM scoped to resources
- [ ] KMS encryption everywhere
- [ ] VPC Flow Logs active
- [ ] ALB logs enabled
- [ ] Secrets Manager integrated
- [ ] AWS WAF deployed

---

## PR6: Final Security Evaluation

**Branch**: `evaluation/final-security-review`
**Priority**: P0 (Validation)
**Estimated Effort**: 1 day
**Dependencies**: PR1, PR2, PR3, PR4, PR5 all merged

### Scope
Re-run the comprehensive 5-agent security analysis to validate all improvements.

### Evaluation Prompt

```
You are a team of five expert security and code quality agents performing a FINAL evaluation after security remediation.

Previous analysis found 67 issues (8 critical, 16 high, 27 medium, 16 low).
All issues have been addressed in PRs 1-5.

**TASK**: Re-run the exact same deep analysis from the initial review:

AGENT 1 (Python Backend Security):
- Analyze all Python backend files for security vulnerabilities
- Check if race conditions, weak RNG, global state issues are fixed
- Verify WebSocket timeouts and rate limiting implemented
- Look for any NEW vulnerabilities introduced by fixes

AGENT 2 (Frontend Security):
- Analyze TypeScript/React files for security issues
- Verify innerHTML removed, URL validation added, CSP implemented
- Check console logging removed, DevTools disabled in production
- Look for any NEW vulnerabilities

AGENT 3 (Python Code Quality):
- Analyze Python code for quality issues
- Verify cyclomatic complexity ≤10, function length ≤50 lines
- Check magic numbers extracted, broad exceptions fixed
- Verify racing.py properly split into modules

AGENT 4 (TypeScript/React Quality):
- Analyze React code quality
- Verify large hooks split, error boundaries added
- Check DOM manipulation removed
- Verify proper React patterns

AGENT 5 (AWS Infrastructure Security):
- Analyze Terraform and deployment scripts
- Verify IAM wildcards removed, KMS encryption added
- Check VPC Flow Logs, WAF, Secrets Manager implemented
- Verify no hardcoded credentials

**OUTPUT FORMAT**:
For each agent, provide:

1. **Issues Resolved**: Count of original issues now fixed
2. **Remaining Issues**: Any original issues still present
3. **New Issues Found**: Any new problems introduced
4. **Security Grade**: Updated letter grade (A+ to F)
5. **Recommendations**: Any additional improvements

**FINAL SUMMARY**:
- Overall security grade (before vs after)
- Total issues resolved
- Key improvements made
- Production readiness assessment
```

### Implementation Steps

1. Deploy 5 agents in parallel with evaluation prompt
2. Compile results into `FINAL-EVALUATION-RESULTS.md`
3. Create before/after comparison report
4. Generate production readiness assessment

### Success Criteria
- [ ] Overall grade ≥ A-
- [ ] Zero critical issues
- [ ] <3 high-severity issues
- [ ] <10 total issues
- [ ] Production deployment approved

---

## Implementation Guidelines

### Code Standards
- Follow existing code style and patterns
- Use type hints in Python
- Use TypeScript strict mode
- Pass all linting checks
- No skipping of linting rules without approval

### Testing Requirements
- Unit tests for all security fixes
- Integration tests for complex refactors
- Security tests with actual attack payloads
- Regression tests for bug fixes
- All tests must pass before merging

### Documentation Standards
- Update docstrings for refactored code
- Add comments explaining security decisions
- Document complex algorithms
- Update CHANGELOG.md for each PR

### Security Considerations
- Never skip security linting rules
- Test with actual attack vectors
- Validate all user input
- Sanitize all error messages
- Use secure defaults

### Performance Targets
- No performance degradation
- WebSocket latency <100ms
- Track generation <500ms
- Bundle size increase <50KB

## Rollout Strategy

### Phase 1: Critical Security (Week 1)
- Deploy PR1, PR2, PR5 in parallel
- Test in dev environment
- Deploy to production ASAP

### Phase 2: Code Quality (Week 2)
- Deploy PR3, PR4 in parallel
- Extensive testing
- Deploy to production

### Phase 3: Validation (Week 2-3)
- Run PR6 evaluation
- Create final report
- Get production approval

## Success Metrics

### Launch Metrics
- All 6 PRs merged
- Zero critical issues
- Grade A or higher
- Production deployment successful

### Ongoing Metrics
- Zero security incidents
- Code quality maintained
- Test coverage >80%
- No regressions introduced
