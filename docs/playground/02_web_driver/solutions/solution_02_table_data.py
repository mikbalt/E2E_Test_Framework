"""Solution: Table Data Extraction."""

import pytest


@pytest.mark.web
class TestTableDataSolution:
    def test_members_table_has_data(self, web_driver, base_url):
        web_driver.goto(f"{base_url}/login")
        web_driver.fill("#username", "admin")
        web_driver.fill("#password", "admin123")
        web_driver.click("button[type=submit]")
        web_driver.wait_for_url("**/dashboard**")

        web_driver.goto(f"{base_url}/members")
        web_driver.wait_for_selector("table")
        data = web_driver.get_table_data("table")
        assert len(data) > 0
