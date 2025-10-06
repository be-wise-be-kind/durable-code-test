# How to Add a New API Endpoint

**Purpose**: Step-by-step guide for adding new API endpoints to the FastAPI backend with automatic documentation

**Scope**: FastAPI backend development, REST API creation, endpoint documentation, request/response handling

**Overview**: Comprehensive guide for adding new API endpoints to the FastAPI backend that ensures proper
    integration with the auto-generated documentation system. Covers endpoint creation patterns,
    request/response models, validation, error handling, and testing approaches that maintain
    consistency with existing API architecture and documentation standards.

**Dependencies**: FastAPI backend, Python type hints, Pydantic models, REST API knowledge

**Exports**: API endpoint creation workflow, documentation patterns, testing approaches

**Related**: FastAPI backend documentation, API design standards, testing guides

**Implementation**: FastAPI router patterns, Pydantic validation, endpoint documentation, testing integration

---

This guide provides step-by-step instructions for adding new API endpoints to the FastAPI backend with proper documentation and testing.

## Prerequisites

- FastAPI backend running at http://localhost:8000
- Understanding of Python type hints
- Basic knowledge of REST API principles

## Steps to Add a New API Endpoint

### 1. Create or Update Your Router Module

Create a new Python module in `durable-code-app/backend/app/` or add to an existing one.

```python
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any

# Create a router with prefix and tags
router = APIRouter(
    prefix="/api/your_feature",
    tags=["your_feature"],  # This groups endpoints in the docs
)
```

### 2. Define Pydantic Models (Optional but Recommended)

Define request and response models for type safety and automatic documentation:

```python
class RequestModel(BaseModel):
    """Request model for your endpoint."""
    field1: str
    field2: int

class ResponseModel(BaseModel):
    """Response model for your endpoint."""
    result: str
    status: str
```

### 3. Create Your Endpoint

Add your endpoint to the router:

```python
@router.get("/config", tags=["your_feature"])
async def get_config() -> dict[str, Any]:
    """Get configuration for your feature.

    This docstring appears in the API documentation.

    Returns:
        Configuration dictionary with supported parameters.
    """
    return {
        "setting1": "value1",
        "setting2": "value2"
    }

@router.post("/action", response_model=ResponseModel)
async def perform_action(request: RequestModel) -> ResponseModel:
    """Perform an action with the given parameters.

    Args:
        request: The request parameters

    Returns:
        ResponseModel: The action result
    """
    # Your business logic here
    return ResponseModel(result="success", status="completed")
```

### 4. Register the Router in main.py

**CRITICAL STEP**: Your endpoints won't appear in the documentation unless you register the router in `main.py`:

```python
# In durable-code-app/backend/app/main.py
from .your_module import router as your_feature_router

# After app initialization
app.include_router(your_feature_router)
```

### 5. WebSocket Endpoints (Special Case)

WebSocket endpoints need special handling because OpenAPI 3.0 doesn't natively support WebSockets. Best practice is to create a companion GET endpoint that documents the WebSocket interface:

```python
# The actual WebSocket endpoint
@router.websocket("/stream")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time streaming."""
    await websocket.accept()
    # WebSocket logic here

# Document the WebSocket endpoint with a GET endpoint
@router.get("/stream/info")
async def get_stream_info():
    """Get information about the WebSocket streaming endpoint.

    Returns connection details, message formats, and available commands.
    """
    return {
        "endpoint": "ws://localhost:8000/api/your_feature/stream",
        "protocol": "WebSocket",
        "commands": {
            "start": {"description": "Start streaming", "example": {...}},
            "stop": {"description": "Stop streaming", "example": {...}}
        },
        "response_format": {
            "field1": "description",
            "field2": "description"
        }
    }
```

This approach ensures users can discover and understand your WebSocket endpoints through the API documentation.

### 6. Excluding Endpoints from Documentation

To exclude certain endpoints (like health checks) from the documentation:

```python
@router.get("/health", include_in_schema=False)
async def health_check():
    """This won't appear in /docs."""
    return {"status": "healthy"}
```

## Best Practices

### 1. Always Use Tags

Tags group related endpoints in the documentation:

```python
router = APIRouter(
    prefix="/api/feature",
    tags=["feature"],  # Groups endpoints in docs
)
```

### 2. Provide Comprehensive Documentation

Use docstrings and response models:

```python
@router.get(
    "/items/{item_id}",
    summary="Get an item by ID",
    description="Retrieve a specific item from the database",
    response_description="The requested item",
    responses={
        200: {"description": "Item found"},
        404: {"description": "Item not found"}
    }
)
```

### 3. Use Type Hints

Type hints enable automatic validation and documentation:

```python
async def get_items(
    skip: int = Query(0, description="Number of items to skip"),
    limit: int = Query(10, description="Number of items to return"),
) -> list[ItemModel]:
    pass
```

### 4. Standard Response Models

Create consistent error response models:

```python
class ErrorResponse(BaseModel):
    error: str
    error_code: str
    timestamp: datetime
```

## Using the Template

Use the FastAPI endpoint template located at `.ai/templates/fastapi-endpoint.py.template` for consistency:

```bash
# Copy and customize the template
cp .ai/templates/fastapi-endpoint.py.template durable-code-app/backend/app/your_endpoint.py
```

## Testing Your Endpoint

### 1. Check Documentation

Visit http://localhost:8000/docs to see your endpoint in the interactive documentation.

### 2. Test with curl

```bash
# GET request
curl http://localhost:8000/api/your_feature/config

# POST request
curl -X POST http://localhost:8000/api/your_feature/action \
  -H "Content-Type: application/json" \
  -d '{"field1": "value", "field2": 123}'
```

### 3. Test with the Interactive Docs

Use the "Try it out" button in the Swagger UI at /docs.

## Common Issues and Solutions

### Endpoint Not Appearing in Docs

1. **Check router registration**: Ensure `app.include_router(your_router)` is in main.py
2. **Check tags**: Verify tags are properly set on both router and endpoints
3. **Check include_in_schema**: Make sure it's not set to False
4. **Restart server**: Changes require server restart

### WebSocket Endpoints

WebSocket endpoints won't appear directly in OpenAPI docs because OpenAPI 3.0 doesn't support WebSockets. Instead:
1. Create a companion GET endpoint that documents the WebSocket interface (see Section 5 above)
2. The GET endpoint will appear in /docs and provide all necessary information about the WebSocket
3. Test WebSockets with a client tool or custom frontend code, not through the Swagger UI

### CORS Issues

For frontend-backend communication, ensure CORS is properly configured in main.py:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Example: Adding Oscilloscope Endpoints

Here's how the oscilloscope endpoints were properly added:

1. Created `oscilloscope.py` with router and endpoints
2. Added regular GET endpoint for configuration (appears in docs)
3. Added WebSocket endpoint for streaming (appears in docs but not testable there)
4. Registered router in main.py: `app.include_router(oscilloscope_router)`
5. Added proper tags and documentation

## Checklist

- [ ] Created router with appropriate prefix and tags
- [ ] Defined Pydantic models for requests/responses
- [ ] Added comprehensive docstrings
- [ ] Used proper type hints
- [ ] Registered router in main.py
- [ ] Tested endpoint appears in /docs
- [ ] Verified endpoint functionality
- [ ] Added error handling
- [ ] Updated any relevant tests

## Related Documentation

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [OpenAPI Specification](https://swagger.io/specification/)
- Project template: `.ai/templates/fastapi-endpoint.py.template`
