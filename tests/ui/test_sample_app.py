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

from sphere_e2e_test_framework import tracked_step

logger = logging.getLogger(__name__)


@allure.suite("UI Tests")
@allure.feature("Calculator Demo")
@pytest.mark.ui
@pytest.mark.smoke
@pytest.mark.skip(reason="Demo only — runs against Calculator, not an HSM test")
class TestCalculatorDemo:
    """
    Demo test using Windows Calculator.
    Shows the pattern for testing any Windows desktop app.
    """

    @pytest.fixture(autouse=True)
    def setup(self, ui_app, evidence):
        """Wire shared fixtures into test instance."""
        self.driver = ui_app
        self.evidence = evidence
        yield

    @allure.title("Calculator - Basic Addition")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_basic_addition(self):
        """Test: Open calculator, perform 7 + 3, verify result = 10."""
        driver = self.driver
        evidence = self.evidence

        with tracked_step(evidence, driver, "Given: Calculator is open"):
            assert driver.main_window is not None, (
                "Calculator main window was not found"
            )
            logger.info("Calculator opened successfully")

        with tracked_step(evidence, driver, "When: Perform 7 + 3"):
            driver.click_button(name="Seven")
            driver.click_button(name="Plus")
            driver.click_button(name="Three")
            driver.click_button(name="Equals")

        with tracked_step(evidence, driver, "Then: Result is 10"):
            result_text = driver.get_text(auto_id="CalculatorResults")
            logger.info(f"Calculator result: {result_text}")
            assert "10" in result_text, (
                f"Expected '10' in result, got: {result_text}"
            )

    @allure.title("Calculator - App Launch and Close")
    @allure.severity(allure.severity_level.NORMAL)
    def test_app_launch_and_close(self):
        """Test: Verify Calculator can launch and close properly."""
        driver = self.driver
        evidence = self.evidence

        with tracked_step(evidence, driver, "Given: Calculator launched"):
            assert driver.main_window.is_visible(), (
                "Calculator window is not visible after launch"
            )
            evidence.log("Calculator window is visible")

        with tracked_step(evidence, driver, "Then: Window state captured"):
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
    def setup(self, ui_app, evidence):
        """Wire shared fixtures into test instance."""
        self.driver = ui_app
        self.evidence = evidence
        yield

    @allure.title("HSM Admin - Launch and Verify Main Window")
    def test_launch_main_window(self):
        """Test: Launch HSM Admin and verify main window is displayed."""
        with tracked_step(self.evidence, self.driver, "Given: App launched"):
            assert self.driver.main_window.is_visible(), (
                "HSM Admin main window is not visible"
            )
            self.driver.print_control_tree(depth=3)

    @allure.title("HSM Admin - Navigate to Settings")
    def test_navigate_settings(self):
        """Test: Click Settings button/menu."""
        with tracked_step(self.evidence, self.driver, "When: Open Settings"):
            self.driver.click_button(name="Settings")

        with tracked_step(self.evidence, self.driver, "Then: Settings panel visible"):
            assert self.driver.element_exists(title="Settings", control_type="Window"), (
                "Settings panel did not appear"
            )

    @allure.title("HSM Admin - Connect to HSM Device")
    def test_connect_hsm(self):
        """Test: Connect to HSM device via the admin tool."""
        with tracked_step(self.evidence, self.driver, "When: Click Connect"):
            self.driver.click_button(name="Connect")

        with tracked_step(self.evidence, self.driver, "Then: Status shows Connected"):
            status = self.driver.get_text(auto_id="StatusLabel")
            assert "Connected" in status, (
                f"Expected 'Connected' in status, got: '{status}'"
            )
