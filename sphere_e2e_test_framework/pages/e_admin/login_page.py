"""
Login page object for E-Admin.

Handles session selection, HSM connection, and password-based login.
"""

import logging

import allure

from sphere_e2e_test_framework.pages.e_admin.e_admin_base_page import EAdminBasePage, TIMEOUT

logger = logging.getLogger(__name__)


class LoginPage(EAdminBasePage):
    """E-Admin login / connection screen."""

    def connect_to_hsm(self, step_name=None):
        """Click Connect, wait for confirmation popup, click OK.

        Returns a DashboardPage after refreshing the window.
        """
        from sphere_e2e_test_framework.pages.e_admin.dashboard_page import DashboardPage

        with self._step(step_name):
            self.driver.click_button(auto_id="btnUpdate")
            logger.info("Connect button clicked")

            self.driver.wait_for_element(
                timeout=TIMEOUT, auto_id="btnOKE", control_type="Button",
            )

            popup = self.driver.check_popup()
            if popup:
                logger.info(f"Popup detected: '{popup.window_text()}'")
                try:
                    allure.attach(
                        popup.window_text(),
                        name="popup_text",
                        attachment_type=allure.attachment_type.TEXT,
                    )
                except Exception:
                    pass

            if self.evidence:
                self.evidence.screenshot(self.driver, "connect_popup_visible")

            self.driver.click_button(auto_id="btnOKE")
            logger.info("OK button clicked")

        self.driver.refresh_window()
        return DashboardPage(self.driver, self.evidence)

    def open_login_form(self, step_name=None):
        """Click 'Click to login!' link to open the login form.

        Waits for the session combobox to appear before returning.
        """
        with self._step(step_name):
            self.driver.click_element(
                auto_id="lbl_clickLogin", control_type="Text",
            )
            self.driver.wait_for_element(
                timeout=TIMEOUT, auto_id="cbSession",
                control_type="ComboBox",
            )
            logger.info("Login form opened")

    def get_sessions(self):
        """Return list of available session names from the combobox.

        Call after open_login_form(). Useful for data-driven tests.
        """
        items = self.driver.get_combobox_items(auto_id="cbSession")
        logger.info(f"Available sessions: {items}")
        return items

    def select_session(self, session_name, step_name=None):
        """Select a session from the session combobox (cbSession).

        Args:
            session_name: Display text, e.g. 'Admin Session', 'User_Session'.
        """
        with self._step(step_name):
            self.driver.select_combobox(
                auto_id="cbSession", value=session_name,
            )
            logger.info(f"Session selected: '{session_name}'")

    def login(self, username, password, step_name=None):
        """Login with username/password via the Password radio flow.

        Assumes the login form is already visible (call open_login_form()
        and select_session() first if on the post-ceremony dashboard).

        Waits for sidebar buttons to appear (post-login dashboard loaded)
        before returning.

        Returns a DashboardPage.
        """
        from sphere_e2e_test_framework.pages.e_admin.dashboard_page import DashboardPage

        with self._step(step_name):
            self.driver.click_radio(auto_id="rbPassword")
            self.driver.type_text(username, auto_id="1001")
            self.driver.type_text(
                password, auto_id="txtPassword", sensitive=True,
            )
            self.driver.click_button(auto_id="btnLogin")
            # Wait until dashboard is fully loaded (sidebar visible)
            self.driver.wait_for_element(
                timeout=TIMEOUT, auto_id="btnLogOut", control_type="Button",
            )
            logger.info(f"Logged in as '{username}'")

        self.driver.refresh_window()
        return DashboardPage(self.driver, self.evidence)

    def login_expect_failure(self, username, password, timeout=TIMEOUT,
                             step_name=None):
        """Attempt login expecting failure. Returns error message.

        Unlike login(), this does NOT wait for the dashboard. Instead it
        expects an error popup (OK button) after clicking Login.
        """
        with self._step(step_name):
            self.driver.click_radio(auto_id="rbPassword")
            self.driver.type_text(username, auto_id="1001")
            self.driver.type_text(
                password, auto_id="txtPassword", sensitive=True,
            )
            self.driver.click_button(auto_id="btnLogin")
            # Expect error popup instead of dashboard
            self.driver.wait_for_element(
                timeout=timeout, auto_id="2", control_type="Button",
            )
            message = self.dismiss_ok_with_message()
            logger.info(f"Login failed as expected: '{message}'")
            return message

    def full_login(self, session_name, username, password, step_name=None):
        """Convenience: open form → select session → login in one call.

        Returns a DashboardPage.
        """
        with self._step(step_name):
            self.open_login_form()
            self.select_session(session_name)
            return self.login(username, password)
