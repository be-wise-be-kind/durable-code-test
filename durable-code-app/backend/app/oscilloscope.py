"""
Purpose: Real-time oscilloscope data streaming API endpoint for the durable code application.

Scope: WebSocket streaming of waveform data with configurable wave types and parameters
Overview: This module provides real-time streaming of oscilloscope data including sine waves,
    square waves, and white noise. It follows FastAPI best practices with WebSocket support
    for efficient real-time data streaming. Includes comprehensive error handling, proper
    validation, and performance optimizations for smooth visualization.
Dependencies: FastAPI, WebSocket, asyncio, numpy for waveform generation
Exports: WebSocket endpoint for oscilloscope data streaming
Interfaces: WebSocket API endpoint with JSON message protocol
Implementation: FastAPI WebSocket route with async streaming and waveform generation
"""

import asyncio
import contextlib
import json
import math
import random
import time
from datetime import datetime
from enum import Enum
from typing import Any

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from loguru import logger
from pydantic import BaseModel, Field, validator

from .racing.state_machine import WebSocketState, WebSocketStateMachine
from .security import get_rate_limiter, get_security_config, validate_numeric_range

# Constants for waveform generation
SAMPLE_RATE = 1000  # Samples per second
BUFFER_SIZE = 100  # Number of samples per transmission
DEFAULT_FREQUENCY = 10.0  # Hz
DEFAULT_AMPLITUDE = 1.0
DEFAULT_OFFSET = 0.0
PI_TIMES_TWO = 2 * math.pi

# Validation constants
MIN_FREQUENCY = 0.1  # Minimum frequency in Hz
MAX_FREQUENCY = 100.0  # Maximum frequency in Hz
MIN_AMPLITUDE = 0.1  # Minimum amplitude
MAX_AMPLITUDE = 10.0  # Maximum amplitude
MIN_OFFSET = -10.0  # Minimum DC offset
MAX_OFFSET = 10.0  # Maximum DC offset

# Timing constants
COMMAND_TIMEOUT = 0.01  # Timeout for receiving commands in seconds
IDLE_SLEEP_DURATION = 0.1  # Sleep duration when not streaming in seconds
# Note: WebSocket global timeout removed - streaming connections are expected to be long-lived
# For production apps requiring connection limits, implement inactivity detection instead
WEBSOCKET_MAX_MESSAGE_SIZE = 1024 * 1024  # 1MB maximum message size

# Example constants for documentation
EXAMPLE_CONFIGURE_FREQUENCY = 20.0  # Example frequency for configure command
EXAMPLE_CONFIGURE_AMPLITUDE = 2.0  # Example amplitude for configure command
EXAMPLE_CONFIGURE_OFFSET = 0.5  # Example offset for configure command

# HTTP Status codes
HTTP_NOT_FOUND = 404

# WebSocket close codes
WS_CLOSE_POLICY_VIOLATION = 1008  # Policy violation (e.g., rate limit exceeded)
WS_CLOSE_NORMAL = 1000  # Normal closure

# API Router for oscilloscope endpoints
router = APIRouter(
    prefix="/api/oscilloscope",
    tags=["oscilloscope"],
    responses={
        HTTP_NOT_FOUND: {"description": "Not found"},
    },
)


class WaveType(str, Enum):
    """Supported waveform types."""

    SINE = "sine"
    SQUARE = "square"
    NOISE = "noise"


class WebSocketRateLimiter:
    """Rate limiter for WebSocket connections to prevent resource exhaustion."""

    def __init__(self, max_connections_per_ip: int = 5, window_seconds: float = 60.0) -> None:
        """Initialize rate limiter.

        Args:
            max_connections_per_ip: Maximum concurrent connections per IP
            window_seconds: Time window for rate limiting in seconds
        """
        self.max_connections = max_connections_per_ip
        self.window = window_seconds
        self.connections: dict[str, list[float]] = {}

    def check_rate_limit(self, client_ip: str) -> bool:
        """Check if client is within rate limits.

        Args:
            client_ip: Client IP address

        Returns:
            True if client is within limits, False if rate limit exceeded
        """
        now = time.time()

        # Initialize or clean old connections for this IP
        if client_ip not in self.connections:
            self.connections[client_ip] = []

        # Remove connections outside the time window
        self.connections[client_ip] = [
            conn_time for conn_time in self.connections[client_ip] if now - conn_time < self.window
        ]

        # Check if limit exceeded
        if len(self.connections[client_ip]) >= self.max_connections:
            logger.warning("Rate limit exceeded", client_ip=client_ip, count=len(self.connections[client_ip]))
            return False

        # Add this connection
        self.connections[client_ip].append(now)
        return True

    def release_connection(self, client_ip: str) -> None:
        """Release a connection slot for an IP address.

        Args:
            client_ip: Client IP address
        """
        if client_ip in self.connections and self.connections[client_ip]:
            self.connections[client_ip].pop()


