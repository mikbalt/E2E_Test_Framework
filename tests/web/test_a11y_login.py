"""Accessibility test for the login page."""

import pytest


@pytest.mark.web
@pytest.mark.a11y
class TestA11yLogin:
    """Accessibility tests for the login page."""

    def test_login_page_no_critical_violations(self, web_driver, a11y_scanner, base_url):
        """Login page should have no critical or serious a11y violations."""
        web_driver.goto(f"{base_url}/login")
        web_driver.wait_for_selector("form")

        report = a11y_scanner.scan(web_driver)
        report.attach_to_allure()
        report.assert_no_violations(impact=["critical", "serious"])

    def test_login_form_accessible(self, web_driver, a11y_scanner, base_url):
        """Login form should have no violations scoped to the form element."""
        web_driver.goto(f"{base_url}/login")
        web_driver.wait_for_selector("form")

        report = a11y_scanner.scan(web_driver, selector="form")
        report.assert_no_violations(impact=["critical"])
