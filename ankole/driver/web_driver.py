"""Playwright-based web UI driver.

Wraps Playwright's sync API with a consistent interface for page objects::

    from ankole.driver.web_driver import WebDriver

    with WebDriver(headless=True) as driver:
        driver.goto("http://localhost:5000")
        driver.fill("#username", "admin")
        driver.click("button[type=submit]")
"""

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


class WebDriver:
    """Playwright wrapper for web UI automation.

    Supports context manager protocol for automatic cleanup.
    """

    def __init__(
        self,
        browser_type: str = "chromium",
        headless: bool = True,
        slow_mo: float = 0,
        timeout: int = 30000,
        viewport: dict | None = None,
        base_url: str | None = None,
        evidence_dir: str = "evidence/screenshots",
        device_name: str | None = None,
    ):
        self.browser_type = browser_type
        self.headless = headless
        self.slow_mo = slow_mo
        self.timeout = timeout
        self.viewport = viewport or {"width": 1280, "height": 720}
        self.base_url = base_url
        self.evidence_dir = evidence_dir
        self.device_name = device_name

        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None

    @property
    def page(self):
        """Current Playwright page object."""
        return self._page

    def start(self, **kwargs) -> "WebDriver":
        """Launch browser and create a new page."""
        from playwright.sync_api import sync_playwright

        self._playwright = sync_playwright().start()

        launcher = getattr(self._playwright, self.browser_type)
        self._browser = launcher.launch(
            headless=self.headless,
            slow_mo=self.slow_mo,
        )

        # Device emulation support
        context_kwargs = {
            "viewport": self.viewport,
            "base_url": self.base_url,
        }
        if self.device_name:
            device = self._playwright.devices.get(self.device_name)
            if device:
                context_kwargs.update(device)
                logger.info(f"Emulating device: {self.device_name}")

        self._context = self._browser.new_context(**context_kwargs)
        self._context.set_default_timeout(self.timeout)
        self._page = self._context.new_page()

        logger.info(
            f"WebDriver started: {self.browser_type} "
            f"(headless={self.headless})"
        )
        return self

    def close(self) -> None:
        """Close browser and cleanup Playwright."""
        if self._context:
            self._context.close()
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()
        logger.info("WebDriver closed")

    def __enter__(self) -> "WebDriver":
        return self.start()

    def __exit__(self, *args) -> None:
        self.close()

    # -- Navigation -----------------------------------------------------------

    def goto(self, url: str) -> None:
        """Navigate to a URL."""
        self._page.goto(url)
        logger.debug(f"Navigated to: {url}")

    def reload(self) -> None:
        """Reload the current page."""
        self._page.reload()

    @property
    def url(self) -> str:
        """Current page URL."""
        return self._page.url

    @property
    def title(self) -> str:
        """Current page title."""
        return self._page.title()

    # -- Interactions ---------------------------------------------------------

    def click(self, selector: str) -> None:
        """Click an element by CSS selector."""
        self._page.click(selector)
        logger.debug(f"Clicked: {selector}")

    def fill(self, selector: str, value: str) -> None:
        """Fill a text input by CSS selector."""
        self._page.fill(selector, value)
        logger.debug(f"Filled: {selector}")

    def select_option(self, selector: str, value: str) -> None:
        """Select an option from a dropdown."""
        self._page.select_option(selector, value)
        logger.debug(f"Selected: {selector} = {value}")

    def check(self, selector: str) -> None:
        """Check a checkbox."""
        self._page.check(selector)

    def uncheck(self, selector: str) -> None:
        """Uncheck a checkbox."""
        self._page.uncheck(selector)

    # -- Text retrieval -------------------------------------------------------

    def get_text(self, selector: str) -> str:
        """Get text content of an element."""
        return self._page.text_content(selector) or ""

    def get_input_value(self, selector: str) -> str:
        """Get value of an input element."""
        return self._page.input_value(selector)

    def get_attribute(self, selector: str, attribute: str) -> str | None:
        """Get an attribute value from an element."""
        return self._page.get_attribute(selector, attribute)

    # -- Waits & queries ------------------------------------------------------

    def wait_for_selector(self, selector: str, timeout: float | None = None) -> Any:
        """Wait for an element to appear."""
        kwargs = {}
        if timeout is not None:
            kwargs["timeout"] = timeout
        return self._page.wait_for_selector(selector, **kwargs)

    def wait_for_url(self, url_pattern: str, timeout: float | None = None) -> None:
        """Wait for URL to match pattern."""
        kwargs = {}
        if timeout is not None:
            kwargs["timeout"] = timeout
        self._page.wait_for_url(url_pattern, **kwargs)

    def is_visible(self, selector: str) -> bool:
        """Check if an element is visible."""
        return self._page.is_visible(selector)

    def is_enabled(self, selector: str) -> bool:
        """Check if an element is enabled."""
        return self._page.is_enabled(selector)

    def count(self, selector: str) -> int:
        """Count elements matching selector."""
        return self._page.locator(selector).count()

    # -- Table data -----------------------------------------------------------

    def get_table_data(self, selector: str) -> list[dict[str, str]]:
        """Extract table data as list of dicts (header -> cell value).

        Args:
            selector: CSS selector for the <table> element.

        Returns:
            List of dicts, one per row, keyed by header text.
        """
        table = self._page.locator(selector)
        headers = table.locator("thead th").all_text_contents()
        rows = table.locator("tbody tr").all()

        data = []
        for row in rows:
            cells = row.locator("td").all_text_contents()
            row_dict = {
                headers[i]: cells[i] if i < len(cells) else ""
                for i in range(len(headers))
            }
            data.append(row_dict)
        return data

    # -- Screenshots ----------------------------------------------------------

    def take_screenshot(self, name: str = "screenshot") -> str:
        """Take a screenshot and save to evidence directory.

        Returns:
            Path to saved screenshot.
        """
        os.makedirs(self.evidence_dir, exist_ok=True)
        filepath = os.path.join(self.evidence_dir, f"{name}.png")
        self._page.screenshot(path=filepath)
        logger.info(f"Screenshot saved: {filepath}")

        try:
            import allure
            with open(filepath, "rb") as f:
                allure.attach(
                    f.read(),
                    name=name,
                    attachment_type=allure.attachment_type.PNG,
                )
        except ImportError:
            pass

        return filepath

    # -- Alert handling -------------------------------------------------------

    def accept_dialog(self) -> None:
        """Auto-accept the next dialog (alert/confirm/prompt)."""
        self._page.on("dialog", lambda dialog: dialog.accept())

    def dismiss_dialog(self) -> None:
        """Auto-dismiss the next dialog."""
        self._page.on("dialog", lambda dialog: dialog.dismiss())
