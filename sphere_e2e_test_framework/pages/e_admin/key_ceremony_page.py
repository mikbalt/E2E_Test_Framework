"""
Key Ceremony orchestrator page object for E-Admin.

Optional convenience class that composes the other page objects into
high-level ceremony flows. Tests can use this for a one-liner ceremony
or use individual page objects for finer-grained control.
"""

import logging
import time

from sphere_e2e_test_framework.pages.e_admin.e_admin_base_page import EAdminBasePage, TIMEOUT
from sphere_e2e_test_framework.pages.e_admin.terms_page import TermsPage
from sphere_e2e_test_framework.pages.e_admin.password_change_page import PasswordChangePage
from sphere_e2e_test_framework.pages.e_admin.user_creation_page import UserCreationPage
from sphere_e2e_test_framework.pages.e_admin.kc_login_page import KCLoginPage

logger = logging.getLogger(__name__)


class KeyCeremonyFlow(EAdminBasePage):
    """High-level orchestrator for key ceremony phases."""

    def accept_terms(self, step_name=None):
        """Accept a single T&C page. Returns self."""
        terms = TermsPage(self.driver, self.evidence)
        terms.accept(step_name=step_name)
        return self

    def change_super_user_password(self, old_password, new_password,
                                   step_name=None):
        """Change SUPER_USER password. Returns self."""
        page = PasswordChangePage(self.driver, self.evidence)
        page.change_password(old_password, new_password, step_name=step_name)
        return self

    def authenticate_super_user(self, password, step_name=None):
        """Authenticate SUPER_USER for admin creation. Returns self."""
        page = UserCreationPage(self.driver, self.evidence)
        page.authenticate_super_user(password, step_name=step_name)
        return self

    def create_user(self, username, password, add_button_id=None,
                    step_name=None):
        """Create a user account. Returns self."""
        page = UserCreationPage(self.driver, self.evidence)
        page.create_user(
            username, password,
            add_button_id=add_button_id,
            step_name=step_name,
        )
        return self

    def accept_ccmk_terms(self, pages=3, step_name=None):
        """Accept multi-page CCMK T&C sequence. Returns self."""
        with self._step(step_name):
            terms = TermsPage(self.driver, self.evidence)
            terms.accept()
            time.sleep(30)

            for i in range(1, pages):
                terms.accept()
                if i < pages - 1:
                    time.sleep(5)

            logger.info(f"CCMK T&C sequence completed ({pages} pages)")
        return self

    def import_ccmk(self, username, password, ccmk_secret, ccmk_kcv,
                    ccmk_combined_kcv=None, is_last=False, step_name=None):
        """Login as KC and import a CCMK component. Returns self.

        Args:
            username: Key Custodian username.
            password: Key Custodian password.
            ccmk_secret: CCMK secret hex.
            ccmk_kcv: Individual KCV.
            ccmk_combined_kcv: Combined KCV (final KC only).
            is_last: If True, skip clicking Next after import.
            step_name: Optional evidence step description.
        """
        with self._step(step_name):
            kc_login = KCLoginPage(self.driver, self.evidence)
            ccmk_page = kc_login.login(username, password)
            ccmk_page.import_component(
                ccmk_secret, ccmk_kcv, ccmk_combined_kcv,
            )
            if not is_last:
                ccmk_page.next()
            logger.info(f"CCMK imported for '{username}'")
        return self

    def _wait_finalization_and_dismiss(self):
        """Shared finalization wait: dismiss confirmation, wait for
        finalization-complete popup (up to 300s), then dismiss it."""
        self.dismiss_ok()
        logger.info("Waiting for finalization to complete...")
        self.driver.wait_for_element(
            timeout=300, auto_id="2", control_type="Button",
        )
        logger.info("Finalization complete popup detected")
        self.driver.click_button(auto_id="2")

    def select_fips_and_finalize(self, step_name=None):
        """Select FIPS mode and wait for finalization. Returns self."""
        with self._step(step_name):
            self.driver.click_radio(auto_id="rbDisagree")
            self.driver.click_button(auto_id="btnNext")
            self._wait_finalization_and_dismiss()
            logger.info("FIPS mode selected and initialization finalized")
        return self

    def select_non_fips_and_finalize(self, step_name=None):
        """Select Non-FIPS mode and wait for finalization. Returns self."""
        with self._step(step_name):
            self.driver.click_radio(auto_id="rbAgree")
            self.driver.click_button(auto_id="btnNext")
            self._wait_finalization_and_dismiss()
            logger.info("Non-FIPS mode selected and initialization finalized")
        return self
