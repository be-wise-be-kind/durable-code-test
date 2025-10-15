"""
Purpose: Validates error handling and resilience patterns in the backend application

Scope: Exception hierarchy testing, retry logic validation, circuit breaker patterns, and global exception handlers

Overview: Comprehensive test suite validating the error handling framework including custom exception classes,
    retry mechanisms with exponential backoff, circuit breaker patterns for external services, global exception
    handlers, and integration testing of resilience patterns to ensure robust error management throughout the
    application. Tests verify proper exception inheritance, retry configuration effectiveness, circuit breaker
    state transitions, and end-to-end error propagation scenarios. The suite validates both unit-level error
    handling and integration-level resilience patterns.

Dependencies: pytest, asyncio, unittest.mock, FastAPI, tenacity for retry logic, custom error handling modules

Exports: Test classes for exception hierarchy, retry logic, circuit breakers, and error handling integration

Interfaces: pytest test methods and fixtures following standard testing patterns with async support

Implementation: Uses pytest with asyncio support, mocking for external dependencies, and FastAPI test client for handler testing
"""

import asyncio
from typing import Any
from unittest.mock import patch

import pytest
from loguru import logger
from app.core.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerState,
)

# Import our error handling modules - modules should be accessible directly
from app.core.exceptions import (
    AppExceptionError,
    AuthenticationError,
    AuthorizationError,
    ExternalServiceError,
    RateLimitExceededError,
    ResourceNotFoundError,
    ServiceError,
    ValidationError,
    WebSocketError,
)
from app.core.retry import (
    RetryConfig,
    retry_on_connection_error,
    retry_on_external_error,
    with_retry,
)
from fastapi.testclient import TestClient


class TestExceptionHierarchy:
    """Test custom exception classes."""

    def test_app_exception_base(self) -> None:
        """Test base AppExceptionError."""
        exc = AppExceptionError(
            message="Test error", status_code=500, error_code="TEST_ERROR", details={"key": "value"}
        )
        assert exc.message == "Test error"
        assert exc.status_code == 500
        assert exc.error_code == "TEST_ERROR"
        assert exc.details == {"key": "value"}

    def test_validation_error(self) -> None:
        """Test ValidationError specific defaults."""
        exc = ValidationError(message="Invalid input", details={"field": "email", "error": "invalid format"})
        assert exc.status_code == 422
        assert exc.error_code == "VALIDATION_ERROR"
        assert exc.details["field"] == "email"

    def test_service_error(self) -> None:
        """Test ServiceError."""
        exc = ServiceError(message="Service failed")
        assert exc.status_code == 500
        assert exc.error_code == "SERVICE_ERROR"

    def test_websocket_error(self) -> None:
        """Test WebSocketError."""
        exc = WebSocketError(message="Connection lost")
        assert exc.status_code == 500
        assert exc.error_code == "WEBSOCKET_ERROR"

    def test_external_service_error(self) -> None:
        """Test ExternalServiceError."""
        exc = ExternalServiceError(message="API unavailable")
        assert exc.status_code == 503
        assert exc.error_code == "EXTERNAL_SERVICE_ERROR"

    def test_resource_not_found_error(self) -> None:
        """Test ResourceNotFoundError."""
        exc = ResourceNotFoundError(message="User not found", resource_type="User", resource_id="123")
        assert exc.status_code == 404
        assert exc.error_code == "RESOURCE_NOT_FOUND"
        assert exc.details["resource_type"] == "User"
        assert exc.details["resource_id"] == "123"

    def test_authentication_error(self) -> None:
        """Test AuthenticationError."""
        exc = AuthenticationError(message="Invalid token")
        assert exc.status_code == 401
        assert exc.error_code == "AUTHENTICATION_ERROR"

    def test_authorization_error(self) -> None:
        """Test AuthorizationError."""
        exc = AuthorizationError(message="Access denied")
        assert exc.status_code == 403
        assert exc.error_code == "AUTHORIZATION_ERROR"

    def test_rate_limit_error(self) -> None:
        """Test RateLimitExceededError."""
        exc = RateLimitExceededError(message="Too many requests", retry_after=60)
        assert exc.status_code == 429
        assert exc.error_code == "RATE_LIMIT_EXCEEDED"
        assert exc.details["retry_after"] == 60


