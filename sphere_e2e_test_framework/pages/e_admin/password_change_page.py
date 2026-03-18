"""
Password change page object for E-Admin.

Handles the SUPER_USER default password change during key ceremony.
"""

import logging

from sphere_e2e_test_framework.pages.e_admin.e_admin_base_page import EAdminBasePage

logger = logging.getLogger(__name__)


class PasswordChangePage(EAdminBasePage):
    """SUPER_USER password change form."""

    def change_password(self, old_password, new_password, step_name=None):
        """Fill old/new/repeat passwords and submit.

        Dismisses the confirmation dialog automatically.
        """
        with self._step(step_name):
            self.driver.type_text(
                old_password, auto_id="txtOldPass", sensitive=True,
            )
            self.driver.type_text(
                new_password, auto_id="txtNewPass", sensitive=True,
            )
            self.driver.type_text(
                new_password, auto_id="txtRepeatNewPass", sensitive=True,
            )
            self.driver.click_button(auto_id="btnChangePass")
            logger.info("Password change submitted")
            self.dismiss_ok()
            logger.info("SUPER_USER password changed successfully")
