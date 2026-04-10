"""Shared fixtures for all playground exercises."""

import pytest

from ankole.driver.api_driver import APIDriver
from ankole.driver.web_driver import WebDriver
from ankole.plugin.config import load_config


@pytest.fixture(scope="session")
def playground_config():
    """Load configuration for playground exercises."""
    return load_config()


@pytest.fixture
def base_url(playground_config):
    """Web app base URL."""
    return (
        playground_config.get("workspace", {})
        .get("web", {})
        .get("base_url", "http://localhost:5000")
    )


@pytest.fixture
def api_url(playground_config):
    """API base URL."""
    return (
        playground_config.get("workspace", {})
        .get("api", {})
        .get("base_url", "http://localhost:8000")
    )


@pytest.fixture
def web_driver(playground_config):
    """Provide a Playwright WebDriver for exercises."""
    web_cfg = playground_config.get("workspace", {}).get("web", {})
    driver = WebDriver(
        browser_type=web_cfg.get("browser", "chromium"),
        headless=web_cfg.get("headless", True),
        base_url=web_cfg.get("base_url", "http://localhost:5000"),
    )
    driver.start()
    yield driver
    driver.close()


@pytest.fixture
def api_driver(playground_config):
    """Provide an API driver for exercises."""
    api_cfg = playground_config.get("workspace", {}).get("api", {})
    driver = APIDriver(
        base_url=api_cfg.get("base_url", "http://localhost:8000"),
    )
    driver.start()
    yield driver
    driver.close()


@pytest.fixture
def authenticated_api(api_driver):
    """Provide an authenticated API driver."""
    api_driver.login("admin", "admin123")
    return api_driver
