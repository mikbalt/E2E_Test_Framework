"""
User Management page object for E-Admin.

Handles viewing, creating, syncing, and verifying user accounts
(post-key-ceremony, via sidebar → User).
"""

import logging
import time

from hsm_test_framework.pages.base_page import BasePage, TIMEOUT

logger = logging.getLogger(__name__)


class UserManagementPage(BasePage):
    """User Management screen (post-login, sidebar → User)."""

    def refresh(self, step_name=None):
        """Click Refresh to reload the user list."""
        with self._step(step_name):
            self.driver.click_button(auto_id="btnRefresh")
            time.sleep(2)
            logger.info("User list refreshed")
        return self

    def get_user_table(self):
        """Read user list table data.

        Returns:
            dict with 'headers' (list[str]) and 'rows' (list[list[str]]).
        """
        data = self.driver.get_table_data()
        logger.info(
            f"User table: {len(data['rows'])} rows, "
            f"headers={data['headers']}",
        )
        return data

    def get_user_count(self):
        """Return number of rows in the user table (lightweight)."""
        data = self.driver.get_table_data()
        return len(data["rows"])

    def get_available_profiles(self):
        """Return list of available profile names from the cbProfiles combobox.

        Call after clicking btnAdd (create user form is open).
        """
        items = self.driver.get_combobox_items(auto_id="cbProfiles")
        logger.info(f"Available profiles: {items}")
        return items

    def create_user(self, username, password, profile_name=None,
                    step_name=None):
        """Create a new user account.

        Args:
            username: Account username.
            password: Account password.
            profile_name: Profile to assign (selected from cbProfiles).
            step_name: Optional evidence step description.

        Returns:
            str: Confirmation message from the popup dialog.
        """
        with self._step(step_name):
            self.driver.click_button(auto_id="btnAdd")
            self.driver.wait_for_element(
                timeout=TIMEOUT, auto_id="txtUsername",
            )
            # Fill username and password FIRST, then select profile last
            # (matching recorded flow order: username → profile → password)
            self.driver.type_text(username, auto_id="txtUsername")
            self.driver.click_radio(auto_id="rbPass")
            self.driver.type_text(
                password, auto_id="txtPass", sensitive=True,
            )
            self.driver.type_text(
                password, auto_id="txtPassRepeat", sensitive=True,
            )
            # Select profile by expanding dropdown and clicking the item
            # directly — combo.select() silently fails on this WinForms combo
            if profile_name:
                available = self.driver.click_combobox_item(
                    auto_id="cbProfiles", value=profile_name,
                )
                logger.info(f"Selected profile: '{profile_name}'")
            self.driver.click_button(auto_id="btnCreate")
            message = self.dismiss_ok_with_message()
            logger.info(f"User '{username}' created with profile '{profile_name}'")
            return message

    def sync(self, step_name=None, sync_timeout=120):
        """Click Sync button and wait for sync result.

        The HSM sync takes ~20-30s. The result popup is spawned from an
        async thread, so top_window() doesn't detect it reliably.
        We use wait_for_element to find the OK button (which works), then
        click it directly on the same element reference — avoiding a
        second _active_window() lookup that would lose the popup.

        Args:
            step_name: Optional evidence step description.
            sync_timeout: Max seconds to wait for sync result.

        Returns:
            str: Confirmation message from the sync result popup.
        """
        with self._step(step_name):
            self.driver.click_button(auto_id="btnSync")
            logger.info("Sync started, waiting for result...")

            # wait_for_element finds the OK button once it appears (~28s)
            ok_btn = self.driver.wait_for_element(
                timeout=sync_timeout,
                auto_id="2",
                control_type="Button",
            )

            # Read sync message from the same window (before clicking OK)
            message = ""
            try:
                parent = ok_btn.parent()
                for ctrl_type in ("Static", "Text"):
                    try:
                        children = parent.children(control_type=ctrl_type)
                        for child in children:
                            text = child.window_text()
                            if text and text not in ("OK", "Yes", "No"):
                                message = text
                                break
                    except Exception:
                        continue
                    if message:
                        break
            except Exception:
                pass

            # Click OK directly on the found element (no second lookup)
            logger.info(f"Sync result: '{message}'")
            ok_btn.click_input()

            # Refresh window reference — the direct click_input() bypasses
            # _active_window(), leaving pywinauto's state stale (COM error)
            time.sleep(0.5)
            self.driver.refresh_window()
            logger.info("User sync completed")
            return message

    def debug_table_cells(self):
        """Dump all DataGridView Edit cells with name, auto_id, and value.

        Use this to debug row selection issues. Call from test:
            user_page.debug_table_cells()
        Output goes to logger.info (visible with -s flag).
        """
        grid = self.driver._active_window().child_window(
            auto_id="dataGridView1", control_type="Table",
        )
        grid.wait("visible", timeout=10)

        edits = grid.descendants(control_type="Edit")
        logger.info(f"=== DataGridView Edit cells: {len(edits)} total ===")
        for i, edit in enumerate(edits):
            name = edit.element_info.name or "(no name)"
            auto_id = edit.element_info.automation_id or "(no id)"
            # Try multiple value reading strategies
            val_iface = val_legacy = val_text = ""
            try:
                val_iface = edit.iface_value.CurrentValue
            except Exception:
                val_iface = "<iface_value failed>"
            try:
                val_legacy = edit.legacy_properties().get("Value", "")
            except Exception:
                val_legacy = "<legacy failed>"
            try:
                val_text = edit.window_text()
            except Exception:
                val_text = "<window_text failed>"
            logger.info(
                f"  [{i:2d}] name={name!r:45s} auto_id={auto_id!r:15s} "
                f"iface_value={val_iface!r:25s} legacy={val_legacy!r:25s} "
                f"window_text={val_text!r}"
            )
        logger.info("=== End DataGridView dump ===")

    def _click_user_row(self, username):
        """Click on a user's Username cell in the DataGridView to select the row.

        WinForms DataGridView cells are Edit controls with names like
        "Username Row N, Not sorted." and dynamic auto_ids. We find
        the Username column cell whose value matches, then click it.
        This mirrors the recorded flow (type_text on the Username cell).
        """
        import re as _re

        grid = self.driver._active_window().child_window(
            auto_id="dataGridView1", control_type="Table",
        )
        grid.wait("visible", timeout=10)

        # Find Edit descendants that are Username column cells
        edits = grid.descendants(control_type="Edit")
        for edit in edits:
            name = edit.element_info.name or ""
            if not _re.match(r"Username Row \d+", name):
                continue
            # Read cell value
            val = ""
            try:
                val = edit.iface_value.CurrentValue
            except Exception:
                try:
                    val = edit.legacy_properties().get("Value", "")
                except Exception:
                    val = edit.window_text() or ""
            if val == username:
                edit.click_input()
                time.sleep(0.5)
                logger.info(f"Clicked '{name}' (value='{username}')")
                return

        raise RuntimeError(
            f"User '{username}' not found in DataGridView Username cells"
        )

    def select_user(self, username, step_name=None):
        """Select a user row in the DataGridView table."""
        with self._step(step_name):
            self._click_user_row(username)
            time.sleep(0.5)
            logger.info(f"Selected user '{username}'")
        return self

    def delete_user(self, username, step_name=None):
        """Select user → click Delete → confirm Yes → return message."""
        with self._step(step_name):
            self._click_user_row(username)
            time.sleep(0.5)
            self.driver.click_button(auto_id="btnDelete")
            # Confirm Yes on "Are you sure?" dialog
            self.driver.wait_for_element(
                timeout=TIMEOUT, auto_id="6", control_type="Button",
            )
            self.driver.click_button(auto_id="6")
            message = self.dismiss_ok_with_message()
            logger.info(f"User '{username}' deleted: '{message}'")
            return message

    def user_exists_in_table(self, username):
        """Check if a username exists in the table.

        Uses get_list_items() as a faster alternative to full table parse.
        Falls back to get_table_data() if list approach finds nothing.
        """
        # Fast: search list items text
        try:
            items = self.driver.get_list_items()
            for item_text in items:
                if username in item_text:
                    logger.info(f"User '{username}' found in list")
                    return True
        except Exception:
            pass

        # Fallback: full table parse
        data = self.driver.get_table_data()
        for row in data["rows"]:
            for cell in row:
                if username in cell:
                    logger.info(f"User '{username}' found in table")
                    return True

        logger.warning(f"User '{username}' NOT found")
        return False

    def get_user_row(self, username):
        """Get the full row data for a specific user.

        Returns:
            tuple: (headers, row) or (headers, None) if not found.
        """
        data = self.get_user_table()
        for row in data["rows"]:
            for cell in row:
                if username in cell:
                    return data["headers"], row
        return data["headers"], None
