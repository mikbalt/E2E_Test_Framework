"""
Key Custodian login page object for E-Admin.

Used during the CCMK import phase of the key ceremony.
"""

import logging

from hsm_test_framework.pages.base_page import BasePage, TIMEOUT

logger = logging.getLogger(__name__)


class KCLoginPage(BasePage):
    """Key Custodian login screen (during CCMK import)."""

    def login(self, username, password, step_name=None):
        """Login as Key Custodian via password authentication.

        Returns a CCMKImportPage.
        """
        from hsm_test_framework.pages.ccmk_import_page import CCMKImportPage

        with self._step(step_name):
            self.driver.refresh_window()
            self.driver.wait_for_element(
                timeout=TIMEOUT, auto_id="rbPassword",
            )
            self.driver.click_radio(auto_id="rbPassword")
            self.driver.type_text(username, auto_id="1001")
            self.driver.type_text(
                password, auto_id="txtPassword", sensitive=True,
            )
            self.driver.click_button(auto_id="btnLogin")
            logger.info(f"Key Custodian '{username}' logged in")

        return CCMKImportPage(self.driver, self.evidence)
