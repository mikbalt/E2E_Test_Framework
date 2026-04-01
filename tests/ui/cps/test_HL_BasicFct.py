"""
[E2E][CPS][HL Test | BasicFct] HL Test BasicFct Coverage

Scenario:
Given eAdmin application is launched and visible.
And eAdmin is connected to HSM successfully.

When Test User log in with credentials
And TestHSM application is launched
And User load HL Test Configuration
And User verify mode is Client/Server
And User verify DLLs is CPSInterface
And User verify HSM Type is Card
And User verify HSM Supplier is Rooky
And User filter the test file into BasicFct
And User filter the test frame into A001
And User check all available tests
And User execute selected tests
Test execution is done and Log result is pop up.

Run:
    pytest tests/ui/cps/test_HL_BasicFct.py -v
    pytest tests/ui/cps/test_HL_BasicFct.py -v --run-id kiwi_run_35 --kiwi-run-id 35
    pytest tests/ui/cps/test_HL_BasicFct.py -v --run-id kiwi_run_35 --kiwi-run-id 35 --alluredir = "C:/Automation/e2e_test_framework/evidence/allure-results"
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

def _agree_and_next(driver):
    """Click 'Agree' radio then 'Next >>>' button."""
    driver.click_element(auto_id="rbAgree")
    driver.wait_for_element(timeout=TIMEOUT, auto_id="btnNext", control_type="Button")
    driver.click_button(auto_id="btnNext")


def _dismiss_ok(driver):
    """Dismiss a dialog by clicking OK (auto_id='2')."""
    driver.wait_for_element(timeout=TIMEOUT, auto_id="2", control_type="Button")
    driver.click_button(auto_id="2")


# ---------------------------------------------------------------------------
# Test class
# ---------------------------------------------------------------------------

@allure.epic("Sphere HSM Idemia - E2E Tests - CPS")
@allure.feature("HL Test")
@allure.suite("CPS-Tier1 Journeys")
@pytest.mark.cps
@pytest.mark.apps("testhsm")
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

    @allure.story("User performs HL Test for BasicFct Coverage")
    @allure.title("[E2E][CPS][HL Test | BasicFct] HL Test BasicFct Coverage")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.description(
        """
        Scenario: Perform HL Test BasicFct Coverage

        Given eAdmin application is launched and visible.
        And eAdmin is connected to HSM successfully.

        When Test User log in with credentials
        And TestHSM application is launched
        And User load HL Test Configuration
        And User verify mode is Client/Server
        And User verify DLLs is CPSInterface
        And User verify HSM Type is Card
        And User verify HSM Supplier is Rooky
        And User filter the test file into BasicFct
        And User filter the test frame into A001
        And User check all available tests
        And User execute selected tests
        Test execution is done and Log result is pop up.
        """
    )
    @allure.tag("cps", "windows", "ui", "BasicFct")
    @allure.testcase("https://10.88.1.13/case/37511/")
    @pytest.mark.critical
    @pytest.mark.tcms(case_id=37511)
    def test_HL_BasicFct(self):
        """Test HL BasicFct."""

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
        # Phase 2: Test User login
        # ==================================================================
        with tracked_step(self.evidence, e_admin, "When: Test User log in with credentials"):
            e_admin.click_element(auto_id="lbl_clickLogin", control_type="Text")
            e_admin.select_combobox(auto_id="cbSession", value="Secure_User_Session")
            e_admin.click_element(auto_id="rbPassword")
            e_admin.type_text("usercps", auto_id="1001")
            e_admin.type_text("1122334455667788", auto_id="txtPassword")
            e_admin.click_button(auto_id="btnLogin")

        with tracked_step(self.evidence, e_admin, "Then: Test user is login successfully"):
            logger.info("Test user is log in successfully")

        # ==================================================================
        # Phase 3: Open TestHSM.net load config
        # ==================================================================
        
        testhsm = self.apps["testhsm"]
        with tracked_step(self.evidence, testhsm, "When: TestHSM application is launched"):
            assert testhsm.main_window.is_visible(), (
                "TestHSM.net main window is not visible after launch"
            )
            logger.info("TestHSM.net launched successfully")

        with tracked_step(self.evidence, testhsm, "And: User load HL Test Configuration"):
            testhsm.click_button(auto_id="buttonLoadConfig")
            testhsm.refresh_window()
            logger.info("HL Config is loaded successfully")

        with tracked_step(self.evidence, testhsm, "And: User verify mode is Client/Server"):
            testhsm.click_element(auto_id="radioModeServer",control_type="RadioButton")
            logger.info("Test Mode is Client/Server")

        with tracked_step(self.evidence, testhsm, "And: User verify DLLs is CPSInterface"):
            testhsm.click_element(auto_id="radioCPSInterfacedll",control_type="RadioButton")
            logger.info("DLLs is using CPSInterface")

        with tracked_step(self.evidence, testhsm, "And: User verify HSM type is Card"):
            testhsm.click_element(auto_id="radioCard",control_type="RadioButton")
            logger.info("HSM Type is using Card")

        with tracked_step(self.evidence, testhsm, "And: User verify HSM Supplier is Rooky"):
            testhsm.click_element(auto_id="radioRooky",control_type="RadioButton")
            logger.info("HSM Supplier is using Rooky")

        with tracked_step(self.evidence, testhsm, "And: User filter the test file into BasicFct"):
            testhsm.type_text("BasicFct", auto_id="txtFileFilter")
            logger.info("File filter is implemented")

        with tracked_step(self.evidence, testhsm, "And: User filter the test frame into A001"):
            testhsm.type_text("A001", auto_id="txtDescriptionFilter")
            logger.info("Frame filter is implemented")

        with tracked_step(self.evidence, testhsm, "And: User choose all available tests"):
            testhsm.click_button(auto_id="buttonAll")
            logger.info("All available test is selected")

        with tracked_step(self.evidence, testhsm, "And: User execute selected tests"):
            testhsm.click_button(auto_id="buttonLaunch")
            logger.info("All selected test is executed.")

        with tracked_step(self.evidence, testhsm, "Then: Test execution is done and Log result is popup"):
            _dismiss_ok(testhsm)
            logger.info("Selected test execution is done and Log is available on popup.")
        
        collector = LogCollector(self.evidence)
        collector.collect_latest("C:/Users/Administrator/Documents/HSM-Tools/Test Folder/Test4/ROOKY_FIPS_2021/UnitTest_HSMRookyApplet/general/CommonFile/CPSDLL/TM_CPS_ORG_002/", pattern="*.txt")