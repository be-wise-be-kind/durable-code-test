# How to Write File Headers

**Purpose**: Step-by-step guide for creating proper file headers before writing any code

**Scope**: All file types (Python, TypeScript, YAML, Markdown, etc.)

**Overview**: File headers provide essential context for AI agents and developers to quickly understand a file's purpose without reading the entire implementation. This guide shows how to write comprehensive, atemporal headers following project standards.

---

## CRITICAL: Before Writing ANY File

**MANDATORY WORKFLOW:**

1. ✅ **STOP** - Don't start writing code yet
2. ✅ **READ** `.ai/docs/FILE_HEADER_STANDARDS.md` completely
3. ✅ **IDENTIFY** your file type (Python, TypeScript, YAML, Markdown)
4. ✅ **SELECT** the correct template for your file type
5. ✅ **WRITE** the header first
6. ✅ **VALIDATE** header has all mandatory fields
7. ✅ **THEN** write your code

**This workflow is NOT optional.** Header linters will block PRs with missing or incorrect headers.

## Why File Headers Matter

### For AI Agents
- **Instant context** - Understand purpose without reading 500 lines of code
- **Faster navigation** - Quickly identify if file is relevant to task
- **Reduced tokens** - Don't need to read entire file to understand it
- **Better decisions** - Know dependencies and exports before modifying

### For Developers
- **Quick orientation** - Understand unfamiliar code faster
- **Maintenance clarity** - Know what can/can't be changed
- **Dependency tracking** - See what this file relies on
- **API discovery** - Find exported functions/classes quickly

## Template Selection

### Python Files (.py)

**Use for**: Backend code, linting rules, scripts

**Template Location**: `.ai/docs/FILE_HEADER_STANDARDS.md` (Docstring format)

**Format**:
```python
"""
Purpose: Brief one-line description of why this file exists
Scope: What this file is responsible for
Overview: 3-5 sentence detailed explanation of what this file does and how it fits
    into the larger system. Explain key concepts and primary functionality.
Dependencies: List key external packages and internal modules this file relies on
Exports: Main classes, functions, constants provided by this file
Interfaces: Key APIs, methods, or protocols exposed to other modules
Implementation: Notable patterns, algorithms, or architectural decisions
"""
```

### TypeScript/JavaScript Files (.ts, .tsx, .js, .jsx)

**Use for**: React components, hooks, utilities, services

**Template Location**: `.ai/docs/FILE_HEADER_STANDARDS.md` (JSDoc format)

**Format**:
```typescript
/**
 * Purpose: Brief one-line description of why this file exists
 * Scope: What this file is responsible for
 * Overview: 3-5 sentence detailed explanation of what this file does and how it fits
 *     into the larger system. Explain key concepts and primary functionality.
 * Dependencies: List key external packages and internal modules this file relies on
 * Exports: Main components, hooks, functions, or types provided by this file
 * Props/Interfaces: For components - key props and their purposes
 * State/Behavior: For components - how the component behaves and manages state
 * Implementation: Notable patterns, algorithms, or architectural decisions
 */
```

### YAML Files (.yml, .yaml)

**Use for**: Configuration, CI/CD, Docker Compose, index files

**Template Location**: `.ai/docs/FILE_HEADER_STANDARDS.md` (Comment format)

**Format**:
```yaml
# Purpose: Brief one-line description of why this file exists
# Scope: What this file configures or defines
# Overview: 3-5 sentence detailed explanation of what this file does and how it fits
#     into the larger system. Explain key concepts and configuration purpose.
# Dependencies: Other files or services this configuration relies on
# Exports: Key sections or configurations provided by this file
# Environment: Where this configuration is used (dev, prod, CI/CD, etc.)
# Related: Other related configuration files or documentation
# Implementation: Notable configuration patterns or decisions
```

### Markdown Files (.md)

**Use for**: Documentation, guides, READMEs

**Template Location**: `.ai/docs/FILE_HEADER_STANDARDS.md` (Metadata format)

**Format**:
```markdown
# File Title

**Purpose**: Brief one-line description

**Scope**: What this document covers

**Overview**: 3-5 sentence detailed explanation...
```

## Mandatory Fields

Every file header MUST include:

