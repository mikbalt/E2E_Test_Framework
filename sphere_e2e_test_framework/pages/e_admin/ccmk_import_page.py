"""
CCMK Import page object for E-Admin.

Handles importing a Key Custodian's CCMK component during the key ceremony.
"""

import logging

from sphere_e2e_test_framework.pages.e_admin.e_admin_base_page import EAdminBasePage, TIMEOUT

logger = logging.getLogger(__name__)


class CCMKImportPage(EAdminBasePage):
    """CCMK component import form."""

    def import_component(self, ccmk_secret, ccmk_kcv,
                         ccmk_combined_kcv=None, step_name=None):
        """Fill in the CCMK secret, KCV, and optionally the combined KCV.

        Args:
            ccmk_secret: The CCMK secret hex string.
            ccmk_kcv: The individual KCV value.
            ccmk_combined_kcv: Combined KCV (only for the final KC).
            step_name: Optional evidence step description.
        """
        with self._step(step_name):
            self.driver.wait_for_element(
                timeout=TIMEOUT, auto_id="mtxtSecret",
            )
            self.driver.type_keys_to_field(
                ccmk_secret, auto_id="mtxtSecret", sensitive=True,
            )
            self.driver.type_text(ccmk_kcv, auto_id="txtKCV")

            if ccmk_combined_kcv:
                self.driver.type_text(
                    ccmk_combined_kcv, auto_id="txtCCMKKCV",
                )

            self.driver.click_button(auto_id="btnProcess")
            self.dismiss_ok()
            logger.info("CCMK component imported")

    def next(self):
        """Click Next to proceed to the next KC login.

        Returns a KCLoginPage.
        """
        from sphere_e2e_test_framework.pages.e_admin.kc_login_page import KCLoginPage

        self.driver.click_button(auto_id="btnNext")
        return KCLoginPage(self.driver, self.evidence)
