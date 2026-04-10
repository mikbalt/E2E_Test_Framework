"""Base web page object for Playwright-based automation.

Provides shared helpers: evidence-tracked steps, navigation, and element interaction.
All web page objects should inherit from this class.
"""

import logging
from contextlib import contextmanager
from typing import Any

from ankole.pages.base_page import BasePage

logger = logging.getLogger(__name__)


class BaseWebPage(BasePage):
    """Base class for Playwright web page objects.

    Args:
        driver: WebDriver instance.
        evidence: Evidence instance for screenshots/logging.
        base_url: Base URL of the web application.
    """

    def __init__(self, driver, evidence=None, base_url: str = ""):
        super().__init__(driver, evidence)
        self.base_url = base_url.rstrip("/")

    def navigate_to(self, path: str) -> None:
        """Navigate to a path relative to base_url."""
        url = f"{self.base_url}{path}" if self.base_url else path
        self.driver.goto(url)

    def get_flash_messages(self) -> list[str]:
        """Get all flash/alert messages on the page."""
        if self.driver.is_visible(".alert"):
            return self.driver.get_all_elements_text(".alert")
        return []

    def get_page_title(self) -> str:
        """Get the page title from the <h1> or <title> tag."""
        if self.driver.is_visible("h1"):
            return self.driver.get_text("h1").strip()
        return self.driver.title

    def is_logged_in(self) -> bool:
        """Check if the user is currently logged in."""
        return self.driver.is_visible("#sidebar") or self.driver.is_visible("nav .logout")

    def click_sidebar_link(self, text: str) -> None:
        """Click a sidebar navigation link by its text."""
        self.driver.click(f"#sidebar a:has-text('{text}')")

    @contextmanager
    def _web_step(self, description: str, screenshot: bool = True):
        """Wrap a block in an evidence step with optional screenshot."""
        if self.evidence and description:
            try:
                import allure
                with allure.step(description):
                    yield
                    if screenshot:
                        self.driver.take_screenshot(
                            f"step_{description.replace(' ', '_')[:40]}"
                        )
            except ImportError:
                yield
        else:
            yield
