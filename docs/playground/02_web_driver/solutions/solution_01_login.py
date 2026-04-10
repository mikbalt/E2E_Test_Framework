"""Solution: Web Login Automation."""

import pytest


@pytest.mark.web
class TestWebLoginSolution:
    def test_successful_login(self, web_driver, base_url):
        web_driver.goto(f"{base_url}/login")
        web_driver.fill("#username", "admin")
        web_driver.fill("#password", "admin123")
        web_driver.click("button[type=submit]")
        web_driver.wait_for_url("**/dashboard**")
        assert "dashboard" in web_driver.url
