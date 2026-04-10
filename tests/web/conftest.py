"""Fixtures for web UI tests (Playwright)."""

import pytest

from ankole.driver.web_driver import WebDriver
from ankole.plugin.config import load_config


@pytest.fixture(scope="session")
def web_config():
    """Load web-specific configuration."""
    cfg = load_config()
    return cfg.get("workspace", {}).get("web", {})


@pytest.fixture
def web_driver(web_config):
    """Provide a Playwright WebDriver for each test."""
    driver = WebDriver(
        browser_type=web_config.get("browser", "chromium"),
        headless=web_config.get("headless", True),
        slow_mo=web_config.get("slow_mo", 0),
        timeout=web_config.get("timeout", 30000),
        viewport=web_config.get("viewport", {"width": 1280, "height": 720}),
        base_url=web_config.get("base_url", "http://localhost:5000"),
    )
    driver.start()
    yield driver
    driver.close()


@pytest.fixture
def base_url(web_config):
    """Base URL for the workspace web app."""
    return web_config.get("base_url", "http://localhost:5000")
