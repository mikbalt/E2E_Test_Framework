"""
Dashboard page object for E-Admin.

The main screen after connecting to the HSM.
"""

import logging
import time

from sphere_e2e_test_framework.pages.e_admin.e_admin_base_page import EAdminBasePage

logger = logging.getLogger(__name__)


class DashboardPage(EAdminBasePage):
    """E-Admin dashboard (post-connection main screen)."""

    def is_visible(self):
        """Check if the dashboard main window is visible."""
        return self.driver.main_window.is_visible()

    def start_hsm_init(self, step_name=None):
        """Click 'HSM Initialization' button.

        Returns a TermsPage (first T&C screen of the ceremony).
        """
        from sphere_e2e_test_framework.pages.e_admin.terms_page import TermsPage

        with self._step(step_name):
            self.driver.click_button(auto_id="btnHSMInit")
            logger.info("HSM Initialization started")

        self.driver.refresh_window()
        return TermsPage(self.driver, self.evidence)

    def get_logged_in_user(self):
        """Read the username from lbl_clickLogin label.

        After login, this label changes from 'Click to login!' to the
        logged-in username (e.g. 'admin', 'user_op_1').
        """
        return self.driver.get_text(
            auto_id="lbl_clickLogin", control_type="Text",
        )

    def open_login(self):
        """Return a LoginPage for post-ceremony login flows."""
        from sphere_e2e_test_framework.pages.e_admin.login_page import LoginPage
        return LoginPage(self.driver, self.evidence)

    def goto_profile(self, step_name=None):
        """Click Profile sidebar button.

        Returns a ProfileManagementPage.
        """
        from sphere_e2e_test_framework.pages.e_admin.profile_management_page import (
            ProfileManagementPage,
        )

        with self._step(step_name):
            self.driver.click_button(auto_id="btnProfile")
            logger.info("Navigated to Profile Management")
        return ProfileManagementPage(self.driver, self.evidence)

    def goto_user(self, step_name=None):
        """Click User sidebar button.

        Returns a UserManagementPage.
        """
        from sphere_e2e_test_framework.pages.e_admin.user_management_page import (
            UserManagementPage,
        )

        with self._step(step_name):
            self.driver.click_button(auto_id="btnUser")
            logger.info("Navigated to User Management")
        return UserManagementPage(self.driver, self.evidence)

    def goto_reset(self, step_name=None):
        """Click Reset sidebar button.

        Returns a BasePage placeholder (dedicated ResetPage TBD).
        """
        with self._step(step_name):
            self.driver.click_button(auto_id="btnReset")
            logger.info("Navigated to Reset")
        return BasePage(self.driver, self.evidence)

    def logout(self, step_name=None):
        """Click Logout, dismiss confirmation if present, return LoginPage."""
        from sphere_e2e_test_framework.pages.e_admin.login_page import LoginPage

        with self._step(step_name):
            self.driver.click_button(auto_id="btnLogOut")
            time.sleep(1)
            self.driver.refresh_window()
            # Dismiss OK dialog if one appeared after logout
            if self.driver.element_exists(auto_id="2", control_type="Button"):
                self.driver.click_button(auto_id="2")
            logger.info("Logged out")
        return LoginPage(self.driver, self.evidence)
