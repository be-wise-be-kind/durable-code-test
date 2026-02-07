"""
Purpose: WebSocket client wrapper with Locust event reporting for load testing

Scope: Shared WebSocket communication layer for Locust custom User classes

Overview: Provides a LocustWebSocketClient class that wraps the websockets sync client library
    to manage WebSocket connections during load tests. Each operation (connect, send, receive,
    close) measures response time and reports success or failure to the Locust event system,
    enabling WebSocket metrics to appear alongside HTTP metrics in the Locust UI. Includes a
    utility function for converting HTTP host URLs to WebSocket URLs. Uses the websockets sync
    API, which relies on standard Python sockets compatible with gevent monkey-patching.

Dependencies: websockets (sync client), Locust (environment events for metric reporting), json

Exports: LocustWebSocketClient class, http_to_ws_url utility function

Interfaces: connect(url, name), send_json(data, name), receive_json(name, timeout),
    close(name), is_connected property

Implementation: Each method catches specific exceptions (ConnectionClosed, TimeoutError,
    OSError, json.JSONDecodeError) and reports them as Locust failures without re-raising.
    The calling User class checks is_connected or return values to decide whether to continue.
"""

import json
import time
from urllib.parse import urlparse, urlunparse

from websockets.exceptions import ConnectionClosed, InvalidStatus
from websockets.sync.client import ClientConnection, connect

from locust import events

DEFAULT_OPEN_TIMEOUT = 10
DEFAULT_RECV_TIMEOUT = 5
WS_REQUEST_TYPE = "WebSocket"


def http_to_ws_url(http_url: str, ws_path: str) -> str:
    """Convert an HTTP/HTTPS URL to a WebSocket URL with the given path.

    Swaps http:// to ws:// and https:// to wss://, then appends the
    specified path.
    """
    parsed = urlparse(http_url)
    scheme_map = {"http": "ws", "https": "wss"}
    ws_scheme = scheme_map.get(parsed.scheme, "ws")
    ws_parsed = parsed._replace(scheme=ws_scheme, path=ws_path)
    return urlunparse(ws_parsed)


class LocustWebSocketClient:
    """WebSocket client that reports timing metrics to the Locust event system.

    Each public method measures elapsed time and fires a Locust request event
    on success or failure, enabling WebSocket stats in the Locust UI.
    """

    def __init__(self) -> None:
        self._ws: ClientConnection | None = None

    @property
    def is_connected(self) -> bool:
        """Return True if the WebSocket connection is open."""
        return self._ws is not None

    def connect(self, url: str, name: str = "ws connect") -> bool:
        """Open a WebSocket connection and report timing to Locust.

        Returns True on success, False on failure.
        """
        start = time.perf_counter()
        try:
            self._ws = connect(url, open_timeout=DEFAULT_OPEN_TIMEOUT)
            elapsed_ms = (time.perf_counter() - start) * 1000
            self._fire_event(name, elapsed_ms, 0)
        except (OSError, TimeoutError, InvalidStatus) as exc:
            elapsed_ms = (time.perf_counter() - start) * 1000
            self._fire_event(name, elapsed_ms, 0, exc)
            self._ws = None
            return False
        return True

    def send_json(
        self, data: dict, name: str = "ws send"
    ) -> bool:
        """Serialize data as JSON and send over the WebSocket.

        Returns True on success, False on failure.
        """
        start = time.perf_counter()
        try:
            payload = json.dumps(data)
            if self._ws is None:
                msg = "WebSocket not connected"
                raise OSError(msg)
            self._ws.send(payload)
            elapsed_ms = (time.perf_counter() - start) * 1000
            self._fire_event(name, elapsed_ms, len(payload))
        except (ConnectionClosed, OSError) as exc:
            elapsed_ms = (time.perf_counter() - start) * 1000
            self._fire_event(name, elapsed_ms, 0, exc)
            self._ws = None
            return False
        return True

    def receive_json(
        self,
        name: str = "ws receive",
        timeout: float = DEFAULT_RECV_TIMEOUT,
    ) -> dict | None:
        """Receive a JSON message from the WebSocket.

        Returns the parsed dict on success, None on failure.
        """
        start = time.perf_counter()
        try:
            if self._ws is None:
                msg = "WebSocket not connected"
                raise OSError(msg)
            raw = self._ws.recv(timeout=timeout)
            data: dict = json.loads(raw)
            elapsed_ms = (time.perf_counter() - start) * 1000
            response_length = len(raw) if isinstance(raw, (str, bytes)) else 0
            self._fire_event(name, elapsed_ms, response_length)
        except (ConnectionClosed, TimeoutError, OSError) as exc:
            elapsed_ms = (time.perf_counter() - start) * 1000
            self._fire_event(name, elapsed_ms, 0, exc)
            self._ws = None
            return None
        except json.JSONDecodeError as exc:
            elapsed_ms = (time.perf_counter() - start) * 1000
            self._fire_event(name, elapsed_ms, 0, exc)
            return None
        return data

    def close(self, name: str = "ws disconnect") -> None:
        """Close the WebSocket connection and report timing to Locust."""
        if self._ws is None:
            return
        start = time.perf_counter()
        try:
            self._ws.close()
            elapsed_ms = (time.perf_counter() - start) * 1000
            self._fire_event(name, elapsed_ms, 0)
        except (ConnectionClosed, OSError) as exc:
            elapsed_ms = (time.perf_counter() - start) * 1000
            self._fire_event(name, elapsed_ms, 0, exc)
        finally:
            self._ws = None

    def _fire_event(
        self,
        name: str,
        response_time: float,
        response_length: int,
        exception: BaseException | None = None,
    ) -> None:
        """Report a request event to the Locust event system."""
        if exception is not None:
            events.request.fire(
                request_type=WS_REQUEST_TYPE,
                name=name,
                response_time=response_time,
                response_length=response_length,
                exception=exception,
            )
        else:
            events.request.fire(
                request_type=WS_REQUEST_TYPE,
                name=name,
                response_time=response_time,
                response_length=response_length,
            )
