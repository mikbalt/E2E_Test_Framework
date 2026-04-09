"""Login page object for the Workspace web application."""

import logging

from ankole.pages.web.base_web_page import BaseWebPage

logger = logging.getLogger(__name__)


class LoginPage(BaseWebPage):
    """Page object for the login page."""

    # Selectors
    USERNAME_INPUT = "#username"
    PASSWORD_INPUT = "#password"
    LOGIN_BUTTON = "#login-btn"
    ERROR_MESSAGE = ".alert-danger"

    def goto(self) -> "LoginPage":
        """Navigate to the login page."""
        self.navigate_to("/login")
        return self

    def login(self, username: str, password: str) -> None:
        """Perform login with given credentials."""
        with self._web_step(f"Login as {username}"):
            self.driver.fill(self.USERNAME_INPUT, username)
            self.driver.fill(self.PASSWORD_INPUT, password)
            self.driver.click(self.LOGIN_BUTTON)
        logger.info(f"Login submitted for user: {username}")

    def login_expect_failure(self, username: str, password: str) -> str:
        """Attempt login expecting failure. Returns error message."""
        self.login(username, password)
        self.driver.wait_for_selector(self.ERROR_MESSAGE)
        error = self.driver.get_text(self.ERROR_MESSAGE)
        logger.info(f"Login failed as expected: {error}")
        return error

    def get_error_message(self) -> str:
        """Get the error message displayed on login failure."""
        if self.driver.is_visible(self.ERROR_MESSAGE):
            return self.driver.get_text(self.ERROR_MESSAGE)
        return ""

    def is_on_login_page(self) -> bool:
        """Check if currently on the login page."""
        return self.driver.is_visible(self.USERNAME_INPUT)
