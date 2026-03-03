"""
tests/ui/conftest.py -- Shared UI fixtures and hooks.

Handles:
- COM threading initialization (required before pywinauto)
- pywinauto warning filter
- UIDriver-level failure screenshots

Component-specific fixtures live in sub-packages (e.g. e_admin/conftest.py).
"""

# --- COM threading: must run BEFORE pywinauto/comtypes is imported ---
import sys
import ctypes

# Tell comtypes to use STA (same mode we set below), otherwise it
# defaults to COINIT_MULTITHREADED and conflicts with our CoInitializeEx.
sys.coinit_flags = 2  # COINIT_APARTMENTTHREADED

try:
    ctypes.windll.ole32.CoInitializeEx(None, 0x2)  # COINIT_APARTMENTTHREADED
except OSError:
    pass

import io
import logging
import warnings

import pytest

# Suppress pywinauto's "Apply externally defined coinit_flags" noise —
# we set coinit_flags intentionally above; the warning is expected.
warnings.filterwarnings("ignore", message="Apply externally defined coinit_flags")

logger = logging.getLogger(__name__)


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
