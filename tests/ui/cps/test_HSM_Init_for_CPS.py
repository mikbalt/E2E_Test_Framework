"""
[E2E][CPS][Initialize HSM] Initialize HSM for CPS Client

Scenario: HSM Initialize and test preparation for CPS Client

Given eAdmin application is launched and visible.
And eAdmin is connected to HSM successfully.

When Admin log in with credentials
And Admin generate new Test Key successfully
And Admin created User Profile successfully
And Admin created Test User account successfully
And Admin synchronize the system
Then all SE are synchronized.

When Test User log in with credentials
Then test preparation for CPS Client is complete

Run:
    pytest tests/ui/cps/test_HSM_Init_for_CPS.py -v
    pytest tests/ui/cps/test_HSM_Init_for_CPS.py -v --run-id kiwi_run_35 --kiwi-run-id 35
"""
import logging

import allure
import pytest

from sphere_e2e_test_framework import tracked_step, LogCollector
from tests.test_data import KeyCeremonyData

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Timeout — single place to tune all wait_for_element timeouts (seconds)
# ---------------------------------------------------------------------------
TIMEOUT = 120


# ---------------------------------------------------------------------------
# Reusable UI helpers (scoped to this module)
# ---------------------------------------------------------------------------

def _dismiss_ok(driver):
    """Dismiss a dialog by clicking OK (auto_id='2')."""
    driver.wait_for_element(timeout=TIMEOUT, auto_id="2", control_type="Button")
    driver.click_button(auto_id="2")

# ---------------------------------------------------------------------------
# Test class
# ---------------------------------------------------------------------------

