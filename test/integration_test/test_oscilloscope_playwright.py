#!/usr/bin/env python3
"""
Purpose: Validates oscilloscope functionality through end-to-end browser automation

Scope: WebSocket connection establishment, real-time data streaming, UI control interactions, waveform visualization, and error handling

Overview: End-to-end integration tests using Playwright to validate oscilloscope functionality including
    WebSocket connections, real-time data streaming, user interface interactions, waveform visualization,
    control panel operations, and error handling scenarios across the complete technology stack from frontend
    to backend. Tests verify browser compatibility, UI responsiveness, data accuracy, and user workflow
    completeness. The suite ensures proper integration between frontend components and backend services
    through realistic user interaction patterns and comprehensive scenario coverage.

Dependencies: playwright, pytest, asyncio

Exports: Playwright-based integration test classes and browser automation fixtures for oscilloscope testing

Interfaces: Async pytest fixtures and test methods using Playwright browser automation API

Implementation: Uses Playwright to automate browser interactions and validate the oscilloscope functionality across the full stack
"""

import asyncio
import json
import os
from collections.abc import AsyncGenerator
from typing import Any

import pytest
import pytest_asyncio
from loguru import logger

# Conditional import to prevent import errors when playwright is not available
try:
    from playwright.async_api import (  # type: ignore[import-not-found,import-untyped,unused-ignore]
        Page,
        WebSocket,
        async_playwright,
    )

    PLAYWRIGHT_AVAILABLE = True
except ImportError as e:
    logger.debug("Playwright not available", error=str(e))
    PLAYWRIGHT_AVAILABLE = False
    # When playwright is not available, create placeholders to prevent NameError
    Page = Any  # type: ignore[misc,assignment,unused-ignore]
    WebSocket = Any  # type: ignore[misc,assignment,unused-ignore]
    async_playwright = None  # type: ignore[assignment,unused-ignore]

# Enable auto mode for async fixtures
pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture(scope="function")
async def browser() -> AsyncGenerator[Any, None]:
    """Create a browser instance for testing."""
    if not PLAYWRIGHT_AVAILABLE or async_playwright is None:
        pytest.skip("Playwright not available")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        yield browser
        await browser.close()


@pytest_asyncio.fixture(scope="function")
async def page(browser: Any) -> Any:
    """Create a page instance for testing."""
    context = await browser.new_context()
    page = await context.new_page()
    yield page
    await context.close()


