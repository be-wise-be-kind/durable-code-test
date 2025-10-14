"""Circuit breaker pattern implementation for preventing cascading failures.

Purpose: Circuit breaker pattern implementation for preventing cascading
    failures in distributed systems.
Scope: Service resilience and fault isolation for external service dependencies
Overview: This module implements the circuit breaker pattern to protect the
    application from cascading failures when external services become
    unavailable or unresponsive. The circuit breaker monitors the success and
    failure rates of service calls, automatically opening when failure
    thresholds are exceeded, preventing further attempts that would likely
    fail.
    It includes three states: CLOSED (normal operation), OPEN (failures
    exceeded threshold), and HALF_OPEN (testing recovery). The implementation
    provides configurable thresholds, timeout periods, and recovery testing
    intervals, ensuring system stability while allowing for automatic recovery
    when services become available again.
Dependencies: asyncio for async operations, loguru for logging, time for
    timeout tracking
Exports: CircuitBreaker class, CircuitState enum, circuit_breaker decorator
Interfaces: CircuitBreaker.call() method, decorator interface for wrapping
    service calls
Implementation: State machine pattern with automatic state transitions based
    on failure metrics
"""

import asyncio
import time
from collections.abc import Callable
from enum import Enum
from typing import Any, TypeVar

from loguru import logger

from .exceptions import ExternalServiceError

T = TypeVar("T")

# Circuit Breaker Configuration Constants
DATABASE_FAILURE_THRESHOLD = 3
DATABASE_SUCCESS_THRESHOLD = 2
DATABASE_TIMEOUT_DURATION = 30.0

EXTERNAL_API_FAILURE_THRESHOLD = 5
EXTERNAL_API_SUCCESS_THRESHOLD = 3
EXTERNAL_API_TIMEOUT_DURATION = 60.0

CACHE_FAILURE_THRESHOLD = 10
CACHE_SUCCESS_THRESHOLD = 5
CACHE_TIMEOUT_DURATION = 20.0


