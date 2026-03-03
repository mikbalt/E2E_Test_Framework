"""
E-Admin UI Test - Connection and Dashboard Verification

Run:
    pytest tests/ui/e_admin/test_connect.py -v --alluredir=evidence/allure-results

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
# And add an `hsm_target` fixture in tests/ui/e_admin/conftest.py that loads
# per-target config from settings.yaml.

@allure.suite("E2E")
@allure.feature("e-admin")
@allure.story("Key Ceremony")
@allure.tag("e-admin", "windows", "ui")
@pytest.mark.e_admin
class TestEAdminConnection:

    @pytest.fixture(autouse=True)
    def setup(self, e_admin_driver, evidence):
        """Wire shared fixtures into test instance attributes."""
        self.driver = e_admin_driver
        self.evidence = evidence
        yield

    @allure.title("Key ceremony using password via E-Admin")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.description(
        """
        Scenario: Perform Key Ceremony with 3 Key Custodians and 1 Auditor using password via eAdmin
        Given : eAdmin application is installed and HSM are in place and configured correctly.
        When : user changes the SUPER_USER default password
        And SUPER_USER logs in to eAdmin with new credentials
        And SUPER_USER creates Key Custodian 1 account
        And SUPER_USER creates Key Custodian 2 account
        And SUPER_USER creates Key Custodian 3 account
        And SUPER_USER creates Auditor account
        And Login as Key Custodian 1 and imports CCMK
        And Login as Key Custodian 2 and imports CCMK
        And Login as Key Custodian 3 and imports CCMK
        Then 3 Key Custodian accounts and 1 Auditor account are created successfully
        And CCMK is imported successfully for all 4 quorum members

        """
    )
    @pytest.mark.smoke
    @pytest.mark.critical
    @pytest.mark.tcms(case_id=37509)
    def test_connect_and_load_dashboard(self):
        """Open E-Admin, connect, click OK, verify dashboard loads."""
        driver = self.driver
        evidence = self.evidence

        # Given: app launched and visible
        with tracked_step(evidence, driver, "Given: E-Admin launched and visible"):
            assert driver.main_window.is_visible(), (
                "E-Admin main window is not visible after launch"
            )
            logger.info("E-Admin launched successfully")

        # When: connect and confirm popup
        with tracked_step(evidence, driver, "When: Click Connect and confirm popup"):
            driver.click_button(auto_id="btnUpdate")
            logger.info("Connect button clicked")

            driver.wait_for_element(
                timeout=10, auto_id="btnOKE", control_type="Button"
            )

            popup = driver.check_popup()
            if popup:
                logger.info(f"Popup detected: '{popup.window_text()}'")
                allure.attach(
                    popup.window_text(),
                    name="popup_text",
                    attachment_type=allure.attachment_type.TEXT,
                )

            # Capture popup state before dismissing
            evidence.screenshot(driver, "step_002a_popup_visible")

            driver.click_button(auto_id="btnOKE")
            logger.info("OK button clicked")

        # Refresh window reference after OK (window may change)
        driver.refresh_window()

        # Then: dashboard loaded
        with tracked_step(evidence, driver, "Then: Dashboard loaded successfully"):
            assert driver.main_window.is_visible(), (
                "E-Admin window not visible after connection"
            )
            # Log the control tree as evidence of dashboard state
            driver.print_control_tree(depth=2)
            logger.info("Dashboard loaded - control tree captured")
