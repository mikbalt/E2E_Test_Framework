"""
E-Admin UI Test - Connection and Dashboard Verification

Run:
    pytest tests/ui/e-admin.py -v --alluredir=evidence/allure-results

Filter by markers:
    pytest -m "smoke and ui" -v
    pytest -m "e_admin" -v
"""

import logging

import allure
import pytest

from hsm_test_framework import tracked_step

logger = logging.getLogger(__name__)

# NOTE: When multiple HSM targets are available, parametrize like this:
#
# @pytest.mark.parametrize("hsm_target", ["simulator", "production"], indirect=True)
# class TestEAdminConnection:
#     ...
#
# And add an `hsm_target` fixture in tests/ui/conftest.py that loads
# per-target config from settings.yaml.


@allure.suite("UI Tests")
@allure.feature("E-Admin - Connection")
@allure.story("HSM Connection Workflow")
@allure.tag("e-admin", "windows", "ui")
@pytest.mark.ui
@pytest.mark.e_admin
class TestEAdminConnection:

    @pytest.fixture(autouse=True)
    def setup(self, e_admin_driver, evidence):
        """Wire shared fixtures into test instance attributes."""
        self.driver = e_admin_driver
        self.evidence = evidence
        yield

    @allure.title("E-Admin - Verify Connection and Dashboard Load")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.description(
        "Verifies that E-Admin application can:\n"
        "1. Launch and become visible\n"
        "2. Connect to HSM via Connect button\n"
        "3. Dismiss popups and confirm with OK\n"
        "4. Load dashboard successfully"
    )
    @pytest.mark.smoke
    @pytest.mark.critical
    def test_connect_and_load_dashboard(self):
        """Open E-Admin, connect, click OK, verify dashboard loads."""
        driver = self.driver
        evidence = self.evidence

        # Step 1: Verify app launched
        with tracked_step(evidence, driver, "Verify app is visible"):
            assert driver.main_window.is_visible(), (
                "E-Admin main window is not visible after launch"
            )
            logger.info("E-Admin launched successfully")

        # Step 2: Click Connect
        with tracked_step(evidence, driver, "Click Connect button"):
            driver.click_button(auto_id="btnUpdate")
            logger.info("Connect button clicked")

        # Wait for connection response (replaces time.sleep)
        driver.wait_for_element(timeout=10, auto_id="btnOKE", control_type="Button")

        # Step 3: Dismiss popup and click OK
        with tracked_step(evidence, driver, "Dismiss popup and click OK"):
            popup = driver.check_popup()
            if popup:
                logger.info(f"Popup detected: '{popup.window_text()}'")
                allure.attach(
                    popup.window_text(),
                    name="popup_text",
                    attachment_type=allure.attachment_type.TEXT,
                )
            driver.click_button(auto_id="btnOKE")
            logger.info("OK button clicked")

        # Refresh window reference after OK (window may change)
        driver.refresh_window()

        # Step 4: Verify dashboard loaded
        with tracked_step(evidence, driver, "Verify dashboard loaded"):
            assert driver.main_window.is_visible(), (
                "E-Admin window not visible after connection"
            )
            logger.info("Dashboard loaded - printing control tree for verification")
            driver.print_control_tree(depth=5)