class CircuitBreakerState(Enum):
    """States of a circuit breaker."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreakerStateMachine:
    """State machine for circuit breaker state transitions."""

    def __init__(
        self,
        name: str,
        failure_threshold: int,
        success_threshold: int,
        timeout_duration: float,
    ) -> None:
        """Initialize state manager."""
        self.name = name
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout_duration = timeout_duration
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: float | None = None
        self._lock = asyncio.Lock()

    async def transition_to_open(self) -> None:
        """Transition to OPEN state."""
        self.state = CircuitBreakerState.OPEN
        self.last_failure_time = time.time()
        self.success_count = 0
        logger.error(
            "Circuit breaker '{name}' opened after {count} failures",
            name=self.name,
            count=self.failure_count,
        )

    async def transition_to_closed(self) -> None:
        """Transition to CLOSED state."""
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        logger.info("Circuit breaker '{name}' closed", name=self.name)

    async def transition_to_half_open(self) -> None:
        """Transition to HALF_OPEN state."""
        self.state = CircuitBreakerState.HALF_OPEN
        self.success_count = 0
        logger.info("Circuit breaker '{name}' half-opened for testing", name=self.name)

    async def should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self.last_failure_time is None:
            return False
        return time.time() - self.last_failure_time >= self.timeout_duration

    async def on_success(self) -> None:
        """Handle successful call.

        Note: Must be called while holding self._lock to ensure atomicity.
        """
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                await self.transition_to_closed()
        elif self.state == CircuitBreakerState.CLOSED:
            self.failure_count = 0

    async def on_failure(self) -> None:
        """Handle failed call.

        Note: Must be called while holding self._lock to ensure atomicity.
        """
        if self.state == CircuitBreakerState.HALF_OPEN:
            await self.transition_to_open()
            return

        if self.state == CircuitBreakerState.CLOSED:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                await self.transition_to_open()

    async def check_state_transition(self) -> None:
        """Check if state should transition from OPEN to HALF_OPEN."""
        if self.state == CircuitBreakerState.OPEN and await self.should_attempt_reset():
            await self.transition_to_half_open()

    def get_status(self) -> dict[str, Any]:
        """Get current state manager status."""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "failure_threshold": self.failure_threshold,
            "success_threshold": self.success_threshold,
            "timeout_duration": self.timeout_duration,
        }


class CircuitBreaker:
    """
    Circuit breaker implementation to prevent cascading failures.

    The circuit breaker has three states:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Service is failing, requests are rejected immediately
    - HALF_OPEN: Testing if service has recovered

    Transitions:
    - CLOSED -> OPEN: After failure_threshold failures
    - OPEN -> HALF_OPEN: After timeout_duration seconds
    - HALF_OPEN -> CLOSED: After success_threshold successes
    - HALF_OPEN -> OPEN: After any failure
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        *,
        timeout_duration: float = 60.0,
        expected_exceptions: tuple[type[Exception], ...] | None = None,
    ) -> None:
        """
        Initialize circuit breaker.

        Args:
            name: Name for logging and identification
            failure_threshold: Number of failures before opening circuit
            success_threshold: Number of successes in half-open before closing
            timeout_duration: Seconds to wait before trying half-open
            expected_exceptions: Exceptions that trigger the circuit breaker
        """
        self.name = name
        self.expected_exceptions = expected_exceptions or (
            ExternalServiceError,
            ConnectionError,
            TimeoutError,
        )
        self.state_manager = CircuitBreakerStateMachine(name, failure_threshold, success_threshold, timeout_duration)

    async def _execute_function(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Execute the function with proper async handling."""
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        return func(*args, **kwargs)

    async def call(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """
        Execute function through circuit breaker.

        Args:
            func: Function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Result of func

        Raises:
            ExternalServiceError: When circuit is open
            Exception: Whatever func raises
        """
        async with self.state_manager._lock:
            await self.state_manager.check_state_transition()

            # Reject if circuit is open
            if self.state_manager.state == CircuitBreakerState.OPEN:
                raise ExternalServiceError(
                    f"Circuit breaker '{self.name}' is open",
                    details={
                        "circuit_breaker": self.name,
                        "state": self.state_manager.state.value,
                    },
                )

        # Attempt the call
        try:
            result = await self._execute_function(func, *args, **kwargs)
            # Hold lock during state update to prevent race condition
            async with self.state_manager._lock:
                await self.state_manager.on_success()
            return result

        except self.expected_exceptions:
            # Hold lock during state update to prevent race condition
            async with self.state_manager._lock:
                await self.state_manager.on_failure()
            raise

    def __call__(self, func: Callable[..., Any]) -> Callable[..., Any]:
        """
        Decorator to wrap function with circuit breaker.

        Args:
            func: Function to wrap

        Returns:
            Wrapped function

        Example:
            @circuit_breaker
            async def external_api_call():
                ...
        """
        if asyncio.iscoroutinefunction(func):

            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                return await self.call(func, *args, **kwargs)

            return async_wrapper

        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            # For sync functions, we need to run in an event loop
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.call(func, *args, **kwargs))

        return sync_wrapper

    @property
    def is_open(self) -> bool:
        """Check if circuit is open."""
        return self.state_manager.state == CircuitBreakerState.OPEN

    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed."""
        return self.state_manager.state == CircuitBreakerState.CLOSED

    def get_status(self) -> dict[str, Any]:
        """
        Get current circuit breaker status.

        Returns:
            Dictionary with status information
        """
        status = self.state_manager.get_status()
        status["name"] = self.name
        return status


# Pre-configured circuit breakers for common scenarios
database_circuit_breaker = CircuitBreaker(
    name="database",
    failure_threshold=DATABASE_FAILURE_THRESHOLD,
    success_threshold=DATABASE_SUCCESS_THRESHOLD,
    timeout_duration=DATABASE_TIMEOUT_DURATION,
)

external_api_circuit_breaker = CircuitBreaker(
    name="external_api",
    failure_threshold=EXTERNAL_API_FAILURE_THRESHOLD,
    success_threshold=EXTERNAL_API_SUCCESS_THRESHOLD,
    timeout_duration=EXTERNAL_API_TIMEOUT_DURATION,
)

cache_circuit_breaker = CircuitBreaker(
    name="cache",
    failure_threshold=CACHE_FAILURE_THRESHOLD,
    success_threshold=CACHE_SUCCESS_THRESHOLD,
    timeout_duration=CACHE_TIMEOUT_DURATION,
)
