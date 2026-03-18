"""
Terms & Conditions page object for E-Admin.

Thin wrapper around the agree-and-next flow. Returns self so the caller
decides what page comes next.
"""

import logging

from sphere_e2e_test_framework.pages.e_admin.e_admin_base_page import EAdminBasePage

logger = logging.getLogger(__name__)


class TermsPage(EAdminBasePage):
    """Generic Terms & Conditions accept page."""

    def accept(self, step_name=None):
        """Click Agree + Next. Returns self for chaining."""
        self.agree_and_next(step_name=step_name)
        return self
