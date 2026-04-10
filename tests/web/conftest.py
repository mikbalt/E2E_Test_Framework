"""Fixtures for web UI tests (Playwright)."""

import pytest

from ankole.driver.web_driver import WebDriver
from ankole.plugin.config import load_config


def pytest_generate_tests(metafunc):
    """Parametrize web_driver across configured browsers.

    If the test function uses the `web_driver` fixture, this hook
    parametrizes it across all browsers listed in settings.yaml at
    `workspace.web.browsers` (default: ["chromium"]).
    """
    if "web_driver" in metafunc.fixturenames:
        cfg = load_config()
        web_cfg = cfg.get("workspace", {}).get("web", {})
        browsers = web_cfg.get("browsers", [web_cfg.get("browser", "chromium")])
        if len(browsers) > 1:
            metafunc.parametrize("web_driver", browsers, indirect=True)


@pytest.fixture(scope="session")
def web_config():
    """Load web-specific configuration."""
    cfg = load_config()
    return cfg.get("workspace", {}).get("web", {})


@pytest.fixture
def web_driver(request, web_config):
    """Provide a Playwright WebDriver for each test.

    Supports browser parametrization via pytest_generate_tests.
    """
    # If parametrized, request.param is the browser type
    browser_type = getattr(request, "param", None) or web_config.get("browser", "chromium")

    device_cfg = web_config.get("device_emulation", {})
    device_name = device_cfg.get("device_name") if device_cfg.get("enabled") else None

    driver = WebDriver(
        browser_type=browser_type,
        headless=web_config.get("headless", True),
        slow_mo=web_config.get("slow_mo", 0),
        timeout=web_config.get("timeout", 30000),
        viewport=web_config.get("viewport", {"width": 1280, "height": 720}),
        base_url=web_config.get("base_url", "http://localhost:5000"),
        device_name=device_name,
    )
    driver.start()
    yield driver
    driver.close()


@pytest.fixture
def base_url(web_config):
    """Base URL for the workspace web app."""
    return web_config.get("base_url", "http://localhost:5000")
