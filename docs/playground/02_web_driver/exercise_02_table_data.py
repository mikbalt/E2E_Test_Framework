"""Exercise: Table Data Extraction.

TODO: Extract and verify table data from the members page.
"""

import pytest


@pytest.mark.web
class TestTableData:
    """Table data extraction exercises."""

    def test_members_table_has_data(self, web_driver, base_url):
        """TODO: Navigate to members page and verify table has rows."""
        # Step 1: Log in first
        web_driver.goto(f"{base_url}/login")
        web_driver.fill("#username", "admin")
        web_driver.fill("#password", "admin123")
        web_driver.click("button[type=submit]")
        web_driver.wait_for_url("**/dashboard**")

        # Step 2: Navigate to members page
        # TODO: Navigate to the members page
        web_driver.goto(f"{base_url}/members")

        # Step 3: Extract table data
        # TODO: Use web_driver.get_table_data() on the members table
        web_driver.wait_for_selector("table")
        data = web_driver.get_table_data("table")

        # Step 4: Assert the table has at least one row
        assert len(data) > 0
        # Step 5: Assert the first row has expected keys
        assert "username" in data[0] or len(data[0]) > 0
