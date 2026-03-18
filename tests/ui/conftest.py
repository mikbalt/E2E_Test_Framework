"""
tests/ui/conftest.py -- Shared UI fixtures and hooks.

Handles:
- COM threading initialization (required before pywinauto)
- pywinauto warning filter
- UIDriver-level failure screenshots
- TCMS dependency-tracking hooks (shared across all app suites)
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

# --- TCMS dependency hooks (shared across all app suites) ---
# NOTE: We import specific names instead of wildcard to avoid shadowing
# pytest_runtest_makereport (the local definition below needs to call both
# the dependency-tracking logic AND the screenshot logic).
from sphere_e2e_test_framework.testing.conftest_hooks import (  # noqa: F401
    pytest_collection_modifyitems,
    pytest_runtest_setup,
    track_passed_case,
)


# ===========================================================================
# UIDriver Failure Screenshot Hook + Dependency Tracking
# ===========================================================================


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Track TCMS dependencies and capture UIDriver screenshot on failure.

    Merges two responsibilities:
    1. Record passed TCMS case IDs (from conftest_hooks.track_passed_case)
    2. Capture window-specific screenshot on test failure (UI tests only)
    """
    outcome = yield
    report = outcome.get_result()

    # --- Dependency tracking (always runs) ---
    track_passed_case(item, report)

    # --- Screenshot on failure ---
    if report.when != "call" or not report.failed:
        return

    # Try to get UIDriver from the test instance or fixtures
    driver = None
    if hasattr(item, "instance") and item.instance is not None:
        driver = getattr(item.instance, "driver", None)
    if driver is None and hasattr(item, "funcargs"):
        # Search for any *_driver fixture (e_admin_driver, cps_driver, etc.)
        for key, val in item.funcargs.items():
            if key.endswith("_driver") or key == "ui_app":
                driver = val
                break

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