# Global rate limiter instance
# Note: Increased from 5 to 50 connections to support demo usage patterns
# where users frequently refresh or reconnect. This still provides protection
# against abuse while allowing normal demo interaction.
_websocket_rate_limiter = WebSocketRateLimiter(max_connections_per_ip=50, window_seconds=60.0)


class OscilloscopeCommand(BaseModel):
    """Command model for oscilloscope control with enhanced security validation."""

    command: str = Field(..., description="Command type (start, stop, configure)")
    wave_type: WaveType | None = Field(WaveType.SINE, description="Type of waveform")
    frequency: float | None = Field(
        DEFAULT_FREQUENCY,
        ge=MIN_FREQUENCY,
        le=MAX_FREQUENCY,
        description="Frequency in Hz",
    )
    amplitude: float | None = Field(
        DEFAULT_AMPLITUDE,
        ge=MIN_AMPLITUDE,
        le=MAX_AMPLITUDE,
        description="Wave amplitude",
    )
    offset: float | None = Field(DEFAULT_OFFSET, ge=MIN_OFFSET, le=MAX_OFFSET, description="DC offset")

    @validator("command")
    def validate_command(cls, value: str) -> str:  # noqa: N805
        """Validate command is one of allowed values."""
        allowed_commands = {"start", "stop", "configure"}
        if value not in allowed_commands:
            raise ValueError(f"Command must be one of: {', '.join(allowed_commands)}")
        return value

    @validator("frequency")
    def validate_frequency(cls, value: float | None) -> float | None:  # noqa: N805
        """Validate frequency is within secure operational range."""
        if value is not None:
            return validate_numeric_range(value, MIN_FREQUENCY, MAX_FREQUENCY, "frequency")
        return value

    @validator("amplitude")
    def validate_amplitude(cls, value: float | None) -> float | None:  # noqa: N805
        """Validate amplitude is within secure operational range."""
        if value is not None:
            return validate_numeric_range(value, MIN_AMPLITUDE, MAX_AMPLITUDE, "amplitude")
        return value

    @validator("offset")
    def validate_offset(cls, value: float | None) -> float | None:  # noqa: N805
        """Validate offset is within secure operational range."""
        if value is not None:
            return validate_numeric_range(value, MIN_OFFSET, MAX_OFFSET, "offset")
        return value


class OscilloscopeData(BaseModel):
    """Data model for oscilloscope streaming."""

    timestamp: float = Field(..., description="Unix timestamp")
    samples: list[float] = Field(..., description="Waveform samples")
    sample_rate: int = Field(SAMPLE_RATE, description="Sample rate in Hz")
    wave_type: WaveType = Field(..., description="Current waveform type")
    parameters: dict[str, float] = Field(..., description="Current waveform parameters")


class WaveformGenerator:
    """Generate waveform samples for oscilloscope display."""

    def __init__(self) -> None:
        """Initialize the waveform generator."""
        self.phase = 0.0
        self.last_time = time.time()
        self.wave_type = WaveType.SINE
        self.frequency = DEFAULT_FREQUENCY
        self.amplitude = DEFAULT_AMPLITUDE
        self.offset = DEFAULT_OFFSET

    def configure(self, wave_type: WaveType, frequency: float, amplitude: float, offset: float) -> None:
        """Configure waveform parameters."""
        self.wave_type = wave_type
        self.frequency = frequency
        self.amplitude = amplitude
        self.offset = offset

    def _generate_sine_value(self, t: float) -> float:
        """Generate a single sine wave sample."""
        return self.amplitude * math.sin(PI_TIMES_TWO * self.frequency * t + self.phase)

    def _generate_square_value(self, t: float) -> float:
        """Generate a single square wave sample."""
        sine_value = math.sin(PI_TIMES_TWO * self.frequency * t + self.phase)
        return self.amplitude if sine_value >= 0 else -self.amplitude

    def _generate_noise_value(self) -> float:
        """Generate a single white noise sample."""
        return self.amplitude * (2 * random.random() - 1)  # noqa: S311  # nosec B311

    def _get_sample_value(self, t: float) -> float:
        """Get a single sample value based on wave type."""
        if self.wave_type == WaveType.SINE:
            return self._generate_sine_value(t)
        if self.wave_type == WaveType.SQUARE:
            return self._generate_square_value(t)
        if self.wave_type == WaveType.NOISE:
            return self._generate_noise_value()
        return 0.0

    def _update_phase_for_continuity(self, num_samples: int, dt: float) -> None:
        """Update phase to maintain waveform continuity."""
        if self.wave_type == WaveType.NOISE:
            return

        self.phase += PI_TIMES_TWO * self.frequency * num_samples * dt
        # Keep phase in reasonable range
        if self.phase > PI_TIMES_TWO:
            self.phase -= PI_TIMES_TWO

    def generate_samples(self, num_samples: int) -> list[float]:
        """Generate waveform samples based on current configuration."""
        dt = 1.0 / SAMPLE_RATE
        samples = []

        for i in range(num_samples):
            t = i * dt
            value = self._get_sample_value(t)
            samples.append(value + self.offset)

        self._update_phase_for_continuity(num_samples, dt)
        return samples


