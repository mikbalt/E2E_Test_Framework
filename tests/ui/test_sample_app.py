"""
Sample UI Test - Windows Calculator

Demonstrates how to use the HSM Test Framework for Windows UI automation.
This test opens Calculator, clicks some buttons, and verifies results.

Replace this with your actual HSM application tests.

Run:
    pytest tests/ui/test_sample_app.py -v --alluredir=evidence/allure-results
"""

import logging

import allure
import pytest

from hsm_test_framework import Evidence, StepTracker, UIDriver

logger = logging.getLogger(__name__)


@allure.suite("UI Tests")
@allure.feature("Calculator Demo")
@pytest.mark.ui
@pytest.mark.smoke
class TestCalculatorDemo:
    """
    Demo test using Windows Calculator.
    Shows the pattern for testing any Windows desktop app.
    """

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: Launch Calculator."""
        self.driver = UIDriver(
            app_path="calc.exe",
            title="Calculator",
            backend="uia",
            startup_wait=2,
        )
        self.driver.start()
        self.evidence = Evidence("test_calculator")

        yield

        self.evidence.finalize()
        self.driver.close()

    @allure.title("Calculator - Basic Addition")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_basic_addition(self):
        """Test: Open calculator, perform 7 + 3, verify result = 10."""
        driver = self.driver
        evidence = self.evidence

        # Step 1: Verify app opened
        with StepTracker(evidence, driver, "Verify Calculator opened"):
            assert driver.main_window is not None
            logger.info("Calculator opened successfully")

        # Step 2: Click "7"
        with StepTracker(evidence, driver, "Click button '7'"):
            driver.click_button(name="Seven")

        # Step 3: Click "+"
        with StepTracker(evidence, driver, "Click button '+'"):
            driver.click_button(name="Plus")

        # Step 4: Click "3"
        with StepTracker(evidence, driver, "Click button '3'"):
            driver.click_button(name="Three")

        # Step 5: Click "="
        with StepTracker(evidence, driver, "Click button '='"):
            driver.click_button(name="Equals")

        # Step 6: Verify result
        with StepTracker(evidence, driver, "Verify result is 10"):
            # The result display automation ID varies by Windows version
            # Try common approaches:
            result_text = driver.get_text(auto_id="CalculatorResults")
            logger.info(f"Calculator result: {result_text}")
            assert "10" in result_text, f"Expected '10' in result, got: {result_text}"

    @allure.title("Calculator - App Launch and Close")
    @allure.severity(allure.severity_level.NORMAL)
    def test_app_launch_and_close(self):
        """Test: Verify Calculator can launch and close properly."""
        driver = self.driver
        evidence = self.evidence

        with StepTracker(evidence, driver, "Verify Calculator is visible"):
            assert driver.main_window.is_visible()
            evidence.log("Calculator window is visible")

        with StepTracker(evidence, driver, "Capture window state"):
            # Print control tree for debugging (helpful for new apps)
            driver.print_control_tree(depth=2)
            evidence.desktop_screenshot("full_desktop_view")


# ==========================================================================
# Template for YOUR HSM Application Tests
# ==========================================================================

@allure.suite("UI Tests")
@allure.feature("HSM Admin Tool")
@pytest.mark.ui
@pytest.mark.skip(reason="Template - configure app path in config/settings.yaml first")
class TestHSMAdminApp:
    """
    Template for testing HSM Admin application.
    Modify this class for your actual HSM Windows app.
    """

    @pytest.fixture(autouse=True)
    def setup(self, config):
        """Setup: Launch HSM Admin."""
        app_config = config.get("apps", {}).get("hsm_admin", {})
        self.driver = UIDriver(
            app_path=app_config.get("path"),
            title=app_config.get("title"),
            backend=app_config.get("backend", "uia"),
            startup_wait=app_config.get("startup_wait", 5),
        )
        self.driver.start()
        self.evidence = Evidence("test_hsm_admin")

        yield

        self.evidence.finalize()
        self.driver.close()

    @allure.title("HSM Admin - Launch and Verify Main Window")
    def test_launch_main_window(self):
        """Test: Launch HSM Admin and verify main window is displayed."""
        with StepTracker(self.evidence, self.driver, "Verify main window"):
            assert self.driver.main_window.is_visible()
            self.driver.print_control_tree(depth=3)

    @allure.title("HSM Admin - Navigate to Settings")
    def test_navigate_settings(self):
        """Test: Click Settings button/menu."""
        with StepTracker(self.evidence, self.driver, "Open Settings"):
            # Adjust button name/auto_id based on your app
            self.driver.click_button(name="Settings")

        with StepTracker(self.evidence, self.driver, "Verify Settings panel"):
            assert self.driver.element_exists(title="Settings", control_type="Window")

    @allure.title("HSM Admin - Connect to HSM Device")
    def test_connect_hsm(self):
        """Test: Connect to HSM device via the admin tool."""
        with StepTracker(self.evidence, self.driver, "Click Connect"):
            self.driver.click_button(name="Connect")

        with StepTracker(self.evidence, self.driver, "Verify connection status"):
            status = self.driver.get_text(auto_id="StatusLabel")
            assert "Connected" in status
