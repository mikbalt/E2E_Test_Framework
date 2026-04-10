"""Exercise: Accessibility Scanning.

TODO: Scan the login page for accessibility violations.
"""

import pytest

from ankole.driver.a11y import A11yScanner


@pytest.fixture
def scanner():
    return A11yScanner(default_tags=["wcag2a", "wcag2aa"])


@pytest.mark.web
@pytest.mark.a11y
class TestAccessibility:
    """Accessibility scanning exercises."""

    def test_login_page_a11y(self, web_driver, scanner, base_url):
        """TODO: Scan the login page and assert no critical violations."""
        web_driver.goto(f"{base_url}/login")
        web_driver.wait_for_selector("form")

        report = scanner.scan(web_driver)
        print(report.summary())

        # Assert no critical or serious violations
        report.assert_no_violations(impact=["critical", "serious"])

    def test_login_form_scoped_scan(self, web_driver, scanner, base_url):
        """TODO: Scan only the login form element."""
        web_driver.goto(f"{base_url}/login")
        web_driver.wait_for_selector("form")

        report = scanner.scan(web_driver, selector="form")
        report.assert_no_violations(impact=["critical"])
