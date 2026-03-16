"""
User creation page object for E-Admin.

Handles creating Admin, Key Custodian, and Auditor accounts during
the key ceremony flow.
"""

import logging

from hsm_test_framework.pages.base_page import BasePage, TIMEOUT

logger = logging.getLogger(__name__)


class UserCreationPage(BasePage):
    """User creation form (Admin, KC, Auditor)."""

    def create_user(self, username, password, add_button_id=None,
                    step_name=None):
        """Fill the create-user form and submit.

        Args:
            username: Account username.
            password: Account password.
            add_button_id: If provided, click this button first to open
                the form (e.g. 'btnAdd1', 'btnAuditorCreate').
            step_name: Optional evidence step description.
        """
        with self._step(step_name):
            if add_button_id:
                self.driver.click_button(auto_id=add_button_id)
                self.driver.wait_for_element(
                    timeout=TIMEOUT, auto_id="txtUsername",
                )

            self.driver.type_text(username, auto_id="txtUsername")
            self.driver.click_radio(auto_id="rbPass")
            self.driver.type_text(
                password, auto_id="txtPass", sensitive=True,
            )
            self.driver.type_text(
                password, auto_id="txtPassRepeat", sensitive=True,
            )
            self.driver.click_button(auto_id="btnCreate")
            self.dismiss_ok()
            logger.info(f"User '{username}' created")

    def authenticate_super_user(self, password, step_name=None):
        """Authenticate as SUPER_USER (dismiss dialog, enter password, click Auth)."""
        with self._step(step_name):
            self.dismiss_ok()
            self.driver.type_text(
                password, auto_id="txtPassword", sensitive=True,
            )
            self.driver.click_button(auto_id="btnAuth")
            self.driver.wait_for_element(
                timeout=TIMEOUT, auto_id="txtUsername",
            )
            logger.info("SUPER_USER authenticated")
