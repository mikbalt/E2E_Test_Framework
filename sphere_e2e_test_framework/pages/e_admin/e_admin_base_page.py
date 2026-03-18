"""E-Admin base page — adds E-Admin specific navigation to BasePage.

Provides sidebar navigation (User Management, Profile Management, Logout)
and Terms & Conditions acceptance that are specific to the E-Admin application.
"""

from sphere_e2e_test_framework.pages.base_page import BasePage, TIMEOUT


class EAdminBasePage(BasePage):
    """Base class for E-Admin page objects.

    Extends ``BasePage`` with E-Admin specific navigation helpers.
    Non-E-Admin page objects should inherit from ``BasePage`` directly.
    """

    def agree_and_next(self, step_name=None):
        """Click 'Agree' radio then 'Next >>>' button."""
        with self._step(step_name):
            self.driver.click_radio(auto_id="rbAgree")
            self.driver.wait_for_element(
                timeout=TIMEOUT, auto_id="btnNext", control_type="Button",
            )
            self.driver.click_button(auto_id="btnNext")

    # ------------------------------------------------------------------
    # Sidebar navigation (returns new page instances)
    # ------------------------------------------------------------------
    def goto_user_management(self, step_name=None):
        """Navigate to User Management via sidebar."""
        from sphere_e2e_test_framework.pages.e_admin.user_creation_page import UserCreationPage

        with self._step(step_name):
            self.driver.click_element(auto_id="btnUserManagement")
        return UserCreationPage(self.driver, self.evidence)

    def goto_profile_management(self, step_name=None):
        """Navigate to Profile Management via sidebar."""
        with self._step(step_name):
            self.driver.click_element(auto_id="btnProfileManagement")
        return EAdminBasePage(self.driver, self.evidence)

    def logout(self, step_name=None):
        """Click Logout in sidebar, returns LoginPage."""
        from sphere_e2e_test_framework.pages.e_admin.login_page import LoginPage

        with self._step(step_name):
            self.driver.click_button(auto_id="btnLogout")
        return LoginPage(self.driver, self.evidence)
