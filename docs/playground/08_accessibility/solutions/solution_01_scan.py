"""Solution: Accessibility Scanning."""

import pytest
from ankole.driver.a11y import A11yScanner


@pytest.fixture
def scanner():
    return A11yScanner(default_tags=["wcag2a", "wcag2aa"])


@pytest.mark.web
@pytest.mark.a11y
class TestAccessibilitySolution:
    def test_login_page(self, web_driver, scanner, base_url):
        web_driver.goto(f"{base_url}/login")
        web_driver.wait_for_selector("form")
        report = scanner.scan(web_driver)
        report.assert_no_violations(impact=["critical", "serious"])

    def test_form_scoped(self, web_driver, scanner, base_url):
        web_driver.goto(f"{base_url}/login")
        web_driver.wait_for_selector("form")
        report = scanner.scan(web_driver, selector="form")
        report.assert_no_violations(impact=["critical"])
