"""
tests/ui/e_admin/conftest.py -- E-Admin specific fixtures.

Provides:
- e_admin_config: session-scoped config extracted from settings.yaml
- e_admin_driver: function-scoped UIDriver that does NOT auto-close
- collect_app_logs: auto-collects E-Admin AppLogs into a zip after each test
"""

import datetime
import logging
import os
import zipfile

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


@pytest.fixture(autouse=True)
def collect_app_logs(request, e_admin_config, evidence):
    """Auto-collect E-Admin AppLogs into a zip after each test (pass or fail).

    The zip is saved in the test's evidence directory and attached to Allure.
    Configure the logs path via E_ADMIN_APP_LOGS env var or
    apps.e_admin.app_logs_dir in settings.yaml.
    """
    yield

    app_logs_dir = e_admin_config.get("app_logs_dir", "")
    if not app_logs_dir or not os.path.isdir(app_logs_dir):
        logger.debug(f"App logs dir not found or not configured: {app_logs_dir}")
        return

    try:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_name = f"AppLogs_{request.node.name}_{timestamp}.zip"
        zip_path = os.path.join(evidence.evidence_dir, zip_name)

        file_count = 0
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, _dirs, files in os.walk(app_logs_dir):
                for fname in files:
                    full_path = os.path.join(root, fname)
                    arcname = os.path.relpath(full_path, app_logs_dir)
                    zf.write(full_path, arcname)
                    file_count += 1

        if file_count == 0:
            os.remove(zip_path)
            logger.info("App logs dir is empty, skipped zip")
            return

        logger.info(f"Collected {file_count} app log files -> {zip_path}")

        # Attach to Allure
        try:
            import allure
            with open(zip_path, "rb") as f:
                allure.attach(
                    f.read(),
                    name=zip_name,
                    attachment_type=allure.attachment_type.TEXT,
                    extension="zip",
                )
        except ImportError:
            pass

    except Exception as e:
        logger.warning(f"Failed to collect app logs: {e}")
