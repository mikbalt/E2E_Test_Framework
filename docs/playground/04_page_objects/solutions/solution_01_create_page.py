"""Solution: Page Object for Login."""

import pytest


class LoginPage:
    URL_PATH = "/login"

    def __init__(self, driver):
        self.driver = driver

    def navigate(self, base_url):
        self.driver.goto(f"{base_url}{self.URL_PATH}")
        return self

    def login(self, username, password):
        self.driver.fill("#username", username)
        self.driver.fill("#password", password)
        self.driver.click("button[type=submit]")
        return self

    def wait_for_dashboard(self):
        self.driver.wait_for_url("**/dashboard**")
        return self


@pytest.mark.web
class TestPageObjectSolution:
    def test_login_via_page_object(self, web_driver, base_url):
        page = LoginPage(web_driver)
        page.navigate(base_url).login("admin", "admin123").wait_for_dashboard()
        assert "dashboard" in web_driver.url