### 1. Purpose (Required)
**What**: One-line answer to "Why does this file exist?"

❌ **Bad**: "Contains utility functions"
✅ **Good**: "Centralized error handling utilities for backend API with structured logging"

❌ **Bad**: "User component"
✅ **Good**: "React component displaying user profile with edit capabilities and role badges"

### 2. Scope (Required)
**What**: Boundaries - what this file covers and what it doesn't

❌ **Bad**: "Handles users"
✅ **Good**: "User authentication and session management, excluding registration and password reset"

❌ **Bad**: "Data processing"
✅ **Good**: "Real-time oscilloscope data processing and circular buffer management, excluding WebSocket communication"

### 3. Overview (Required)
**What**: 3-5 sentences explaining the file in detail

**Should include**:
- Main functionality
- How it fits into the larger system
- Key concepts or patterns used
- Primary use cases

**Example (Good)**:
```
Overview: Provides WebSocket service for real-time oscilloscope data streaming. Handles
    connection lifecycle including automatic reconnection on disconnect, message queuing
    during reconnection, and graceful shutdown. Implements singleton pattern to prevent
    duplicate connections in React StrictMode. Primary communication channel between backend
    oscilloscope generator and frontend visualization components.
```

### 4. Dependencies (Required)
**What**: Key external packages and internal modules used

**Format**:
```
Dependencies: React, useState, useEffect, useCallback from react; WebSocket API;
    CircularBuffer from utils; OscilloscopeTypes from types; PerformanceMonitor from core
```

### 5. Exports (Required)
**What**: Main functions, classes, components, hooks, types provided

**For Python**:
```
Exports: UserService class, authenticate(), create_user(), delete_user(); UserNotFoundException
```

**For TypeScript**:
```
Exports: useOscilloscope hook, OscilloscopeState interface, OscilloscopeConfig type
```

### 6. Interfaces/Props (Situational)
**When**: For components, classes with public APIs

**What**: Key public methods, props, or API endpoints

**Example (React component)**:
```
Props: data (OscilloscopeData[]) - Array of data points to visualize;
    width (number) - Canvas width in pixels;
    height (number) - Canvas height in pixels;
    autoResize (boolean) - Whether to resize canvas automatically;
    onError (ErrorCallback) - Error handler callback
```

### 7. State/Behavior (Situational)
**When**: For stateful components or services

**What**: How state is managed and key behaviors

**Example**:
```
State/Behavior: Maintains connection state (connected, connecting, disconnected, error),
    automatic reconnection with exponential backoff, message queue for offline resilience,
    event-driven updates to prevent polling overhead
```

### 8. Implementation (Required)
**What**: Notable patterns, algorithms, or architectural decisions

**Example**:
```
Implementation: Uses singleton pattern to ensure single WebSocket instance across component
    re-mounts. Implements exponential backoff for reconnection (1s, 2s, 4s, 8s max).
    Circular buffer with Float32Array for memory efficiency. Event-driven state updates
    eliminate polling loops for 60fps performance.
```

## Atemporal Language Rule

**CRITICAL**: Headers must use atemporal language - avoid time-based references.

### ❌ Avoid These Temporal Words:
- "currently", "now", "today"
- "new", "old", "legacy", "updated"
- "recently", "soon", "planned", "future"
- Specific dates ("as of 2025", "added in Q1")
- "latest", "previous", "upcoming"

### ✅ Use Timeless Descriptions:

❌ **Bad**:
```
Purpose: New component for displaying user profiles, replacing the old ProfileCard
Overview: Recently updated to use modern React hooks. Currently implements lazy loading
    for images. Will soon add role-based access control.
```

✅ **Good**:
```
Purpose: Component for displaying user profiles with role badges and edit capabilities
Overview: Implements React hooks for state management and lazy loading for profile images.
    Displays user information with role-based styling and conditional edit interface based
    on permissions.
```

## Step-by-Step Writing Process

### Step 1: Understand Your File's Purpose

Before writing the header, answer these questions:
- Why does this file need to exist?
- What problem does it solve?
- Who/what will use this file?
- What are the key 2-3 things it does?

### Step 2: Identify Dependencies

Look at your imports/requires:
```python
# From these imports...
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.auth import require_auth
from app.services.user import UserService
```

