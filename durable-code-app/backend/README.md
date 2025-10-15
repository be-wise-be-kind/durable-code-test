# Backend API

**Purpose**: FastAPI backend service providing oscilloscope simulation and real-time data streaming

**Scope**: Python backend application with WebSocket support for real-time data streaming and REST API endpoints

**Overview**: Provides a high-performance Python backend built with FastAPI framework, featuring real-time
    oscilloscope data simulation and WebSocket communication. Implements asynchronous request handling,
    data streaming capabilities, and comprehensive API documentation with automatic OpenAPI generation.
    Includes health monitoring, error handling, and scalable architecture patterns for production deployment.
    The service generates synthetic waveform data and streams it to frontend clients through WebSocket connections.

**Dependencies**: FastAPI web framework, uvicorn ASGI server, WebSocket support libraries, Python 3.11

**Exports**: REST API endpoints, WebSocket streaming service, health monitoring, and OpenAPI documentation

**Related**: Frontend React application, Docker containerization, and deployment configuration

**Implementation**: Asynchronous Python architecture with FastAPI, WebSocket streaming, and production-ready patterns

## Quick Start

```bash
# Install dependencies with Poetry
poetry install

# Run development server
poetry run uvicorn app.main:app --reload

# Run with Docker
docker build -t backend .
docker run -p 8000:8000 backend
```

## API Documentation

- OpenAPI documentation: http://localhost:8000/docs
- Health endpoint: http://localhost:8000/health
- WebSocket endpoint: ws://localhost:8000/ws
# Test comment