async def _handle_command(
    command: OscilloscopeCommand, generator: WaveformGenerator, state_machine: WebSocketStateMachine
) -> str:
    """Handle incoming WebSocket commands."""
    handlers = {
        "start": _handle_start_command,
        "stop": _handle_stop_command,
        "configure": _handle_configure_command,
    }

    handler = handlers.get(command.command)
    if handler:
        return handler(command, generator, state_machine)
    return "Unknown command"


def _handle_start_command(
    command: OscilloscopeCommand, generator: WaveformGenerator, state_machine: WebSocketStateMachine
) -> str:
    """Handle start command."""
    generator.configure(
        wave_type=command.wave_type or WaveType.SINE,
        frequency=command.frequency or DEFAULT_FREQUENCY,
        amplitude=command.amplitude or DEFAULT_AMPLITUDE,
        offset=command.offset or DEFAULT_OFFSET,
    )
    # Only transition to streaming if not already streaming
    if not state_machine.is_streaming():
        state_machine.start_streaming()
    return f"Started streaming {command.wave_type} wave"


def _handle_stop_command(
    command: OscilloscopeCommand,
    generator: WaveformGenerator,  # pylint: disable=unused-argument
    state_machine: WebSocketStateMachine,
) -> str:
    """Handle stop command."""
    state_machine.pause_streaming()
    return "Stopped streaming"


def _handle_configure_command(
    command: OscilloscopeCommand, generator: WaveformGenerator, state_machine: WebSocketStateMachine
) -> str:
    """Handle configure command."""
    generator.configure(
        wave_type=command.wave_type or generator.wave_type,
        frequency=command.frequency or generator.frequency,
        amplitude=command.amplitude or generator.amplitude,
        offset=command.offset or generator.offset,
    )
    return f"Configured to {command.wave_type} wave"


async def _process_command(
    websocket: WebSocket, generator: WaveformGenerator, state_machine: WebSocketStateMachine
) -> None:
    """Process incoming WebSocket commands."""
    try:
        message = await asyncio.wait_for(websocket.receive_text(), timeout=COMMAND_TIMEOUT)
        try:
            data = json.loads(message)
            command = OscilloscopeCommand(**data)
            log_msg = await _handle_command(command, generator, state_machine)
            logger.info(log_msg)
        except (json.JSONDecodeError, ValueError) as e:
            logger.error("Invalid command received", error=str(e), exc_info=True)
            await websocket.send_json({"error": str(e)})
    except TimeoutError:  # design-lint: ignore[logging.exception-logging]
        # Timeout is expected when no commands received - no logging needed
        pass


async def _send_data(websocket: WebSocket, generator: WaveformGenerator) -> None:
    """Send oscilloscope data over WebSocket."""
    samples = generator.generate_samples(BUFFER_SIZE)
    response_data = OscilloscopeData(
        timestamp=time.time(),
        samples=samples,
        sample_rate=SAMPLE_RATE,
        wave_type=generator.wave_type,
        parameters={
            "frequency": generator.frequency,
            "amplitude": generator.amplitude,
            "offset": generator.offset,
        },
    )
    await websocket.send_json(response_data.dict())


async def _handle_timeout_error(websocket: WebSocket, state_machine: WebSocketStateMachine, client_ip: str) -> None:
    """Handle WebSocket timeout errors."""
    logger.info("WebSocket connection timeout", client_ip=client_ip)
    state_machine.disconnect()
    with contextlib.suppress(WebSocketDisconnect, OSError):
        await websocket.send_json({"error": "Connection timeout", "message": "Inactivity timeout"})
        await websocket.close(code=WS_CLOSE_NORMAL, reason="Timeout")


