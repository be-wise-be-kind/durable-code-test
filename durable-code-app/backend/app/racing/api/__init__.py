"""Racing API package.

Purpose: API route handlers for racing game endpoints
Scope: Track generation and racing game APIs
Overview: This package contains all FastAPI route handlers for the racing
    game, organized by functionality.
Dependencies: FastAPI, domain logic modules
Exports: Router for mounting in main application
Interfaces: REST API endpoints
Implementation: Modular route handlers with proper separation of concerns
"""

from .routes import router

__all__ = ["router"]
