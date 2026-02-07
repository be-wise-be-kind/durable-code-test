"""
Purpose: Mixed HTTP and WebSocket load test scenario with configurable weight ratios

Scope: Combined Locust locustfile importing both BackendHttpUser and OscilloscopeWebSocketUser

Overview: Imports the BackendHttpUser and OscilloscopeWebSocketUser classes into a single
    module namespace so Locust discovers and spawns both User types when this file is loaded.
    Weight ratios between HTTP and WebSocket users are configurable via HTTP_WEIGHT and
    WS_WEIGHT environment variables (defaults: 70/30). When Locust loads this file via
    LOCUST_LOCUSTFILE=locustfiles/mixed_users.py, it discovers both User subclasses through
    module introspection and distributes simulated users according to the configured weights.
    No wrapper classes are needed; setting the weight class attribute on the imported classes
    is sufficient for Locust's user distribution mechanism.

Dependencies: locustfiles.http_users for BackendHttpUser, locustfiles.websocket_users for
    OscilloscopeWebSocketUser, os for environment variable reading

Exports: BackendHttpUser (re-exported with modified weight),
    OscilloscopeWebSocketUser (re-exported with modified weight)

Interfaces: HTTP_WEIGHT and WS_WEIGHT environment variables control user distribution ratio

Implementation: Uses the same sys.path manipulation pattern as websocket_users.py to ensure
    the lib package is importable. Imports both User classes and sets their weight class
    attributes from environment variables before Locust performs module introspection.
"""

import os
import sys
from pathlib import Path

# Add load-testing root to path so lib package and sibling locustfiles are importable
_load_testing_root = str(Path(__file__).resolve().parent.parent)
if _load_testing_root not in sys.path:
    sys.path.insert(0, _load_testing_root)

from locustfiles.http_users import BackendHttpUser
from locustfiles.websocket_users import OscilloscopeWebSocketUser

BackendHttpUser.weight = int(os.environ.get("HTTP_WEIGHT", "70"))
OscilloscopeWebSocketUser.weight = int(os.environ.get("WS_WEIGHT", "30"))