def _handle_disconnect_error(state_machine: WebSocketStateMachine, client_ip: str) -> None:
    """Handle WebSocket disconnect errors."""
    logger.debug("Oscilloscope WebSocket connection closed", connection_type="websocket", client_ip=client_ip)
    state_machine.disconnect()


async def _handle_connection_error(
    websocket: WebSocket, state_machine: WebSocketStateMachine, client_ip: str, error: OSError
) -> None:
    """Handle WebSocket connection errors."""
    logger.error("Connection error in oscilloscope stream", error=str(error), client_ip=client_ip)
    state_machine.disconnect()
    with contextlib.suppress(WebSocketDisconnect, OSError):
        await websocket.send_json({"error": "Connection error", "message": str(error)})


async def _handle_data_processing_error(
    websocket: WebSocket, state_machine: WebSocketStateMachine, client_ip: str, error: ValueError | TypeError
) -> None:
    """Handle data processing errors."""
    logger.error("Data processing error in oscilloscope stream", error=str(error), client_ip=client_ip)
    state_machine.disconnect()
    with contextlib.suppress(WebSocketDisconnect, OSError):
        await websocket.send_json({"error": "Data processing error", "message": str(error)})


def _handle_cancellation_error(state_machine: WebSocketStateMachine, client_ip: str) -> None:
    """Handle cancellation errors."""
    logger.debug("Oscilloscope stream cancelled", client_ip=client_ip)
    state_machine.disconnect()


async def _run_stream_loop(
    websocket: WebSocket, generator: WaveformGenerator, state_machine: WebSocketStateMachine
) -> None:
    """Run the main streaming loop."""
    while not state_machine.is_disconnected():
        await _process_command(websocket, generator, state_machine)

        if state_machine.is_streaming():
            await _send_data(websocket, generator)
            await asyncio.sleep(BUFFER_SIZE / SAMPLE_RATE)
        else:
            await asyncio.sleep(IDLE_SLEEP_DURATION)


async def _cleanup_connection(state_machine: WebSocketStateMachine, client_ip: str) -> None:
    """Clean up connection state and release resources."""
    if not state_machine.is_disconnected():
        # First transition to disconnecting state if not already
        state_machine.disconnect()
        # Then complete the disconnect
        if not state_machine.is_disconnected():
            state_machine.complete_disconnect()
    _websocket_rate_limiter.release_connection(client_ip)


async def _dispatch_exception_handler(
    exception: Exception, websocket: WebSocket, state_machine: WebSocketStateMachine, client_ip: str
) -> None:
    """Dispatch exception to appropriate handler based on type."""
    if isinstance(exception, TimeoutError):
        await _handle_timeout_error(websocket, state_machine, client_ip)
    elif isinstance(exception, WebSocketDisconnect):
        _handle_disconnect_error(state_machine, client_ip)
    elif isinstance(exception, OSError):
        await _handle_connection_error(websocket, state_machine, client_ip, exception)
    elif isinstance(exception, (ValueError, TypeError)):
        await _handle_data_processing_error(websocket, state_machine, client_ip, exception)


async def _handle_stream_errors(
    websocket: WebSocket, generator: WaveformGenerator, state_machine: WebSocketStateMachine, client_ip: str
) -> None:
    """Handle WebSocket stream errors with specific error handlers.

    Note: No global timeout - the connection stays alive as long as it's actively streaming.
    This is appropriate for real-time data streaming applications where continuous
    connections are expected. The connection will close on client disconnect or errors.
    """
    try:
        await _run_stream_loop(websocket, generator, state_machine)
    except asyncio.CancelledError:
        _handle_cancellation_error(state_machine, client_ip)
        # Don't re-raise - let cleanup happen in finally block
    except (WebSocketDisconnect, OSError, ValueError, TypeError) as exception:
        await _dispatch_exception_handler(exception, websocket, state_machine, client_ip)
    finally:
        await _cleanup_connection(state_machine, client_ip)


