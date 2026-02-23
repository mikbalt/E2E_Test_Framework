"""
Example: UI test for a consumer repo.
Shows how to use the shared framework in your own test repository.
"""

import allure
import pytest

from hsm_test_framework import UIDriver, Evidence, StepTracker


@allure.suite("My App - UI Tests")
@pytest.mark.ui
@pytest.mark.smoke
class TestMyApp:

    @pytest.fixture(autouse=True)
    def setup(self, config):
        app_config = config.get("apps", {}).get("my_app", {})
        self.driver = UIDriver(
            app_path=app_config.get("path"),
            title=app_config.get("title"),
            backend=app_config.get("backend", "uia"),
            startup_wait=app_config.get("startup_wait", 5),
        )
        self.driver.start()
        self.evidence = Evidence("test_my_app")

        yield

        self.evidence.finalize()
        self.driver.close()

    @allure.title("My App - Launch Successfully")
    def test_app_launches(self):
        with StepTracker(self.evidence, self.driver, "Verify app launched"):
            assert self.driver.main_window.is_visible()

    @allure.title("My App - Click Main Button")
    def test_click_main_button(self):
        with StepTracker(self.evidence, self.driver, "Click main action button"):
            self.driver.click_button(name="Start")  # Replace with your button

        with StepTracker(self.evidence, self.driver, "Verify result"):
            status = self.driver.get_text(auto_id="StatusLabel")
            assert "Ready" in status
