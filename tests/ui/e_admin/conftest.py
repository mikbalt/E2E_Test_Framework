"""
tests/ui/e_admin/conftest.py -- E-Admin specific fixtures.

Provides:
- e_admin_config: session-scoped config extracted from settings.yaml
- e_admin_driver: function-scoped UIDriver that does NOT auto-close
"""

import logging

import pytest

logger = logging.getLogger(__name__)


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