```
# Extract for Dependencies field:
Dependencies: FastAPI (APIRouter, HTTPException), Pydantic (BaseModel),
    app.core.auth (require_auth), app.services.user (UserService)
```

### Step 3: Determine Exports

What does this file provide to others?

```python
# From code like this...
class UserAPI:
    def get_user(self, user_id: str): ...
    def update_user(self, user_id: str, data: dict): ...

router = APIRouter()

@router.get("/users/{user_id}")
async def get_user_endpoint(): ...
```

```
# Extract for Exports field:
Exports: UserAPI class with get_user() and update_user() methods;
    FastAPI router with /users endpoints
```

### Step 4: Write Implementation Notes

What's special about your implementation?
- Design patterns used (singleton, factory, observer)
- Performance optimizations
- Architectural decisions
- Algorithms or data structures

### Step 5: Review and Validate

Check your header against this checklist:
- [ ] Has all mandatory fields (Purpose, Scope, Overview, Dependencies, Exports, Implementation)
- [ ] Overview is 3-5 sentences minimum
- [ ] No temporal language ("currently", "new", dates)
- [ ] Dependencies list is complete
- [ ] Exports are clearly listed
- [ ] Implementation notes explain key decisions

## Complete Examples

### Example 1: Python Backend Service

```python
"""
Purpose: User authentication and session management service for backend API
Scope: Handles login, logout, session validation, and token refresh; excludes user
    registration and password reset which are handled by UserManagementService
Overview: Provides centralized authentication logic for the FastAPI backend. Implements
    JWT token generation and validation with refresh token rotation. Manages active
    session storage in Redis for fast validation and session invalidation. Integrates
    with UserRepository for credential verification and enforces rate limiting to prevent
    brute force attacks. Primary authentication layer for all protected API endpoints.
Dependencies: FastAPI (security utilities), PyJWT (token generation), Redis (session storage),
    bcrypt (password hashing), app.repositories.user (UserRepository),
    app.core.exceptions (AuthenticationError)
Exports: AuthService class with authenticate(), validate_token(), refresh_token(),
    logout() methods; AuthenticationError, InvalidTokenError exceptions
Interfaces: authenticate(email, password) -> TokenPair; validate_token(token) -> User;
    refresh_token(refresh_token) -> TokenPair; logout(user_id) -> None
Implementation: Uses JWT with RS256 algorithm for tokens. Access tokens expire in 15 minutes,
    refresh tokens in 7 days with automatic rotation. Session data stored in Redis with
    TTL matching token expiration. Implements exponential backoff rate limiting (3 failures
    = 15min lockout). Password verification uses bcrypt with cost factor 12.
"""
```

### Example 2: React Component

```typescript
/**
 * Purpose: Display real-time oscilloscope visualization with interactive canvas rendering
 * Scope: Handles canvas drawing, data visualization, and user interactions; excludes data
 *     fetching and WebSocket communication which are managed by useOscilloscope hook
 * Overview: Renders waveform data on HTML5 canvas with smooth 60fps animation. Supports
 *     auto-scaling, grid overlay, and cursor tracking for value inspection. Implements
 *     efficient rendering using requestAnimationFrame and partial canvas updates to minimize
 *     redraws. Responds to window resize events and provides accessible controls for
 *     screen readers. Primary visualization component for oscilloscope demo feature.
 * Dependencies: React (useRef, useEffect, useCallback), useCanvas hook for canvas management,
 *     useOscilloscope hook for data, OscilloscopeTypes for type definitions, CSS Modules
 *     for styling
 * Exports: OscilloscopeCanvas component
 * Props: width (number, required) - Canvas width in pixels;
 *     height (number, required) - Canvas height in pixels;
 *     autoResize (boolean, default true) - Resize canvas on window resize;
 *     showGrid (boolean, default true) - Display background grid;
 *     gridColor (string, default '#333') - Grid line color;
 *     waveColor (string, default '#0ff') - Waveform color;
 *     className (string, optional) - Additional CSS classes
 * State/Behavior: Maintains canvas context and rendering loop via useCanvas hook. Updates
 *     visualization when new data arrives through event-driven pattern. Handles mouse
 *     events for cursor tracking and value inspection. Cleanup on unmount stops animation
 *     loop and releases canvas context.
 * Implementation: Uses Float32Array in circular buffer for memory efficiency. Renders only
 *     changed portions of canvas when data updates (partial redraw optimization). Implements
 *     event-driven rendering instead of continuous polling to maintain 60fps with zero
 *     idle CPU usage. Canvas cleared and redrawn only on data events or user interactions.
 */
```