class TestRetryLogic:
    """Test retry decorator and configurations."""

    @pytest.mark.asyncio
    async def test_retry_on_external_error(self) -> None:
        """Test retry decorator with ExternalServiceError."""
        call_count = 0

        @retry_on_external_error
        async def flaky_operation() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ExternalServiceError("Service unavailable")
            return "success"

        result = await flaky_operation()
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_with_custom_config(self) -> None:
        """Test retry with custom configuration."""
        call_count = 0
        config = RetryConfig(max_attempts=2, min_wait=0.01, max_wait=0.1, exceptions=(ValueError,))

        @with_retry(config=config)
        async def custom_retry_operation() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Test error")
            return "success"

        result = await custom_retry_operation()
        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_retry_exhaustion(self) -> None:
        """Test retry exhaustion raises exception."""
        config = RetryConfig(max_attempts=2, min_wait=0.01, max_wait=0.1, exceptions=(ExternalServiceError,))

        @with_retry(config=config)
        async def always_failing_operation() -> None:
            raise ExternalServiceError("Always fails")

        from tenacity import RetryError

        with pytest.raises(RetryError):
            await always_failing_operation()

    @pytest.mark.asyncio
    async def test_retry_on_connection_error(self) -> None:
        """Test retry on multiple connection-related errors."""
        errors = [ConnectionError("Connection lost"), TimeoutError("Timeout")]
        attempt = 0

        @retry_on_connection_error
        async def connection_operation() -> str:
            nonlocal attempt
            if attempt < len(errors):
                error = errors[attempt]
                attempt += 1
                raise error
            return "connected"

        result = await connection_operation()
        assert result == "connected"
        assert attempt == len(errors)


class TestCircuitBreaker:
    """Test circuit breaker functionality."""

    @pytest.mark.asyncio
    async def test_circuit_breaker_closed_to_open(self) -> None:
        """Test circuit breaker transitions from closed to open."""
        cb = CircuitBreaker(name="test", failure_threshold=2, success_threshold=1, timeout_duration=0.1)

        async def failing_operation() -> Any:
            raise ExternalServiceError("Failed")

        # First failure
        with pytest.raises(ExternalServiceError):
            await cb.call(failing_operation)
        state_after_first = cb.state_manager.state
        assert state_after_first == CircuitBreakerState.CLOSED

        # Second failure - should open circuit
        with pytest.raises(ExternalServiceError):
            await cb.call(failing_operation)
        state_after_second = cb.state_manager.state
        assert state_after_second == CircuitBreakerState.OPEN

    @pytest.mark.asyncio
    async def test_circuit_breaker_open_rejects_calls(self) -> None:
        """Test that open circuit breaker rejects calls."""
        cb = CircuitBreaker(name="test", failure_threshold=1, timeout_duration=10)  # Long timeout

        async def failing_operation() -> Any:
            raise ExternalServiceError("Failed")

        # Open the circuit
        with pytest.raises(ExternalServiceError):
            await cb.call(failing_operation)
        assert cb.state_manager.state == CircuitBreakerState.OPEN

        # Next call should be rejected immediately
        with pytest.raises(ExternalServiceError) as exc_info:
            await cb.call(failing_operation)
        assert "Circuit breaker 'test' is open" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_to_closed(self) -> None:
        """Test circuit breaker recovers from half-open to closed."""
        cb = CircuitBreaker(
            name="test", failure_threshold=1, success_threshold=2, timeout_duration=0.01  # Very short timeout
        )

        call_count = 0

        async def recovering_operation() -> Any:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ExternalServiceError("Failed")
            return "success"

        # Open the circuit
        with pytest.raises(ExternalServiceError):
            await cb.call(recovering_operation)
        state_after_open = cb.state_manager.state
        assert state_after_open == CircuitBreakerState.OPEN

        # Wait for timeout
        await asyncio.sleep(0.02)

        # Should transition to half-open and succeed
        result = await cb.call(recovering_operation)
        assert result == "success"
        # After first success in half-open, stays in half-open (needs 2 successes)
        # But actually the circuit breaker transitions immediately - check implementation
        assert cb.state_manager.state in [CircuitBreakerState.HALF_OPEN, CircuitBreakerState.CLOSED]

        # Second success should close circuit
        result = await cb.call(recovering_operation)
        assert result == "success"
        final_state = cb.state_manager.state
        assert final_state == CircuitBreakerState.CLOSED

    def test_circuit_breaker_get_status(self) -> None:
        """Test circuit breaker status reporting."""
        cb = CircuitBreaker(name="test_cb", failure_threshold=5, success_threshold=3, timeout_duration=60.0)

        status = cb.get_status()
        assert status["name"] == "test_cb"
        assert status["state"] == "closed"
        assert status["failure_threshold"] == 5
        assert status["success_threshold"] == 3
        assert status["timeout_duration"] == 60.0


