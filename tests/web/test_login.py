"""Web UI tests for login functionality."""

import pytest

from ankole.pages.web.login_page import LoginPage
from tests.test_data import LoginData


@pytest.mark.web
class TestLogin:
    """Test login page functionality."""

    @pytest.fixture(autouse=True)
    def setup(self, web_driver, base_url):
        self.driver = web_driver
        self.login_page = LoginPage(self.driver, base_url=base_url)
        self.td = LoginData.from_env()

    def test_login_success(self):
        """Valid credentials should redirect to dashboard."""
        self.login_page.goto()
        self.login_page.login(self.td.valid_username, self.td.valid_password)
        self.driver.wait_for_url("**/dashboard")
        assert "dashboard" in self.driver.url

    def test_login_invalid_credentials(self):
        """Invalid credentials should show error message."""
        self.login_page.goto()
        error = self.login_page.login_expect_failure(
            self.td.invalid_username, self.td.invalid_password
        )
        assert error, "Expected error message on failed login"

    def test_login_empty_fields(self):
        """Empty fields should not submit or show validation error."""
        self.login_page.goto()
        self.login_page.login("", "")
        assert self.login_page.is_on_login_page()

    @pytest.mark.smoke
    def test_login_page_loads(self):
        """Login page should be accessible."""
        self.login_page.goto()
        assert self.login_page.is_on_login_page()
