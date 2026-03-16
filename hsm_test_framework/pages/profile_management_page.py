"""
Profile Management page object for E-Admin.

Handles viewing, creating, and verifying user profiles.
"""

import logging
import time

from hsm_test_framework.pages.base_page import BasePage, TIMEOUT

logger = logging.getLogger(__name__)


class ProfileManagementPage(BasePage):
    """Profile Management screen (post-login, sidebar → Profile)."""

    def refresh(self, step_name=None):
        """Click Refresh to reload the profile list."""
        with self._step(step_name):
            self.driver.click_button(auto_id="btnRefresh")
            time.sleep(2)
            logger.info("Profile list refreshed")
        return self

    def get_profile_table(self):
        """Read profile list table data.

        Returns:
            dict with 'headers' (list[str]) and 'rows' (list[list[str]]).
        """
        data = self.driver.get_table_data()
        logger.info(
            f"Profile table: {len(data['rows'])} rows, "
            f"headers={data['headers']}",
        )
        return data

    def get_profile_count(self):
        """Return number of rows in the profile table (lightweight)."""
        data = self.driver.get_table_data()
        return len(data["rows"])

    def create_profile(self, profile_name, select_all_acl=True,
                       step_name=None):
        """Create a new profile.

        Args:
            profile_name: Name for the new profile.
            select_all_acl: If True, click 'Select all' checkbox.
            step_name: Optional evidence step description.

        Returns:
            str: Confirmation message from the popup dialog.
        """
        with self._step(step_name):
            self.driver.click_button(auto_id="btnAdd")
            self.driver.wait_for_element(
                timeout=TIMEOUT, auto_id="txtProfileName",
            )
            self.driver.type_text(profile_name, auto_id="txtProfileName")
            if select_all_acl:
                self.driver.click_element(auto_id="checkBox1")
            self.driver.click_button(auto_id="btnCreate")
            message = self.dismiss_ok_with_message()
            logger.info(f"Profile '{profile_name}' created")
            return message

    def profile_exists_in_table(self, profile_name):
        """Check if a profile name exists in the table rows.

        Uses get_list_items() as a faster alternative to full table parse.
        Falls back to get_table_data() if list approach finds nothing.
        """
        # Fast: search list items text
        try:
            items = self.driver.get_list_items()
            for item_text in items:
                if profile_name in item_text:
                    logger.info(f"Profile '{profile_name}' found in list")
                    return True
        except Exception:
            pass

        # Fallback: full table parse
        data = self.driver.get_table_data()
        for row in data["rows"]:
            for cell in row:
                if profile_name in cell:
                    logger.info(f"Profile '{profile_name}' found in table")
                    return True

        logger.warning(f"Profile '{profile_name}' NOT found")
        return False
