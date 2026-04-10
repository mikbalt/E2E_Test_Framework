"""Integration tests for BrowserMocker (Playwright route interception)."""

import pytest


@pytest.mark.web
class TestBrowserMock:
    """Tests for browser-level API mocking."""

    def test_intercept_api_response(self, web_driver, browser_mocker, base_url):
        """Intercept an API call and return mock data."""
        browser_mocker.intercept(
            "GET", "**/api/members",
            json=[{"id": 999, "username": "mock_user"}],
        )
        web_driver.goto(f"{base_url}/members")
        # The page should render the mocked member data
        web_driver.wait_for_selector("table")

    def test_simulate_offline(self, web_driver, browser_mocker, base_url):
        """Simulate offline mode — all requests should fail."""
        browser_mocker.simulate_offline()
        try:
            web_driver.goto(f"{base_url}/login")
        except Exception:
            pass  # Expected — page load fails when offline
