# How to Implement Backend Error Handling

## Overview
This guide covers implementing robust error handling in FastAPI backend applications, including structured exceptions, retry logic, circuit breakers, and global exception handlers.

## Key Principles
1. **No broad exception catching** - Always catch specific exception types
2. **Structured error responses** - Consistent format with error codes
3. **Retry logic for external calls** - Exponential backoff for resilience
4. **Circuit breakers** - Prevent cascading failures
5. **Proper error logging** - Log errors without exposing internals

## Implementation Steps

### 1. Create Exception Hierarchy

Use the `backend-exception-hierarchy.py.template`:

```python
# app/core/exceptions.py
from typing import Any, Optional
from fastapi import status

class AppExceptionError(Exception):
    """Base exception with structured error info."""
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}

# Create specific exceptions
class ValidationError(AppExceptionError):
    """For input validation failures."""
    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR",
            details=details,
        )
```

### 2. Add Global Exception Handlers

In your FastAPI app:

```python
# app/main.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from .core.exceptions import AppExceptionError, ValidationError

app = FastAPI()

@app.exception_handler(AppExceptionError)
async def app_exception_handler(request: Request, exc: AppExceptionError):
    """Handle application-specific exceptions."""
    logger.error(f"Application error: {exc.error_code}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "details": exc.details,
        },
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions safely."""
    logger.exception(f"Unexpected error on {request.url.path}")
    # Don't expose internal details
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_ERROR",
            "message": "An unexpected error occurred",
            "details": {},
        },
    )
```

### 3. Replace Broad Exception Catching

**Bad (broad catching):**
```python
try:
    result = await process_data()
except Exception as e:  # Too broad!
    logger.error(f"Error: {e}")
```

**Good (specific catching):**
```python
try:
    result = await process_data()
except (ConnectionError, TimeoutError) as e:
    logger.error(f"Connection error: {e}")
    raise ExternalServiceError("Service unavailable")
except (ValueError, TypeError) as e:
    logger.error(f"Data error: {e}")
    raise ValidationError("Invalid data format")
except asyncio.CancelledError:
    logger.debug("Operation cancelled")
    raise  # Re-raise for proper cleanup
```

### 4. Add Retry Logic

Use the `backend-retry-logic.py.template`:

```python
# app/core/retry.py
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=1, max=10),
    retry=retry_if_exception_type(ExternalServiceError)
)
async def fetch_external_data():
    """Automatically retries on ExternalServiceError."""
    response = await make_api_call()
    if not response.ok:
        raise ExternalServiceError("API call failed")
    return response.json()
```

### 5. Implement Circuit Breakers

For services that may fail:

```python
# app/core/circuit_breaker.py
class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout_duration=60):
        self.failure_threshold = failure_threshold
        self.timeout_duration = timeout_duration
        self.failure_count = 0
        self.state = "CLOSED"

    async def call(self, func, *args, **kwargs):
        if self.state == "OPEN":
            raise ExternalServiceError("Circuit breaker is open")

        try:
            result = await func(*args, **kwargs)
            self.failure_count = 0  # Reset on success
            return result
        except Exception as e:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
            raise
```

### 6. Enable Linting Checks

Ensure broad exception catching is detected:

```toml
# pyproject.toml
[tool.pylint.messages_control]
disable = [
    # Remove W0718 from disable list!
    # "W0718",  # broad-exception-caught
]
```

### 7. Add Error Handling Linting Rules

Create custom linting rules:

```python
# tools/design_linters/rules/error_handling/resilience_rules.py
class NoBroadExceptionsRule(Rule):
    """Detect and prevent broad exception catching."""

    def check(self, tree: ast.AST, filepath: str, source: str):
        violations = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                if node.type and isinstance(node.type, ast.Name):
                    if node.type.id in ["Exception", "BaseException"]:
                        violations.append(
                            Violation(
                                rule=self.name,
                                filepath=filepath,
                                line=node.lineno,
                                message="Use specific exception types",
                                severity="error"
                            )
                        )
        return violations
```

## Testing Error Handling

```python
# test/test_error_handling.py
def test_validation_error():
    exc = ValidationError("Invalid input", details={"field": "email"})
    assert exc.status_code == 422
    assert exc.error_code == "VALIDATION_ERROR"

@pytest.mark.asyncio
async def test_retry_logic():
    call_count = 0

    @retry_on_external_error
    async def flaky_operation():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ExternalServiceError("Failed")
        return "success"

    result = await flaky_operation()
    assert result == "success"
    assert call_count == 3  # Retried twice
```

## Common Patterns

### Pattern 1: External API Calls
```python
@retry_on_connection_error
async def call_external_api(url: str):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
    except httpx.TimeoutException:
        raise ExternalServiceError("API timeout")
    except httpx.HTTPStatusError as e:
        raise ExternalServiceError(f"API error: {e.response.status_code}")
```

### Pattern 2: Database Operations
```python
async def get_user(user_id: str):
    try:
        user = await db.fetch_one(query, {"id": user_id})
        if not user:
            raise ResourceNotFoundError("User not found", resource_id=user_id)
        return user
    except DatabaseError as e:
        logger.error(f"Database error: {e}")
        raise ServiceError("Database operation failed")
```

### Pattern 3: WebSocket Error Handling
```python
try:
    while True:
        message = await websocket.receive_text()
        await process_message(message)
except WebSocketDisconnect:
    logger.debug("WebSocket disconnected")
except (ValueError, TypeError) as e:
    logger.error(f"Invalid message: {e}")
    await websocket.send_json({"error": "Invalid message format"})
```

## Checklist

- [ ] No `except Exception:` or `except BaseException:` in code
- [ ] All exceptions inherit from base exception class
- [ ] Global exception handlers configured
- [ ] Retry logic on external operations
- [ ] Circuit breakers for critical services
- [ ] Error logging without exposing internals
- [ ] W0718 linting check enabled
- [ ] Tests for error handling paths
- [ ] Structured error responses with codes
- [ ] Proper cleanup in exception handlers

## Dependencies

Add to `pyproject.toml`:
```toml
[tool.poetry.dependencies]
tenacity = "^8.2.3"  # For retry logic
```

## Related Files
- `app/core/exceptions.py` - Exception hierarchy
- `app/core/retry.py` - Retry decorators
- `app/core/circuit_breaker.py` - Circuit breaker implementation
- `app/main.py` - Global exception handlers
- `.ai/templates/backend-exception-hierarchy.py.template`
- `.ai/templates/backend-retry-logic.py.template`
