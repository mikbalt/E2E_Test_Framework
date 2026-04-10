"""Exercise: Web Login Automation.

TODO: Complete the test to log in via the web UI.
"""

import pytest


@pytest.mark.web
class TestWebLogin:
    """Login page automation exercises."""

    def test_successful_login(self, web_driver, base_url):
        """TODO: Fill in the login form and verify successful redirect."""
        # Step 1: Navigate to the login page
        web_driver.goto(f"{base_url}/login")

        # Step 2: Fill in username and password
        # TODO: Use web_driver.fill() for "#username" and "#password"
        web_driver.fill("#username", "admin")
        web_driver.fill("#password", "admin123")

        # Step 3: Click the submit button
        # TODO: Use web_driver.click() on "button[type=submit]"
        web_driver.click("button[type=submit]")

        # Step 4: Verify we landed on the dashboard
        # TODO: Use web_driver.wait_for_url() or check web_driver.url
        web_driver.wait_for_url("**/dashboard**")
        assert "dashboard" in web_driver.url
