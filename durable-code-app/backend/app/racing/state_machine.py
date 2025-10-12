"""
Purpose: WebSocket state machine for managing oscilloscope stream lifecycle.

Scope: State management for WebSocket connections with validation of state transitions
Overview: This module provides a robust state machine implementation for managing WebSocket
    connection lifecycles. It ensures valid state transitions, prevents invalid operations,
    and provides clear error messages. The state machine pattern improves code maintainability
    and testability compared to ad-hoc boolean state management.
Dependencies: Enum for state definitions, dataclasses for configuration
Exports: WebSocketState enum, WebSocketStateMachine class
Interfaces: State machine with transition validation and state query methods
Implementation: Finite state machine with explicit transition rules and validation
"""

from dataclasses import dataclass, field
from enum import Enum


class WebSocketState(str, Enum):
    """Valid states for WebSocket connection lifecycle."""

    CONNECTING = "connecting"
    CONNECTED = "connected"
    STREAMING = "streaming"
    PAUSED = "paused"
    DISCONNECTING = "disconnecting"
    DISCONNECTED = "disconnected"


@dataclass
class WebSocketStateMachine:
    """State machine for managing WebSocket connection lifecycle.

    This state machine ensures that WebSocket connections follow valid state
    transitions and prevents invalid operations. It improves code maintainability
    by making state management explicit and testable.

    Valid state transitions:
        CONNECTING → CONNECTED, DISCONNECTED
        CONNECTED → STREAMING, PAUSED, DISCONNECTING
        STREAMING → PAUSED, DISCONNECTING
        PAUSED → STREAMING, DISCONNECTING
        DISCONNECTING → DISCONNECTED
        DISCONNECTED → (terminal state)

    Example:
        >>> sm = WebSocketStateMachine()
        >>> sm.state
        <WebSocketState.CONNECTING: 'connecting'>
        >>> sm.transition_to(WebSocketState.CONNECTED)
        >>> sm.can_stream()
        True
        >>> sm.start_streaming()
        >>> sm.is_streaming()
        True
    """

    state: WebSocketState = WebSocketState.CONNECTING
    _transition_rules: dict[WebSocketState, set[WebSocketState]] = field(
        default_factory=lambda: {
            WebSocketState.CONNECTING: {
                WebSocketState.CONNECTED,
                WebSocketState.DISCONNECTED,
            },
            WebSocketState.CONNECTED: {
                WebSocketState.STREAMING,
                WebSocketState.PAUSED,
                WebSocketState.DISCONNECTING,
            },
            WebSocketState.STREAMING: {
                WebSocketState.PAUSED,
                WebSocketState.DISCONNECTING,
            },
            WebSocketState.PAUSED: {
                WebSocketState.STREAMING,
                WebSocketState.DISCONNECTING,
            },
            WebSocketState.DISCONNECTING: {
                WebSocketState.DISCONNECTED,
            },
            WebSocketState.DISCONNECTED: set(),  # Terminal state
        }
    )

    def transition_to(self, new_state: WebSocketState) -> None:
        """Transition to a new state with validation.

        Args:
            new_state: The state to transition to

        Raises:
            ValueError: If the transition is not allowed from the current state
        """
        if not self.can_transition_to(new_state):
            valid_transitions = ", ".join(s.value for s in self._transition_rules[self.state])
            raise ValueError(
                f"Invalid transition from {self.state.value} to {new_state.value}. "
                f"Valid transitions: {valid_transitions}"
            )
        self.state = new_state

    def can_transition_to(self, new_state: WebSocketState) -> bool:
        """Check if a transition to the given state is valid.

        Args:
            new_state: The state to check

        Returns:
            True if the transition is valid, False otherwise
        """
        return new_state in self._transition_rules[self.state]

    def is_streaming(self) -> bool:
        """Check if currently in streaming state.

        Returns:
            True if in STREAMING state, False otherwise
        """
        return self.state == WebSocketState.STREAMING

    def is_paused(self) -> bool:
        """Check if currently in paused state.

        Returns:
            True if in PAUSED state, False otherwise
        """
        return self.state == WebSocketState.PAUSED

    def is_connected(self) -> bool:
        """Check if in any connected state (CONNECTED, STREAMING, or PAUSED).

        Returns:
            True if connected, False otherwise
        """
        return self.state in {
            WebSocketState.CONNECTED,
            WebSocketState.STREAMING,
            WebSocketState.PAUSED,
        }

    def is_disconnected(self) -> bool:
        """Check if in a disconnected state (DISCONNECTING or DISCONNECTED).

        Returns:
            True if disconnected, False otherwise
        """
        return self.state in {
            WebSocketState.DISCONNECTING,
            WebSocketState.DISCONNECTED,
        }

    def can_stream(self) -> bool:
        """Check if streaming can be started from current state.

        Returns:
            True if can transition to STREAMING, False otherwise
        """
        return self.can_transition_to(WebSocketState.STREAMING)

    def start_streaming(self) -> None:
        """Start streaming (transition to STREAMING state).

        Raises:
            ValueError: If streaming cannot be started from current state
        """
        self.transition_to(WebSocketState.STREAMING)

    def pause_streaming(self) -> None:
        """Pause streaming (transition to PAUSED state).

        Raises:
            ValueError: If streaming cannot be paused from current state
        """
        self.transition_to(WebSocketState.PAUSED)

    def disconnect(self) -> None:
        """Begin disconnection process.

        Raises:
            ValueError: If disconnection cannot be initiated from current state
        """
        if self.state == WebSocketState.DISCONNECTED:
            # Already disconnected, no-op
            return

        if self.can_transition_to(WebSocketState.DISCONNECTING):
            self.transition_to(WebSocketState.DISCONNECTING)
        elif self.can_transition_to(WebSocketState.DISCONNECTED):
            self.transition_to(WebSocketState.DISCONNECTED)
        else:
            raise ValueError(f"Cannot disconnect from state {self.state.value}")

    def complete_disconnect(self) -> None:
        """Complete disconnection (transition to DISCONNECTED state).

        Raises:
            ValueError: If disconnection cannot be completed from current state
        """
        self.transition_to(WebSocketState.DISCONNECTED)
