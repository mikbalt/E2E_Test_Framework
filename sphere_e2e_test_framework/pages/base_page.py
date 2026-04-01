"""
Base page object for WinForms UI automation.

Provides shared helpers: evidence-tracked steps and dialog dismissal.
App-specific navigation belongs in subclasses (e.g. ``EAdminBasePage``).
"""

import logging
import os
import time
from contextlib import contextmanager

from sphere_e2e_test_framework.driver.evidence import tracked_step

logger = logging.getLogger(__name__)

# Default timeout for wait_for_element calls (seconds).
# Override per-environment via PAGE_TIMEOUT env var (e.g. PAGE_TIMEOUT=600).
# HSM operations (sync, CCMK import) routinely exceed 2 minutes.
TIMEOUT = int(os.environ.get("PAGE_TIMEOUT", 300))


class BasePage:
    """Base class for all page objects (generic WinForms)."""

    def __init__(self, driver, evidence=None):
        self.driver = driver
        self.evidence = evidence

    # ------------------------------------------------------------------
    # Hybrid evidence step
    # ------------------------------------------------------------------
    @contextmanager
    def _step(self, description, auto_screenshot=None):
        """Wrap a block in tracked_step if evidence is available.

        Args:
            description: Step description for evidence/allure.
            auto_screenshot: If None (default), auto-screenshot is enabled.
                Set to False to take screenshots manually within the step.

        Usage::

            with self._step("Given: user logs in"):
                self.driver.click_button(...)

            with self._step("Fill form", auto_screenshot=False):
                self.driver.type_text("admin", auto_id="1001")
                self.evidence.screenshot(self.driver, "after_username")
        """
        if auto_screenshot is None:
            auto_screenshot = True
        if self.evidence and description:
            with tracked_step(self.evidence, self.driver, description,
                              auto_screenshot=auto_screenshot):
                yield
        else:
            yield

    # ------------------------------------------------------------------
    # Mid-step screenshot helper
    # ------------------------------------------------------------------
    def _snap(self, label):
        """Capture a mid-step screenshot before a transient UI event disappears.

        Use before clicking dismiss/confirm buttons so popups, dialogs,
        and notifications are captured in evidence.

        Args:
            label: Short descriptive suffix (e.g. ``"confirm_dialog"``).
                   Saved as ``step_NNN_{label}.png``.
        """
        if self.evidence:
            name = f"step_{self.evidence.step_count:03d}_{label}"
            self.evidence.screenshot(self.driver, name)

    # ------------------------------------------------------------------
    # Common dialog helpers
    # ------------------------------------------------------------------
    def dismiss_ok(self, step_name=None):
        """Dismiss a dialog by clicking OK (auto_id='2')."""
        with self._step(step_name):
            self.driver.wait_for_element(
                timeout=TIMEOUT, auto_id="2", control_type="Button",
            )
            self._snap("popup_before_ok")
            self.driver.click_button(auto_id="2")

    def dismiss_ok_with_message(self, step_name=None):
        """Dismiss OK dialog and return popup message text.

        Reads the popup's text content before clicking OK.
        Tries multiple strategies: popup children (Text, Static),
        active window descendants, and window_text() fallback.
        """
        message = ""
        with self._step(step_name):
            self.driver.wait_for_element(
                timeout=TIMEOUT, auto_id="2", control_type="Button",
            )
            # Try reading from popup or active window
            targets = []
            popup = self.driver.check_popup()
            if popup:
                targets.append(popup)
            targets.append(self.driver._active_window())

            for target in targets:
                if message:
                    break
                # WinForms MessageBox uses Static; UIA may expose as Text
                for ctrl_type in ("Static", "Text"):
                    try:
                        children = target.children(control_type=ctrl_type)
                        for child in children:
                            text = child.window_text()
                            if text and text not in ("OK", "Yes", "No", "Cancel"):
                                message = text
                                break
                    except Exception:
                        continue
                    if message:
                        break
                # Fallback: window title
                if not message:
                    try:
                        message = target.window_text() or ""
                    except Exception:
                        pass

            logger.info(f"Popup message: '{message}'")
            self._snap("popup_message")
            self.driver.click_button(auto_id="2")
        return message