@router.websocket("/stream")
async def oscilloscope_stream(websocket: WebSocket) -> None:
    """Provide WebSocket endpoint for real-time oscilloscope data streaming.

    Accepts commands to start/stop streaming and configure waveform parameters.
    Streams waveform data at configured sample rate.

    Protocol:
        Client -> Server: JSON command (OscilloscopeCommand)
        Server -> Client: JSON data (OscilloscopeData)

    Security:
        - No global connection timeout (appropriate for streaming applications)
        - Rate limiting: 50 connections per IP per minute
        - Connection closes on client disconnect or protocol errors
    """
    # Get client IP for rate limiting
    client_ip = websocket.client.host if websocket.client else "unknown"

    # Check rate limit before accepting connection
    if not _websocket_rate_limiter.check_rate_limit(client_ip):
        await websocket.close(code=WS_CLOSE_POLICY_VIOLATION, reason="Rate limit exceeded")
        logger.warning("WebSocket connection rejected due to rate limit", client_ip=client_ip)
        return

    await websocket.accept()
    logger.info("Oscilloscope WebSocket connection established", client_ip=client_ip)

    # Initialize state machine and generator
    state_machine = WebSocketStateMachine(state=WebSocketState.CONNECTED)
    generator = WaveformGenerator()

    await _handle_stream_errors(websocket, generator, state_machine, client_ip)


def _get_stream_commands() -> dict[str, Any]:
    """Get WebSocket stream command definitions."""
    return {
        "start": {
            "description": "Start streaming waveform data",
            "example": {
                "command": "start",
                "wave_type": "sine",
                "frequency": 10.0,
                "amplitude": 1.0,
                "offset": 0.0,
            },
        },
        "stop": {"description": "Stop streaming", "example": {"command": "stop"}},
        "configure": {
            "description": "Update waveform parameters while streaming",
            "example": {
                "command": "configure",
                "wave_type": "square",
                "frequency": EXAMPLE_CONFIGURE_FREQUENCY,
                "amplitude": EXAMPLE_CONFIGURE_AMPLITUDE,
                "offset": EXAMPLE_CONFIGURE_OFFSET,
            },
        },
    }


def _get_response_format() -> dict[str, Any]:
    """Get WebSocket response format specification."""
    return {
        "timestamp": "Unix timestamp",
        "samples": "Array of waveform samples",
        "sample_rate": "Samples per second",
        "wave_type": "Current waveform type",
        "parameters": {
            "frequency": "Current frequency in Hz",
            "amplitude": "Current amplitude",
            "offset": "Current DC offset",
        },
    }


# API endpoint to document WebSocket streaming interface
@router.get("/stream/info", tags=["oscilloscope"])
@get_rate_limiter().limit(get_security_config("api_data")["rate_limit"])
async def get_stream_info(request: Request) -> dict[str, Any]:
    """Get information about the WebSocket streaming endpoint.

    The oscilloscope provides real-time data streaming via WebSocket at:
    ws://localhost:8000/api/oscilloscope/stream

    Returns:
        Information about the WebSocket endpoint including connection details,
        message formats, and available commands.
    """
    return {
        "endpoint": "ws://localhost:8000/api/oscilloscope/stream",
        "description": "Real-time oscilloscope data streaming via WebSocket",
        "protocol": {
            "connection": "WebSocket",
            "message_format": "JSON",
        },
        "commands": _get_stream_commands(),
        "response_format": _get_response_format(),
        "supported_wave_types": [wave.value for wave in WaveType],
        "sample_rate": SAMPLE_RATE,
        "buffer_size": BUFFER_SIZE,
    }


# API endpoint to get oscilloscope configuration
@router.get("/config", tags=["oscilloscope"])
@get_rate_limiter().limit(get_security_config("config")["rate_limit"])
async def get_oscilloscope_config(request: Request) -> dict[str, Any]:
    """Get current oscilloscope configuration and supported parameters.

    Returns:
        Configuration object containing supported wave types, frequency ranges,
        amplitude ranges, and other oscilloscope parameters.
    """
    return {
        "sample_rate": SAMPLE_RATE,
        "buffer_size": BUFFER_SIZE,
        "supported_wave_types": [wave.value for wave in WaveType],
        "frequency": {
            "min": MIN_FREQUENCY,
            "max": MAX_FREQUENCY,
            "default": DEFAULT_FREQUENCY,
        },
        "amplitude": {
            "min": MIN_AMPLITUDE,
            "max": MAX_AMPLITUDE,
            "default": DEFAULT_AMPLITUDE,
        },
        "offset": {"min": MIN_OFFSET, "max": MAX_OFFSET, "default": DEFAULT_OFFSET},
    }


# Health check for oscilloscope module
@router.get("/health", include_in_schema=False)
@get_rate_limiter().limit(get_security_config("health_check")["rate_limit"])
async def oscilloscope_health_check(request: Request) -> dict[str, Any]:
    """Health check endpoint for oscilloscope module."""
    return {
        "status": "healthy",
        "module": "oscilloscope",
        "timestamp": datetime.now().isoformat(),
        "sample_rate": SAMPLE_RATE,
        "supported_waves": [wave.value for wave in WaveType],
    }
