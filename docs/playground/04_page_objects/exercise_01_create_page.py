"""Exercise: Create a Page Object.

TODO: Create a LoginPage class following the POM pattern.
"""

import pytest


class LoginPage:
    """Page Object for the Login page.

    TODO: Implement the page object methods.
    """

    URL_PATH = "/login"

    def __init__(self, driver):
        self.driver = driver

    def navigate(self, base_url: str):
        """Navigate to the login page."""
        self.driver.goto(f"{base_url}{self.URL_PATH}")
        return self

    def login(self, username: str, password: str):
        """Fill in credentials and submit the form."""
        self.driver.fill("#username", username)
        self.driver.fill("#password", password)
        self.driver.click("button[type=submit]")
        return self

    def wait_for_dashboard(self):
        """Wait until redirected to dashboard."""
        self.driver.wait_for_url("**/dashboard**")
        return self


@pytest.mark.web
class TestPageObject:
    """Page object exercises."""

    def test_login_via_page_object(self, web_driver, base_url):
        """TODO: Use LoginPage to perform login."""
        page = LoginPage(web_driver)
        page.navigate(base_url)
        page.login("admin", "admin123")
        page.wait_for_dashboard()
        assert "dashboard" in web_driver.url
