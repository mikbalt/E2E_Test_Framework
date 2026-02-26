"""
tests/ui/conftest.py -- UI-specific fixtures and hooks.

Handles:
- COM threading initialization (required before pywinauto)
- E-Admin specific fixtures (driver that doesn't auto-close)
- UIDriver-level failure screenshots
"""

# --- COM threading: must run BEFORE pywinauto/comtypes is imported ---
import ctypes

try:
    ctypes.windll.ole32.CoInitializeEx(None, 0x2)  # COINIT_APARTMENTTHREADED
except OSError:
    pass

import io
import logging

import pytest

logger = logging.getLogger(__name__)


# ===========================================================================
# E-Admin Fixtures
# ===========================================================================


@pytest.fixture(scope="session")
def e_admin_config(config):
    """Extract e-admin app config once per session."""
    return config.get("apps", {}).get("e_admin", {})


@pytest.fixture
def e_admin_driver(e_admin_config):
    """
    UIDriver for E-Admin that does NOT auto-close the app.

    E-Admin tests require the app to remain open between tests
    for inspection. Only evidence is finalized; the app stays running.
    """
    from hsm_test_framework.ui_driver import UIDriver

    driver = UIDriver(
        app_path=e_admin_config.get("path"),
        class_name=e_admin_config.get("class_name"),
        backend=e_admin_config.get("backend", "uia"),
        startup_wait=e_admin_config.get("startup_wait", 5),
    )
    driver.start()
    yield driver
    # Intentionally NO driver.close() -- app stays open
    logger.info("e_admin_driver fixture finalized - app left open")


# ===========================================================================
# UIDriver Failure Screenshot Hook
# ===========================================================================


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Capture UIDriver window screenshot on test failure (UI tests only).

    This supplements the desktop-level screenshot in plugin.py with a
    window-specific screenshot from UIDriver.
    """
    outcome = yield
    report = outcome.get_result()

    if report.when != "call" or not report.failed:
        return

    # Try to get UIDriver from the test instance or fixtures
    driver = None
    if hasattr(item, "instance") and item.instance is not None:
        driver = getattr(item.instance, "driver", None)
    if driver is None and hasattr(item, "funcargs"):
        driver = item.funcargs.get("e_admin_driver") or item.funcargs.get("ui_app")

    if driver is None or driver.main_window is None:
        return

    try:
        import allure

        img = driver.take_screenshot(f"FAIL_window_{item.name}")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        allure.attach(
            buf.getvalue(),
            name=f"FAIL_window_{item.name}",
            attachment_type=allure.attachment_type.PNG,
        )
        logger.info(f"UIDriver window screenshot attached for {item.name}")
    except Exception as e:
        logger.debug(f"Could not capture UIDriver screenshot: {e}")
