"""API mocking and stubbing for test isolation.

Two mocker types:
- APIMocker: respx-based HTTP mocking for APIDriver (httpx) tests
- BrowserMocker: Playwright route-based interception for web UI tests

Usage::

    # API-level mocking (httpx)
    with api_mocker.mock_response("GET", "/api/members", json=[]) as mock:
        resp = api_driver.get("/api/members")

    # Browser-level mocking (Playwright)
    browser_mocker.intercept("GET", "**/api/members", json={"data": []})
"""

from __future__ import annotations

import json as json_module
import logging
from contextlib import contextmanager
from typing import Any

logger = logging.getLogger(__name__)


class APIMocker:
    """HTTP mock for httpx-based API tests using respx.

    Context manager methods that intercept matching requests and return
    configured responses.
    """

    def __init__(self):
        self._mock = None

    def start(self) -> "APIMocker":
        """Start the respx mock router."""
        import respx

        self._mock = respx.mock(assert_all_called=False)
        self._mock.start()
        logger.info("APIMocker started")
        return self

    def stop(self) -> None:
        """Stop the respx mock router."""
        if self._mock:
            self._mock.stop()
            self._mock.reset()
            logger.info("APIMocker stopped")

    def __enter__(self) -> "APIMocker":
        return self.start()

    def __exit__(self, *args) -> None:
        self.stop()

    @contextmanager
    def mock_response(
        self,
        method: str,
        url_pattern: str,
        status_code: int = 200,
        json: Any = None,
        text: str | None = None,
        headers: dict | None = None,
    ):
        """Mock a specific HTTP response.

        Args:
            method: HTTP method (GET, POST, etc.).
            url_pattern: URL pattern to match.
            status_code: Response status code.
            json: JSON response body.
            text: Text response body.
            headers: Response headers.
        """
        import httpx
        import respx

        route = self._mock.route(method=method, url__regex=f".*{url_pattern}.*")

        response_kwargs: dict[str, Any] = {"status_code": status_code}
        if json is not None:
            response_kwargs["json"] = json
        elif text is not None:
            response_kwargs["text"] = text
        if headers:
            response_kwargs["headers"] = headers

        route.return_value = httpx.Response(**response_kwargs)
        logger.debug(f"Mocked {method} {url_pattern} -> {status_code}")

        try:
            yield route
        finally:
            pass  # Route cleans up when mock stops

    @contextmanager
    def simulate_network_error(self, method: str, url_pattern: str):
        """Simulate a network error for matching requests."""
        import respx

        route = self._mock.route(method=method, url__regex=f".*{url_pattern}.*")
        route.side_effect = ConnectionError("Simulated network error")
        logger.debug(f"Simulated network error for {method} {url_pattern}")

        try:
            yield route
        finally:
            pass

    @contextmanager
    def simulate_slow_response(
        self,
        method: str,
        url_pattern: str,
        delay: float = 5.0,
        status_code: int = 200,
        json: Any = None,
    ):
        """Simulate a slow response with configurable delay."""
        import asyncio
        import httpx
        import respx

        route = self._mock.route(method=method, url__regex=f".*{url_pattern}.*")

        def slow_handler(request):
            import time
            time.sleep(delay)
            return httpx.Response(
                status_code=status_code,
                json=json or {},
            )

        route.side_effect = slow_handler
        logger.debug(f"Simulated slow response ({delay}s) for {method} {url_pattern}")

        try:
            yield route
        finally:
            pass


class BrowserMocker:
    """Playwright route-based request interception for web UI tests.

    Intercepts browser network requests to mock API responses during
    UI testing without needing a real backend.
    """

    def __init__(self, page: Any):
        self._page = page
        self._routes: list[str] = []

    def intercept(
        self,
        method: str,
        url_pattern: str,
        status: int = 200,
        json: Any = None,
        body: str | None = None,
        headers: dict | None = None,
    ) -> "BrowserMocker":
        """Intercept browser requests matching the pattern.

        Args:
            method: HTTP method to match.
            url_pattern: URL glob pattern (e.g., "**/api/members").
            status: Response status code.
            json: JSON response body.
            body: Text response body.
            headers: Response headers.
        """
        response_headers = {"Content-Type": "application/json"}
        if headers:
            response_headers.update(headers)

        response_body = json_module.dumps(json) if json is not None else (body or "")

        def handler(route, request):
            if request.method.upper() == method.upper():
                route.fulfill(
                    status=status,
                    headers=response_headers,
                    body=response_body,
                )
            else:
                route.continue_()

        self._page.route(url_pattern, handler)
        self._routes.append(url_pattern)
        logger.debug(f"Browser intercept: {method} {url_pattern} -> {status}")
        return self

    def simulate_offline(self) -> "BrowserMocker":
        """Simulate offline by aborting all requests."""

        def abort_handler(route):
            route.abort("connectionfailed")

        self._page.route("**/*", abort_handler)
        self._routes.append("**/*")
        logger.info("Browser mock: simulating offline")
        return self

    def clear_all(self) -> "BrowserMocker":
        """Remove all route intercepts."""
        for pattern in self._routes:
            try:
                self._page.unroute(pattern)
            except Exception:
                pass
        self._routes.clear()
        logger.info("Browser mock: all routes cleared")
        return self
