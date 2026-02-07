"""
Purpose: Browser-based load test scenarios using Playwright for frontend interaction testing

Scope: Locust PlaywrightUser definitions exercising frontend UI journeys through real browser
    instances against the Durable Code application

Overview: Defines three PlaywrightUser subclasses that exercise distinct frontend user journeys
    through real Chromium browser instances. OscilloscopePlaywrightUser validates the full
    oscilloscope WebSocket demo flow (navigate, auto-connect, start, change waveform, stop).
    RacingPlaywrightUser exercises the racing game with canvas interaction and REST API track
    generation. TabNavigationPlaywrightUser measures SPA navigation performance across all
    application tabs. Each step within a task reports timing metrics to the Locust event system
    via the locust-plugins event context manager, enabling per-action statistics in the Locust
    UI. Browser instances are resource-heavy; limit to 4-5 concurrent users per worker.

Dependencies: locust (task), locust-plugins (PlaywrightUser, pw, event, PageWithRetry),
    os for frontend host configuration

Exports: OscilloscopePlaywrightUser, RacingPlaywrightUser, TabNavigationPlaywrightUser classes
    for use by Locust master/worker processes

Interfaces: Frontend UI at LOAD_TEST_FRONTEND_HOST (default http://host.docker.internal:5173),
    backend API at LOCUST_HOST for REST calls triggered by frontend components

Implementation: Each PlaywrightUser subclass uses the @pw decorator for browser lifecycle
    management and the event() context manager for per-step metric reporting. Selectors use
    text-based and semantic patterns (not CSS module class names) for stability across builds.
    Uses wait_until="domcontentloaded" for SPA page loads to prevent stalling on streaming
    resources
"""

import os

from locust import constant, task
from locust_plugins.users.playwright import PageWithRetry, PlaywrightUser, event, pw

FRONTEND_HOST = os.environ.get(
    "LOAD_TEST_FRONTEND_HOST", "http://host.docker.internal:5173"
)

TAB_NAMES = [
    "Repository",
    "Planning",
    "Building",
    "Quality Assurance",
    "Maintenance",
    "Demo",
    "Journey",
]


class OscilloscopePlaywrightUser(PlaywrightUser):
    """Exercises the full oscilloscope WebSocket demo journey through a browser.

    Flow: navigate to frontend, click Demo tab, open oscilloscope, wait for
    auto-connect, start streaming, change waveform type, wait for data, stop.
    """

    host = FRONTEND_HOST
    wait_time = constant(0)

    @task
    @pw
    async def oscilloscope_journey(self, page: PageWithRetry) -> None:
        """Execute one full oscilloscope browser journey."""
        async with event(self, "page_load"):
            await page.goto("/", wait_until="domcontentloaded")
            await page.wait_for_selector("#root", timeout=10000)

        async with event(self, "navigate_to_demo"):
            await page.click('button:has-text("Demo")')
            await page.wait_for_timeout(500)

        async with event(self, "open_oscilloscope"):
            oscilloscope_link = page.get_by_role(
                "heading", name="Oscilloscope"
            )
            await oscilloscope_link.click()
            await page.wait_for_timeout(1000)

        async with event(self, "wait_for_connection"):
            await page.wait_for_selector(
                'text=Connected', timeout=10000
            )

        async with event(self, "click_start"):
            start_btn = page.get_by_role("button", name="Start")
            await start_btn.click()
            await page.wait_for_timeout(500)

        async with event(self, "change_waveform"):
            square_btn = page.get_by_text("Square Wave")
            await square_btn.click()
            await page.wait_for_timeout(500)

        async with event(self, "wait_for_streaming"):
            await page.wait_for_timeout(2000)

        async with event(self, "click_stop"):
            stop_btn = page.get_by_role("button", name="Stop")
            await stop_btn.click()


class RacingPlaywrightUser(PlaywrightUser):
    """Exercises the racing game with REST API track generation and canvas interaction.

    Flow: navigate to frontend, click Demo tab, open racing game, wait for
    auto-loaded track, click Start, simulate mouse movement on canvas.
    """

    host = FRONTEND_HOST
    wait_time = constant(0)

    @task
    @pw
    async def racing_journey(self, page: PageWithRetry) -> None:
        """Execute one full racing game browser journey."""
        async with event(self, "page_load"):
            await page.goto("/", wait_until="domcontentloaded")
            await page.wait_for_selector("#root", timeout=10000)

        async with event(self, "navigate_to_demo"):
            await page.click('button:has-text("Demo")')
            await page.wait_for_timeout(500)

        async with event(self, "open_racing_game"):
            racing_link = page.get_by_role(
                "heading", name="Racing Game"
            )
            await racing_link.click()
            await page.wait_for_timeout(500)

        async with event(self, "wait_for_track_load"):
            await page.wait_for_selector("canvas", timeout=10000)
            await page.wait_for_timeout(1000)

        async with event(self, "click_start_racing"):
            start_btn = page.get_by_role(
                "button", name="Start Racing"
            )
            await start_btn.click()
            await page.wait_for_timeout(500)

        async with event(self, "canvas_mouse_interaction"):
            canvas = page.locator("canvas").first
            bounding_box = await canvas.bounding_box()
            if bounding_box:
                center_x = bounding_box["x"] + bounding_box["width"] / 2
                center_y = bounding_box["y"] + bounding_box["height"] / 2
                await page.mouse.move(center_x, center_y)
                await page.mouse.move(center_x + 50, center_y + 30)
                await page.mouse.move(center_x - 30, center_y + 50)
            await page.wait_for_timeout(3000)


class TabNavigationPlaywrightUser(PlaywrightUser):
    """Measures SPA navigation performance by clicking through all application tabs.

    Flow: navigate to frontend, loop through all tabs clicking each one and
    waiting for content render. Each tab click is reported as a separate Locust event.
    """

    host = FRONTEND_HOST
    wait_time = constant(0)

    @task
    @pw
    async def tab_navigation_journey(self, page: PageWithRetry) -> None:
        """Navigate through all application tabs measuring load times."""
        async with event(self, "page_load"):
            await page.goto("/", wait_until="domcontentloaded")
            await page.wait_for_selector("#root", timeout=10000)

        for tab_name in TAB_NAMES:
            async with event(self, f"tab_{tab_name.lower().replace(' ', '_')}"):
                await page.click(f'button:has-text("{tab_name}")')
                await page.wait_for_timeout(500)
