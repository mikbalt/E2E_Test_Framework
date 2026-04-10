"""Visual regression test for the login page."""

import pytest


@pytest.mark.web
@pytest.mark.visual
class TestVisualLogin:
    """Visual regression tests for login page."""

    def test_login_page_visual(self, web_driver, visual_comparator, base_url):
        """Compare login page screenshot against baseline."""
        web_driver.goto(f"{base_url}/login")
        web_driver.wait_for_selector("form")

        result = visual_comparator.compare(web_driver, "login_page")
        result.attach_to_allure()
        result.assert_match(threshold=0.02)

    def test_login_form_element_visual(self, web_driver, visual_comparator, base_url):
        """Compare just the login form element."""
        web_driver.goto(f"{base_url}/login")
        web_driver.wait_for_selector("form")

        result = visual_comparator.compare(
            web_driver, "login_form",
            selector="form",
        )
        result.assert_match(threshold=0.02)
