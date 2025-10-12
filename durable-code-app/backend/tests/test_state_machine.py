"""Tests for WebSocket state machine implementation."""

import pytest

from app.racing.state_machine import WebSocketState, WebSocketStateMachine


class TestWebSocketStateMachine:
    """Tests for WebSocketStateMachine class."""

    def test_initial_state_is_connecting(self) -> None:
        """Test that initial state is CONNECTING."""
        sm = WebSocketStateMachine()
        assert sm.state == WebSocketState.CONNECTING

    def test_can_initialize_with_custom_state(self) -> None:
        """Test that state machine can be initialized with a custom state."""
        sm = WebSocketStateMachine(state=WebSocketState.CONNECTED)
        assert sm.state == WebSocketState.CONNECTED

    def test_valid_transition_from_connecting_to_connected(self) -> None:
        """Test valid transition from CONNECTING to CONNECTED."""
        sm = WebSocketStateMachine()
        sm.transition_to(WebSocketState.CONNECTED)
        assert sm.state == WebSocketState.CONNECTED

    def test_valid_transition_from_connecting_to_disconnected(self) -> None:
        """Test valid transition from CONNECTING to DISCONNECTED."""
        sm = WebSocketStateMachine()
        sm.transition_to(WebSocketState.DISCONNECTED)
        assert sm.state == WebSocketState.DISCONNECTED

    def test_invalid_transition_from_connecting_to_streaming(self) -> None:
        """Test invalid transition from CONNECTING to STREAMING."""
        sm = WebSocketStateMachine()
        with pytest.raises(ValueError, match="Invalid transition"):
            sm.transition_to(WebSocketState.STREAMING)

    def test_valid_transition_from_connected_to_streaming(self) -> None:
        """Test valid transition from CONNECTED to STREAMING."""
        sm = WebSocketStateMachine(state=WebSocketState.CONNECTED)
        sm.transition_to(WebSocketState.STREAMING)
        assert sm.state == WebSocketState.STREAMING

    def test_valid_transition_from_connected_to_paused(self) -> None:
        """Test valid transition from CONNECTED to PAUSED."""
        sm = WebSocketStateMachine(state=WebSocketState.CONNECTED)
        sm.transition_to(WebSocketState.PAUSED)
        assert sm.state == WebSocketState.PAUSED

    def test_valid_transition_from_streaming_to_paused(self) -> None:
        """Test valid transition from STREAMING to PAUSED."""
        sm = WebSocketStateMachine(state=WebSocketState.CONNECTED)
        sm.start_streaming()
        sm.pause_streaming()
        assert sm.state == WebSocketState.PAUSED

    def test_valid_transition_from_paused_to_streaming(self) -> None:
        """Test valid transition from PAUSED to STREAMING."""
        sm = WebSocketStateMachine(state=WebSocketState.CONNECTED)
        sm.transition_to(WebSocketState.PAUSED)
        sm.start_streaming()
        assert sm.state == WebSocketState.STREAMING

    def test_valid_transition_to_disconnecting(self) -> None:
        """Test valid transition to DISCONNECTING."""
        sm = WebSocketStateMachine(state=WebSocketState.STREAMING)
        sm.transition_to(WebSocketState.DISCONNECTING)
        assert sm.state == WebSocketState.DISCONNECTING

    def test_valid_transition_to_disconnected(self) -> None:
        """Test valid transition to DISCONNECTED."""
        sm = WebSocketStateMachine(state=WebSocketState.DISCONNECTING)
        sm.transition_to(WebSocketState.DISCONNECTED)
        assert sm.state == WebSocketState.DISCONNECTED

    def test_no_transitions_from_disconnected(self) -> None:
        """Test that no transitions are allowed from DISCONNECTED state."""
        sm = WebSocketStateMachine(state=WebSocketState.DISCONNECTED)
        with pytest.raises(ValueError, match="Invalid transition"):
            sm.transition_to(WebSocketState.CONNECTING)

    def test_can_transition_to_checks_valid_transitions(self) -> None:
        """Test can_transition_to method."""
        sm = WebSocketStateMachine(state=WebSocketState.CONNECTED)
        assert sm.can_transition_to(WebSocketState.STREAMING)
        assert sm.can_transition_to(WebSocketState.PAUSED)
        assert not sm.can_transition_to(WebSocketState.CONNECTING)

    def test_is_streaming_returns_true_when_streaming(self) -> None:
        """Test is_streaming returns True when in STREAMING state."""
        sm = WebSocketStateMachine(state=WebSocketState.CONNECTED)
        assert not sm.is_streaming()
        sm.start_streaming()
        assert sm.is_streaming()

    def test_is_paused_returns_true_when_paused(self) -> None:
        """Test is_paused returns True when in PAUSED state."""
        sm = WebSocketStateMachine(state=WebSocketState.CONNECTED)
        assert not sm.is_paused()
        sm.transition_to(WebSocketState.PAUSED)
        assert sm.is_paused()

    def test_is_connected_returns_true_for_connected_states(self) -> None:
        """Test is_connected returns True for CONNECTED, STREAMING, and PAUSED states."""
        # CONNECTED state
        sm = WebSocketStateMachine(state=WebSocketState.CONNECTED)
        assert sm.is_connected()

        # STREAMING state
        sm.start_streaming()
        assert sm.is_connected()

        # PAUSED state
        sm.pause_streaming()
        assert sm.is_connected()

        # DISCONNECTING state
        sm.disconnect()
        assert not sm.is_connected()

    def test_is_disconnected_returns_true_for_disconnected_states(self) -> None:
        """Test is_disconnected returns True for DISCONNECTING and DISCONNECTED states."""
        sm = WebSocketStateMachine(state=WebSocketState.CONNECTED)
        assert not sm.is_disconnected()

        sm.disconnect()
        assert sm.is_disconnected()

        sm.complete_disconnect()
        assert sm.is_disconnected()

    def test_can_stream_returns_true_when_streaming_possible(self) -> None:
        """Test can_stream returns True when streaming is possible."""
        sm = WebSocketStateMachine(state=WebSocketState.CONNECTED)
        assert sm.can_stream()

        sm.start_streaming()
        assert not sm.can_stream()  # Already streaming

        sm.pause_streaming()
        assert sm.can_stream()  # Can resume

    def test_start_streaming_transitions_to_streaming(self) -> None:
        """Test start_streaming method."""
        sm = WebSocketStateMachine(state=WebSocketState.CONNECTED)
        sm.start_streaming()
        assert sm.state == WebSocketState.STREAMING

    def test_start_streaming_raises_error_when_invalid(self) -> None:
        """Test start_streaming raises error when not allowed."""
        sm = WebSocketStateMachine()  # CONNECTING state
        with pytest.raises(ValueError, match="Invalid transition"):
            sm.start_streaming()

    def test_pause_streaming_transitions_to_paused(self) -> None:
        """Test pause_streaming method."""
        sm = WebSocketStateMachine(state=WebSocketState.CONNECTED)
        sm.start_streaming()
        sm.pause_streaming()
        assert sm.state == WebSocketState.PAUSED

    def test_pause_streaming_raises_error_when_invalid(self) -> None:
        """Test pause_streaming raises error when not allowed."""
        sm = WebSocketStateMachine(state=WebSocketState.CONNECTED)
        with pytest.raises(ValueError, match="Invalid transition"):
            sm.pause_streaming()

    def test_disconnect_from_connected_state(self) -> None:
        """Test disconnect method from CONNECTED state."""
        sm = WebSocketStateMachine(state=WebSocketState.CONNECTED)
        sm.disconnect()
        assert sm.state == WebSocketState.DISCONNECTING

    def test_disconnect_from_disconnected_is_noop(self) -> None:
        """Test disconnect is a no-op when already disconnected."""
        sm = WebSocketStateMachine(state=WebSocketState.DISCONNECTED)
        sm.disconnect()  # Should not raise
        assert sm.state == WebSocketState.DISCONNECTED

    def test_complete_disconnect_transitions_to_disconnected(self) -> None:
        """Test complete_disconnect method."""
        sm = WebSocketStateMachine(state=WebSocketState.DISCONNECTING)
        sm.complete_disconnect()
        assert sm.state == WebSocketState.DISCONNECTED

    def test_complete_disconnect_raises_error_when_invalid(self) -> None:
        """Test complete_disconnect raises error when not in DISCONNECTING state."""
        sm = WebSocketStateMachine(state=WebSocketState.CONNECTED)
        with pytest.raises(ValueError, match="Invalid transition"):
            sm.complete_disconnect()

    def test_full_lifecycle_happy_path(self) -> None:
        """Test a complete successful WebSocket lifecycle."""
        sm = WebSocketStateMachine()

        # Connection phase
        assert sm.state == WebSocketState.CONNECTING
        sm.transition_to(WebSocketState.CONNECTED)
        assert sm.is_connected()

        # Start streaming
        sm.start_streaming()
        assert sm.is_streaming()

        # Pause streaming
        sm.pause_streaming()
        assert sm.is_paused()

        # Resume streaming
        sm.start_streaming()
        assert sm.is_streaming()

        # Disconnect
        sm.disconnect()
        assert sm.state == WebSocketState.DISCONNECTING  # type: ignore[comparison-overlap]

        # Complete disconnect
        sm.complete_disconnect()
        assert sm.state == WebSocketState.DISCONNECTED
        assert sm.is_disconnected()

    def test_error_message_includes_valid_transitions(self) -> None:
        """Test that error messages include valid transition options."""
        sm = WebSocketStateMachine(state=WebSocketState.CONNECTED)
        with pytest.raises(ValueError) as exc_info:
            sm.transition_to(WebSocketState.CONNECTING)

        error_message = str(exc_info.value)
        assert "Invalid transition" in error_message
        assert "streaming" in error_message.lower()
        assert "paused" in error_message.lower()

    def test_transition_rules_are_consistent(self) -> None:
        """Test that transition rules are consistently defined across all states."""
        sm = WebSocketStateMachine()

        # Verify all states have transition rules defined
        for state in WebSocketState:
            assert state in sm._transition_rules

        # Verify no state can transition to itself
        for state, valid_transitions in sm._transition_rules.items():
            assert state not in valid_transitions, f"State {state.value} should not transition to itself"

        # Verify DISCONNECTED has no outgoing transitions (terminal state)
        assert len(sm._transition_rules[WebSocketState.DISCONNECTED]) == 0