# Tests now properly configured to run with branch-based container names
class TestOscilloscopeIntegration:
    """Integration tests for oscilloscope functionality."""

    @property
    def frontend_url(self) -> str:
        """Get the frontend URL based on environment variables."""
        # Check if using host network (local dev) or bridge network (CI)
        use_host_network = os.getenv("USE_HOST_NETWORK", "false").lower() == "true"
        frontend_port = os.getenv("FRONTEND_PORT", "5173")

        if use_host_network:
            # Local development with --network host
            return f"http://localhost:{frontend_port}"
        else:
            # CI with bridge network - use container name
            branch_name = os.getenv("BRANCH_NAME", "main")
            container_name = f"durable-code-frontend-{branch_name}-dev"
            return f"http://{container_name}:5173"

    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not available")
    @pytest.mark.skipif(os.getenv("RUN_PLAYWRIGHT_TESTS") != "true", reason="Playwright tests require special setup")
    async def test_oscilloscope_page_loads(self, page: Any) -> None:
        """Test that the oscilloscope page loads successfully."""
        # Navigate to the app - use container name for Docker network
        await page.goto(self.frontend_url)

        # Wait for the app to load
        await page.wait_for_selector("#root", timeout=10000)

        # Check that the Demo tab exists
        demo_tab = await page.query_selector('button:has-text("Demo")')
        assert demo_tab is not None, "Demo tab not found"

        # Click the Demo tab
        await demo_tab.click()

        # Wait for oscilloscope components to load
        await page.wait_for_selector("canvas", timeout=5000)

        # Verify canvas is present
        canvas = await page.query_selector("canvas")
        assert canvas is not None, "Oscilloscope canvas not found"

    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not available")
    @pytest.mark.skipif(os.getenv("RUN_PLAYWRIGHT_TESTS") != "true", reason="Playwright tests require special setup")
    async def test_websocket_connection(self, page: Any) -> None:
        """Test that WebSocket connection is established."""
        ws_connected = False
        ws_messages = []

        # Set up WebSocket event handlers
        def on_websocket(ws: Any) -> None:
            nonlocal ws_connected
            ws_connected = True

            def on_message(message: str) -> None:
                try:
                    data = json.loads(message)
                    ws_messages.append(data)
                except json.JSONDecodeError as e:
                    logger.error("Failed to parse WebSocket message as JSON", error=str(e), exc_info=True)

            ws.on("framereceived", lambda payload: on_message(payload if isinstance(payload, str) else ""))

        page.on("websocket", on_websocket)

        # Navigate to the app
        await page.goto(self.frontend_url)

        # Wait for the Demo tab and click it
        await page.wait_for_selector('button:has-text("Demo")', timeout=10000)
        await page.click('button:has-text("Demo")')

        # Wait for WebSocket connection
        await asyncio.sleep(2)

        assert ws_connected, "WebSocket connection was not established"
        assert len(ws_messages) > 0, "No WebSocket messages received"

    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not available")
    @pytest.mark.skipif(os.getenv("RUN_PLAYWRIGHT_TESTS") != "true", reason="Playwright tests require special setup")
    async def test_oscilloscope_controls(self, page: Any) -> None:
        """Test oscilloscope control interactions."""
        # Navigate to the Demo tab
        await page.goto(self.frontend_url)
        await page.wait_for_selector('button:has-text("Demo")', timeout=10000)
        await page.click('button:has-text("Demo")')

        # Wait for controls to load - check for Connect button or canvas
        try:
            await page.wait_for_selector('button:has-text("Connect")', timeout=2000)
            connect_button = await page.query_selector('button:has-text("Connect")')
        except Exception as e:
            # If no Connect button, app might auto-connect
            logger.debug("Connect button not found, app might auto-connect", error=str(e))
            connect_button = None
            await page.wait_for_selector("canvas", timeout=3000)

        # Click Connect button if present

        if connect_button:
            await connect_button.click()
            await asyncio.sleep(1)

        # Test waveform selector if present
        waveform_selector = await page.query_selector("select")
        if waveform_selector:
            # Change waveform type
            await waveform_selector.select_option("square")
            await asyncio.sleep(0.5)

            await waveform_selector.select_option("triangle")
            await asyncio.sleep(0.5)

            await waveform_selector.select_option("sine")
            await asyncio.sleep(0.5)

        # Test frequency control if present
        frequency_input = await page.query_selector('input[type="range"]')
        if frequency_input:
            # Adjust frequency using evaluate for range inputs
            await page.evaluate("(el) => el.value = 5", frequency_input)
            await page.evaluate('(el) => el.dispatchEvent(new Event("input", { bubbles: true }))', frequency_input)
            await asyncio.sleep(0.5)

    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not available")
    @pytest.mark.skipif(os.getenv("RUN_PLAYWRIGHT_TESTS") != "true", reason="Playwright tests require special setup")
    async def test_oscilloscope_data_streaming(self, page: Any) -> None:
        """Test that oscilloscope receives and displays streaming data."""
        # Navigate to Demo tab
        await page.goto(self.frontend_url)
        await page.wait_for_selector('button:has-text("Demo")', timeout=10000)
        await page.click('button:has-text("Demo")')

        # Wait for canvas
        await page.wait_for_selector("canvas", timeout=5000)

        # Click Connect if button exists
        connect_button = await page.query_selector('button:has-text("Connect")')
        if connect_button:
            await connect_button.click()

        # Wait for data streaming
        await asyncio.sleep(3)

        # Check if canvas has been rendered (by checking its data URL changes)
        canvas = await page.query_selector("canvas")
        if canvas:
            # Take two snapshots of the canvas
            snapshot1 = await canvas.screenshot()
            await asyncio.sleep(1)
            snapshot2 = await canvas.screenshot()

            # If data is streaming, the snapshots should be different
            assert snapshot1 != snapshot2, "Canvas is not updating - no data streaming detected"

    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not available")
    @pytest.mark.skipif(os.getenv("RUN_PLAYWRIGHT_TESTS") != "true", reason="Playwright tests require special setup")
    async def test_oscilloscope_disconnect_reconnect(self, page: Any) -> None:
        """Test disconnect and reconnect functionality."""
        # Navigate to Demo tab
        await page.goto(self.frontend_url)
        await page.wait_for_selector('button:has-text("Demo")', timeout=10000)
        await page.click('button:has-text("Demo")')

        # Connect
        connect_button = await page.query_selector('button:has-text("Connect")')
        if connect_button:
            await connect_button.click()
            await asyncio.sleep(1)

            # Look for Disconnect button
            disconnect_button = await page.query_selector('button:has-text("Disconnect")')
            if disconnect_button:
                # Disconnect
                await disconnect_button.click()
                await asyncio.sleep(1)

                # Reconnect
                connect_button = await page.query_selector('button:has-text("Connect")')
                if connect_button:
                    await connect_button.click()
                    await asyncio.sleep(1)

                    # Verify connection is re-established
                    disconnect_button = await page.query_selector('button:has-text("Disconnect")')
                    assert disconnect_button is not None, "Reconnection failed"

    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not available")
    @pytest.mark.skipif(os.getenv("RUN_PLAYWRIGHT_TESTS") != "true", reason="Playwright tests require special setup")
    async def test_oscilloscope_error_handling(self, page: Any) -> None:
        """Test error handling when backend is unavailable."""
        # Stop the backend (simulate failure)
        # This would need to be coordinated with Docker commands

        # For now, test that the UI handles errors gracefully
        await page.goto(self.frontend_url)
        await page.wait_for_selector('button:has-text("Demo")', timeout=10000)
        await page.click('button:has-text("Demo")')

        # The app should still load even if WebSocket fails
        await page.wait_for_selector("canvas", timeout=5000)
        canvas = await page.query_selector("canvas")
        assert canvas is not None, "App failed to load canvas element"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
