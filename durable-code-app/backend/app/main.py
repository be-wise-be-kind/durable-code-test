"""Main FastAPI application entry point with middleware configuration.

Purpose: Main FastAPI application entry point with middleware configuration and error handling.
Scope: Application initialization, middleware setup, route registration, and global error handlers
Overview: This module serves as the central configuration point for the FastAPI application,
    establishing CORS policies, security middleware, rate limiting, and comprehensive error
    handling. It demonstrates durable code practices with strict complexity limits and type
    safety. The application includes health endpoints, WebSocket support for real-time features,
    and structured exception handling that provides consistent error responses across all endpoints.
Dependencies: FastAPI framework, loguru for logging, custom security and exception modules
Exports: create_app factory function that returns configured FastAPI application instance
Interfaces: Root endpoint (/), health check (/health), and mounted routers for feature modules
Implementation: Uses FastAPI's dependency injection, middleware stack, and exception handler registration
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from .core.exceptions import AppExceptionError, ValidationError
from .oscilloscope import router as oscilloscope_router
from .security import SecurityMiddleware, get_rate_limiter, get_security_config

# Application configuration
API_TITLE = "Durable Code API"
API_DESCRIPTION = "API demonstrating durable code practices"
API_VERSION = "1.0.0"

# CORS configuration - Secure settings
ALLOWED_ORIGINS: list[str] = [
    "http://localhost:3000",  # React dev server
    "http://localhost:5173",  # Vite dev server
]

# Security configuration
ALLOWED_METHODS: list[str] = ["GET", "POST", "DELETE"]  # Only specific methods
ALLOWED_HEADERS: list[str] = ["Content-Type", "Authorization"]  # Only necessary headers

# API Messages and Constants
WELCOME_MESSAGE = "Welcome to Durable Code API"
ROOT_ENDPOINT_DESCRIPTION = "Root endpoint returning welcome message."
HEALTH_ENDPOINT_PATH = "/health"
HEALTH_ENDPOINT_DESCRIPTION = "Health check endpoint for monitoring."
HEALTH_STATUS_OK = "healthy"

# HTTP Status Codes
HTTP_INTERNAL_SERVER_ERROR = 500


async def handle_app_exception(request: Request, exc: Exception) -> JSONResponse:
    """Handle application-specific exceptions with structured responses."""
    if not isinstance(exc, AppExceptionError):
        # Should never happen due to exception handler registration
        return await handle_general_exception(request, exc)

    logger.error(
        "Application error: %s",
        exc.error_code,
        extra={
            "error_code": exc.error_code,
            "status_code": exc.status_code,
            "details": exc.details,
            "path": request.url.path,
        },
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "details": exc.details,
        },
    )


async def handle_validation_error(request: Request, exc: Exception) -> JSONResponse:
    """Handle validation errors with detailed field information."""
    if not isinstance(exc, ValidationError):
        # Should never happen due to exception handler registration
        return await handle_general_exception(request, exc)

    logger.error(
        "Validation error on {path}",
        path=request.url.path,
        details=exc.details,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "details": exc.details,
        },
    )


async def handle_general_exception(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions safely without exposing internals."""
    logger.exception(
        "Unexpected error on %s",
        request.url.path,
        extra={"path": request.url.path, "method": request.method},
    )
    # Don't expose internal error details in production
    return JSONResponse(
        status_code=HTTP_INTERNAL_SERVER_ERROR,
        content={
            "error": "INTERNAL_ERROR",
            "message": "An unexpected error occurred",
            "details": {},
        },
    )


def _configure_exception_handlers(application: FastAPI) -> None:
    """Configure exception handlers for the application."""
    # Configure rate limiting
    from slowapi.errors import RateLimitExceeded

    from .security import RATE_LIMITER, _rate_limit_exceeded_handler

    application.state.limiter = RATE_LIMITER
    application.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Add global exception handlers
    application.add_exception_handler(AppExceptionError, handle_app_exception)
    application.add_exception_handler(ValidationError, handle_validation_error)
    application.add_exception_handler(Exception, handle_general_exception)


def _configure_middleware(application: FastAPI) -> None:
    """Configure middleware for the application."""
    # Add security middleware
    application.add_middleware(SecurityMiddleware)

    # Add CORS middleware with secure configuration
    application.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=False,  # Disable credentials for security
        allow_methods=ALLOWED_METHODS,  # Only specific methods
        allow_headers=ALLOWED_HEADERS,  # Only necessary headers
        max_age=3600,  # Cache preflight for 1 hour
    )


def create_application() -> FastAPI:
    """Create and configure the FastAPI application with security hardening."""
    application = FastAPI(
        title=API_TITLE,
        description=API_DESCRIPTION,
        version=API_VERSION,
    )

    _configure_exception_handlers(application)
    _configure_middleware(application)

    return application


app = create_application()

# Include routers
app.include_router(oscilloscope_router)


@app.get("/")
@get_rate_limiter().limit(get_security_config("api_data")["rate_limit"])
async def root(request: Request) -> dict[str, str]:
    """Root endpoint returning welcome message."""
    return {"message": WELCOME_MESSAGE}


@app.get(HEALTH_ENDPOINT_PATH)
@get_rate_limiter().limit(get_security_config("health_check")["rate_limit"])
async def health_check(request: Request) -> dict[str, str]:
    """Health check endpoint for monitoring."""
    return {"status": HEALTH_STATUS_OK}
