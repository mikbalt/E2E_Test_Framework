"""Fixtures for desktop tests (pywinauto)."""

import platform

import pytest


@pytest.fixture
def calculator(request):
    """Provide a Windows Calculator UIDriver instance."""
    if platform.system() != "Windows":
        pytest.skip("Desktop tests require Windows")

    from ankole.driver.ui_driver import UIDriver
    from ankole.plugin.config import load_config

    cfg = load_config()
    calc_config = cfg.get("apps", {}).get("calculator", {})

    driver = UIDriver(
        app_path=calc_config.get("path", "calc.exe"),
        title=calc_config.get("title", "Calculator"),
        backend=calc_config.get("backend", "uia"),
        startup_wait=calc_config.get("startup_wait", 2),
    )
    driver.start()
    yield driver
    driver.close()
