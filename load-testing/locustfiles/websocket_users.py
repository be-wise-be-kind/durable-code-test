"""
Purpose: WebSocket load test scenario exercising the oscilloscope streaming endpoint

Scope: Locust custom User class for WebSocket protocol testing against the oscilloscope API

Overview: Defines an OscilloscopeWebSocketUser class that exercises the full oscilloscope
    WebSocket protocol sequence: connect, start streaming, receive data frames, reconfigure
    parameters, receive additional frames, stop streaming, and disconnect. Each protocol step
    reports timing metrics to the Locust event system via the LocustWebSocketClient wrapper,
    enabling WebSocket statistics alongside HTTP metrics in the Locust UI. Uses the websockets
    sync client, which cooperates with gevent monkey-patching through standard Python sockets.

Dependencies: Locust framework (User, task, between), lib.websocket_client for WebSocket
    communication and Locust event reporting

Exports: OscilloscopeWebSocketUser class for use by Locust master/worker processes

Interfaces: WebSocket endpoint /api/oscilloscope/stream with JSON command protocol
    (start, configure, stop)

Implementation: Single task executing a full protocol cycle per iteration. Early return on
    connection or receive failure (already reported to Locust). Finally block ensures disconnect.
    To run: set LOCUST_LOCUSTFILE=locustfiles/websocket_users.py
"""

import sys
from pathlib import Path

from locust import User, between, task

# Add load-testing root to path so lib package is importable
_load_testing_root = str(Path(__file__).resolve().parent.parent)
if _load_testing_root not in sys.path:
    sys.path.insert(0, _load_testing_root)

from lib.websocket_client import LocustWebSocketClient, http_to_ws_url

FRAMES_AFTER_START = 5
FRAMES_AFTER_CONFIGURE = 3
WS_STREAM_PATH = "/api/oscilloscope/stream"


class OscilloscopeWebSocketUser(User):
    """Simulates WebSocket traffic against the oscilloscope streaming endpoint.

    Each task iteration executes one full protocol cycle: connect, start,
    receive frames, reconfigure, receive frames, stop, disconnect.
    """

    wait_time = between(2, 5)

    def on_start(self) -> None:
        """Create the WebSocket client instance for this simulated user."""
        self.ws_client = LocustWebSocketClient()

    @task
    def oscilloscope_protocol_cycle(self) -> None:
        """Execute one full oscilloscope WebSocket protocol cycle."""
        ws_url = http_to_ws_url(self.host, WS_STREAM_PATH)

        try:
            if not self.ws_client.connect(ws_url, name="ws connect"):
                return

            if not self.ws_client.send_json(
                {
                    "command": "start",
                    "wave_type": "sine",
                    "frequency": 10.0,
                    "amplitude": 1.0,
                    "offset": 0.0,
                },
                name="ws start",
            ):
                return

            for _ in range(FRAMES_AFTER_START):
                if self.ws_client.receive_json(name="ws receive_frame") is None:
                    return

            if not self.ws_client.send_json(
                {
                    "command": "configure",
                    "frequency": 25.0,
                    "amplitude": 2.0,
                },
                name="ws configure",
            ):
                return

            for _ in range(FRAMES_AFTER_CONFIGURE):
                if self.ws_client.receive_json(name="ws receive_frame") is None:
                    return

            self.ws_client.send_json(
                {"command": "stop"},
                name="ws stop",
            )
        finally:
            self.ws_client.close(name="ws disconnect")