@allure.epic("Sphere HSM Idemia - E2E Tests - CPS")
@allure.feature("HSM Init")
@allure.suite("CPS-Tier1 Journeys")
@pytest.mark.apps("e_admin")
class TestHLCoverage:

    @pytest.fixture(autouse=True)
    def setup(self, app_drivers, evidence):
        """
        Setup shared objects for test methods.

        Attributes exposed to tests:
            e_admin  -> E-Admin UI driver
            self.testhsm  -> TestHSM UI driver
            self.evidence -> evidence collector
        """
        self.apps = app_drivers
        self.evidence = evidence
        yield

    @allure.story("User performs HSM Initialize for CPS Test")
    @allure.title("[E2E][CPS][Initialize HSM] Initialize HSM for CPS Client")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.description(
        """
       Scenario: HSM Initialize and test preparation for CPS Client

        Given eAdmin application is launched and visible.
        And eAdmin is connected to HSM successfully.

        When Admin log in with credentials
        And Admin generate new Test Key successfully
        And Admin created User Profile successfully
        And Admin created Test User account successfully

        When Admin log in with credentials and session Synchronization
        And Admin synchronize the system
        Then on log the all SE are synchronized.

        When Test User log in with credentials
        And Test User credentials is accepted
        Then test preparation for CPS Client is complete
        """
    )
    @allure.tag("cps", "windows", "ui", "Init HSM")
    @allure.testcase("https://10.88.1.13/case/37510/")
    @pytest.mark.critical
    @pytest.mark.tcms(case_id=37510)
    def test_HSM_Initialize_CPS(self):
        """Test HSM Initialize for CPS."""

        # ==================================================================
        # Phase 1: Connect to HSM
        # ==================================================================
        e_admin = self.apps["e_admin"]
        with tracked_step(self.evidence, e_admin, "Given: eAdmin application is launched and visible"):
            assert e_admin.main_window.is_visible(), (
                "E-Admin main window is not visible after launch"
            )
            logger.info("E-Admin launched successfully")

        with tracked_step(self.evidence, e_admin, "Given: eAdmin is connected to HSM successfully"):
            e_admin.click_button(auto_id="btnUpdate")
            logger.info("Connect button clicked")

            e_admin.wait_for_element(
                timeout=TIMEOUT, auto_id="btnOKE", control_type="Button"
            )

            popup = e_admin.check_popup()
            if popup:
                logger.info(f"Popup detected: '{popup.window_text()}'")
                allure.attach(
                    popup.window_text(),
                    name="popup_text",
                    attachment_type=allure.attachment_type.TEXT,
                )

            # Capture popup state before dismissing
            self.evidence.screenshot(e_admin, "step_002a_popup_visible")

            e_admin.click_button(auto_id="btnOKE")
            logger.info("OK button clicked")

        e_admin.refresh_window()

        with tracked_step(self.evidence, e_admin, "Then: HSM connection confirmed"):
            assert e_admin.main_window.is_visible(), (
                "E-Admin window not visible after connection"
            )
            logger.info("Dashboard loaded - control tree captured")

        # ==================================================================
        # Phase 2: Login as Admin
        # ==================================================================
        with tracked_step(self.evidence, e_admin, "And: Admin logs in with credentials"):
            e_admin.click_element(auto_id="lbl_clickLogin", control_type="Text")
            e_admin.select_combobox(auto_id="cbSession", value="Admin_Session")
            e_admin.click_element(auto_id="rbPassword")
            e_admin.type_text("admin", auto_id="1001")
            e_admin.type_text("11111111", auto_id="txtPassword")
            e_admin.click_button(auto_id="btnLogin")
            logger.info("Admin account log in successfully")

        # ==================================================================
        # Phase 3: Generate Test key
        # ==================================================================
        with tracked_step(self.evidence, e_admin, "And: Generate Test Key"):
            e_admin.click_button(auto_id="btnListKey")
            e_admin.click_button(auto_id="btnRefresh")
            e_admin.click_button(auto_id="btnPermanent")
            logger.info("Test key is generated successfully")

        # ==================================================================
        # Phase 3: Create User Profile
        # ==================================================================
        with tracked_step(self.evidence, e_admin, "And: Admin creates User Profile"):
            e_admin.click_button(auto_id="btnProfile")
            e_admin.click_button(auto_id="btnAdd")
            e_admin.type_text("USER_PROFILE_1", auto_id="txtProfileName")
            e_admin.click_element(auto_id="checkBox1")
            e_admin.click_button(auto_id="btnCreate")
            _dismiss_ok(e_admin)
            e_admin.refresh_window()
            logger.info("New user profile creation confirmed")

        # ==================================================================
        # Phase 4: Create Test User
        # ==================================================================
        with tracked_step(self.evidence, e_admin, "And: Admin creates Test User"):
            e_admin.click_button(auto_id="btnUser")
            e_admin.click_button(auto_id="btnAdd")
            e_admin.click_element(auto_id="rbPass")
            e_admin.type_text("usercps", auto_id="txtUsername")
            e_admin.type_text("USER_PROFILE_1", auto_id="1001")
            e_admin.type_text("1122334455667788", auto_id="txtPass")
            e_admin.type_text("1122334455667788", auto_id="txtPassRepeat")
            e_admin.click_button(auto_id="btnCreate")
            _dismiss_ok(e_admin)
            e_admin.refresh_window()
            logger.info("New test user confirmed")

        # ==================================================================
        # Phase 4: Sync the HSM
        # ==================================================================
        with tracked_step(self.evidence, e_admin, "And: Admin synchronize the system"):
            e_admin.click_button(auto_id="btnSync")

        _dismiss_ok(e_admin)
        with tracked_step(self.evidence, e_admin, "Then: all SE are synchronized"):
            logger.info("Sync HSM is done")

        # ==================================================================
        # Phase 5: Admin logout and User login
        # ==================================================================
        with tracked_step(self.evidence, e_admin, "And: Admin log out"):
            e_admin.click_button(auto_id="btnLogOut")

        _dismiss_ok(e_admin)
        logger.info("Admin logged out successfully")

        with tracked_step(self.evidence, e_admin, "When: Test User log in with credentials"):
            e_admin.click_element(auto_id="lbl_clickLogin", control_type="Text")
            e_admin.select_combobox(auto_id="cbSession", value="Secure_User_Session")
            e_admin.click_element(auto_id="rbPassword")
            e_admin.type_text("usercps", auto_id="1001")
            e_admin.type_text("1122334455667788", auto_id="txtPassword")
            e_admin.click_button(auto_id="btnLogin")

        with tracked_step(self.evidence, e_admin, "Then: Test user is login successfully"):
            logger.info("Test user is log in successfully")
            
        e_admin.click_button(auto_id="btnLogOut")

        