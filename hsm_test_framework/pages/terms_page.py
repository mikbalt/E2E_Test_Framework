"""
Terms & Conditions page object for E-Admin.

Thin wrapper around the agree-and-next flow. Returns self so the caller
decides what page comes next.
"""

import logging

from hsm_test_framework.pages.base_page import BasePage

logger = logging.getLogger(__name__)


class TermsPage(BasePage):
    """Generic Terms & Conditions accept page."""

    def accept(self, step_name=None):
        """Click Agree + Next. Returns self for chaining."""
        self.agree_and_next(step_name=step_name)
        return self
