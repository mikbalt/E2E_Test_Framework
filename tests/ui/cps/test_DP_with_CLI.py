"""
[E2E][CPS][DP Test] DP Test Coverage

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
    pytest tests/ui/cps/test_DP_with_CLI.py -v
    pytest tests/ui/cps/test_DP_with_CLI.py -v --run-id kiwi_run_35 --kiwi-run-id 35
    pytest tests/ui/cps/test_DP_with_CLI.py -v --run-id kiwi_run_35 --kiwi-run-id 35 --alluredir = "C:/Automation/e2e_test_framework/evidence/allure-results"
"""
import logging

import allure
import pytest
from pathlib import Path

from sphere_e2e_test_framework import tracked_step, LogCollector
from sphere_e2e_test_framework.driver import cli_driver
from sphere_e2e_test_framework.driver import config_validator
from tests.test_data import KeyCeremonyData
from tests.schema import TestHsmConfigSchemaDP

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
@allure.feature("DP Test")
@allure.suite("CPS-Tier1 Journeys")
@pytest.mark.cps
@pytest.mark.apps("e_admin")
class TestHLCoverage:

    @pytest.fixture(autouse=True)
    def setup(self, app_drivers, evidence, config):
        """
        Setup shared objects for test methods.
        """
        self.apps = app_drivers
        self.evidence = evidence
        self.config = config
        yield

    @allure.story("User performs DP Test Coverage")
    @allure.title("[E2E][CPS][DP Test] DP Test Coverage")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.description(
        """
        Scenario: DP HSM Test Coverage
        Given eAdmin application is launched and visible.
        And eAdmin is connected to HSM successfully.

        When Test User log in with credentials
        And TestHSM application is launched
        And User verify Test Path is Test_Path
        And User verify Mode is Test_Mode
        And User verify DLLs is Test_DLLs
        And User verify Test IP is Test_DLL_IP
        And User verify Test Port is Test_DLL_Port
        And User verify HSM Type is Test_HSM_Type
        And User verify HSM Supplier is Test_HSM_Supplier
        And User filter the test file into Test_Filter
        And User check all available tests
        And User execute selected tests
        Then test execution is done.
        And log result is pop out with result OK.
        """
    )
    @allure.tag("cps", "windows", "ui", "DP")
    @allure.testcase("https://10.88.1.13/case/37513/")
    @pytest.mark.critical
    @pytest.mark.tcms(case_id=37513)
    def test_DP_with_CLI(self):
        """Test DP"""
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
        # Phase 2: Login as Test User
        # ==================================================================
        with tracked_step(self.evidence, e_admin, "When: Test User log in with credentials"):
            e_admin.click_element(auto_id="lbl_clickLogin", control_type="Text")
            e_admin.select_combobox(auto_id="cbSession", value="Secure_User_Session")
            e_admin.click_element(auto_id="rbPassword")
            e_admin.type_text("usercps", auto_id="1001")
            e_admin.type_text("1122334455667788", auto_id="txtPassword")
            e_admin.click_button(auto_id="btnLogin")
            logger.info("Test User login successfully")
        
        e_admin.click_button(auto_id="btnMinimize")

        # ==================================================================
        # Phase 3: TestHSM CLI Configuration for DP Test
        # ==================================================================
        
        # Check DP HSM Service already start or not
        logger.info("Check DP HSM Service already start or not")
        
        validator = config_validator.ConfigValidator(
            schema_class=TestHsmConfigSchemaDP,
            evidence=self.evidence
        )
        
        # Load paths from settings.yaml
        cli_cfg = self.config.get("console_tools", {}).get("testhsm_cli", {})
        executable = cli_cfg.get("executable_windows")
        config_file = cli_cfg.get("config_DP_windows")
        logger.info("TestHSM configuration loaded")
        
        if not executable or not config_file:
            raise RuntimeError("CLI path or config not found in settings.yaml (console_tools.testhsm_cli)")
        
        validator.validate(config_file)
        logger.info("TestHSM configuration is validated")

        report_dir = Path("./results/").resolve()
        report_dir.mkdir(parents=True, exist_ok=True)
        
        collector = LogCollector(self.evidence)
        cli = cli_driver.CLIDriver(
            executable=executable,
            evidence=self.evidence
        )

        # ==================================================================
        # Phase 4: CLI Execution and Log Collection
        # ==================================================================
        try:
            cli.run(
                config_file,
                args=["-v"]
            )
        finally:
            # Ensure logs are collected even if CLI fails
            # 1. Collect from results directory (generated report)
            collector.collect_latest(str(report_dir), name="TestHSM CLI DP Test Report")
            
            # 2. Collect from evidence/cli_logs (CLI execution log)
            collector.collect_latest("evidence/cli_logs", pattern="cli_*.log", name="CLI Execution Log")
            logger.info("Test done, all log already produced")