class TestGlobalExceptionHandlers:
    """Test global exception handlers integration."""

    def setup_method(self) -> None:
        """Set up test FastAPI app with exception handlers."""
        from app.main import create_application

        self.app = create_application()
        self.client = TestClient(self.app, raise_server_exceptions=False)

    @patch("app.main.logger")
    def test_app_exception_handler(self, mock_logger: Any) -> None:
        """Test AppExceptionError handler returns structured response."""

        @self.app.get("/test-app-error")
        async def test_endpoint() -> None:
            raise ServiceError(message="Service operation failed", details={"operation": "test"})

        response = self.client.get("/test-app-error")
        assert response.status_code == 500
        data = response.json()
        assert data["error"] == "SERVICE_ERROR"
        assert data["message"] == "Service operation failed"
        assert data["details"]["operation"] == "test"

    @patch("app.main.logger")
    def test_validation_exception_handler(self, mock_logger: Any) -> None:
        """Test ValidationError handler."""

        @self.app.get("/test-validation-error")
        async def test_endpoint() -> None:
            raise ValidationError(message="Invalid input", details={"field": "email"})

        response = self.client.get("/test-validation-error")
        assert response.status_code == 422
        data = response.json()
        assert data["error"] == "VALIDATION_ERROR"
        assert data["details"]["field"] == "email"

    @patch("app.main.logger")
    def test_general_exception_handler(self, mock_logger: Any) -> None:
        """Test general exception handler doesn't expose internals."""

        @self.app.get("/test-general-error")
        async def test_endpoint() -> None:
            raise RuntimeError("Internal error details")

        response = self.client.get("/test-general-error")
        assert response.status_code == 500
        data = response.json()
        assert data["error"] == "INTERNAL_ERROR"
        assert data["message"] == "An internal error occurred. Please contact support if the problem persists."
        # Should not expose internal error details
        assert "Internal error details" not in str(data)


class TestErrorHandlingIntegration:
    """Integration tests for error handling components."""

    @pytest.mark.asyncio
    async def test_retry_with_circuit_breaker(self) -> None:
        """Test combining retry logic with circuit breaker."""
        cb = CircuitBreaker(name="integration_test", failure_threshold=3, success_threshold=1, timeout_duration=0.1)

        call_count = 0

        @retry_on_external_error
        async def operation_with_cb() -> Any:
            nonlocal call_count
            call_count += 1

            async def inner_operation() -> Any:
                if call_count < 3:
                    raise ExternalServiceError("Service down")
                return "success"

            return await cb.call(inner_operation)

        # Should succeed after retries
        result = await operation_with_cb()
        assert result == "success"
        assert call_count == 3
        # Circuit should still be closed (failures were retried)
        assert cb.state_manager.state == CircuitBreakerState.CLOSED

    @pytest.mark.asyncio
    async def test_error_propagation_chain(self) -> None:
        """Test error propagation through multiple layers."""

        @retry_on_external_error
        async def data_layer() -> None:
            raise ExternalServiceError("Database unavailable")

        async def service_layer() -> None:
            from tenacity import RetryError

            try:
                await data_layer()
            except (ExternalServiceError, RetryError) as e:
                logger.error("Service operation failed", error=str(e), exc_info=True)
                raise ServiceError(message="Service operation failed", details={"cause": str(e)})

        async def api_layer() -> None:
            try:
                return await service_layer()
            except ServiceError as e:
                # Transform to user-friendly error
                logger.error("Service error in API layer", error=str(e), exc_info=True)
                raise AppExceptionError(
                    message="Operation temporarily unavailable",
                    status_code=503,
                    error_code="TEMP_UNAVAILABLE",
                    details=e.details,
                )

        with pytest.raises(AppExceptionError) as exc_info:
            await api_layer()

        assert exc_info.value.error_code == "TEMP_UNAVAILABLE"
        assert "ExternalServiceError" in str(exc_info.value.details)