### Example 3: YAML Configuration

```yaml
# Purpose: Docker Compose configuration for development environment with hot reload
# Scope: Defines services, networks, and volumes for local development; excludes production
#     configuration which is in docker-compose.prod.yml
# Overview: Configures multi-container development environment with backend FastAPI service,
#     frontend React dev server, PostgreSQL database, and Redis cache. Enables hot module
#     replacement for both frontend and backend through volume mounts. Sets up networking
#     for inter-service communication and exposes ports for local access. Includes health
#     checks and restart policies for resilience during development.
# Dependencies: Docker Engine 20.10+, Docker Compose 2.0+, .env file for environment variables,
#     Dockerfiles in durable-code-app/backend and durable-code-app/frontend directories
# Exports: Four services (backend, frontend, postgres, redis), dev network, persistent volumes
#     for database and node_modules
# Environment: Local development only, not for staging or production deployment
# Related: docker-compose.prod.yml (production config), docker-compose.test.yml (testing config),
#     .env.example (environment variable template), Makefile (orchestration commands)
# Implementation: Uses bind mounts for source code to enable hot reload. Node_modules stored
#     in named volume to prevent host/container conflicts. PostgreSQL data persisted in named
#     volume across container restarts. Services connected via custom bridge network for DNS
#     resolution by service name. Health checks configured for all services with 30s intervals.
```

## Common Mistakes to Avoid

### Mistake 1: Vague Purpose
❌ "Utility functions"
✅ "Date formatting and timezone conversion utilities for international user display"

### Mistake 2: Missing Overview Detail
❌ "This file handles WebSocket connections"
✅ "Provides WebSocket service for real-time data streaming with automatic reconnection, message queuing, and graceful error recovery. Implements singleton pattern to prevent duplicate connections..."

### Mistake 3: Incomplete Dependencies
❌ "React, some utils"
✅ "React (useState, useEffect, useCallback), CircularBuffer from utils, WebSocket API, PerformanceMonitor from core"

### Mistake 4: Temporal Language
❌ "Recently updated to use modern hooks, will soon add caching"
✅ "Uses React hooks for state management with planned memoization patterns"

### Mistake 5: No Implementation Details
❌ "Standard implementation"
✅ "Implements exponential backoff for retries, uses Float32Array for memory efficiency, event-driven updates eliminate polling overhead"

## Integration with Workflow

### When Creating New Files

```bash
# 1. Decide to create file
# 2. Read FILE_HEADER_STANDARDS.md
# 3. Write header FIRST
# 4. Write code
# 5. Update exports if they changed
```

### When Modifying Existing Files

```bash
# 1. Read existing header
# 2. Update if scope/exports/implementation changed
# 3. Maintain atemporal language
# 4. Don't add "Updated:" with dates
```

## Validation

Your header is correct when:
- ✅ All mandatory fields present
- ✅ Overview is 3-5 sentences minimum
- ✅ No temporal language
- ✅ Dependencies are complete
- ✅ Exports match actual exports
- ✅ Implementation explains key decisions
- ✅ Correct format for file type

## Quick Reference

| File Type | Format | Key Fields |
|-----------|--------|------------|
| Python | Docstring | All mandatory + Interfaces |
| TypeScript | JSDoc | All mandatory + Props + State |
| React | JSDoc | All mandatory + Props + State/Behavior |
| YAML | Comments | All mandatory + Environment + Related |
| Markdown | Metadata | Purpose + Scope + Overview |

---

**Critical Reminder**: File headers are NOT optional. They are enforced by linters and required for all files. Write the header BEFORE writing code.

**Related Documentation**:
- `.ai/docs/FILE_HEADER_STANDARDS.md` - Complete standards and all templates
- `AGENTS.md` - Agent workflow requiring header creation
