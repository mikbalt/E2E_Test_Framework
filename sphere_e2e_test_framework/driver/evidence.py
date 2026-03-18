"""
Evidence Module - Screenshots, logging, and recording for test evidence.

Captures:
- Screenshots (per step and on failure)
- Full desktop screenshots
- Test execution logs
- Attaches everything to Allure report

Usage:
    evidence = Evidence("test_login")
    evidence.screenshot(driver, "step_1_opened")
    evidence.log("Clicked login button")
    evidence.desktop_screenshot("full_desktop")
    evidence.finalize()
"""

import datetime
import logging
import os
import time
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class Evidence:
    """Manages test evidence collection: screenshots, logs, recordings."""

    def __init__(self, test_name, base_dir="evidence"):
        self.test_name = test_name
        self.timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.evidence_dir = os.path.join(
            base_dir, f"{self.test_name}_{self.timestamp}"
        )
        os.makedirs(self.evidence_dir, exist_ok=True)

        self.step_count = 0
        self.log_entries = []
        self.screenshots = []
        self._finalized = False

        # Setup file logger scoped to framework namespace (avoids root logger
        # pollution that causes cross-contamination in parallel test runs).
        self.log_file = os.path.join(self.evidence_dir, "test_log.txt")
        self._file_handler = logging.FileHandler(self.log_file, encoding="utf-8")
        self._file_handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s - %(message)s")
        )
        self._framework_logger = logging.getLogger("sphere_e2e_test_framework")
        self._framework_logger.addHandler(self._file_handler)

        logger.info(f"Evidence dir: {self.evidence_dir}")

    def step(self, description):
        """Mark a test step for evidence tracking.

        Note: This method only handles logging and counting.
        Allure step integration is handled by tracked_step() or
        manual allure.step() wrapping to avoid double-nesting.
        """
        self.step_count += 1
        msg = f"STEP {self.step_count}: {description}"
        logger.info(msg)
        self.log_entries.append(msg)

    def screenshot(self, driver, name=None):
        """
        Capture screenshot from UIDriver and save + attach to Allure.

        Args:
            driver: UIDriver instance.
            name: Optional name for the screenshot file.
        """
        if name is None:
            name = f"step_{self.step_count:03d}"

        filename = f"{name}.png"
        filepath = os.path.join(self.evidence_dir, filename)

        try:
            img = driver.take_screenshot(name)
            img.save(filepath)
            self.screenshots.append(filepath)
            logger.info(f"Screenshot saved: {filepath}")

            # Attach to Allure
            try:
                import allure
                with open(filepath, "rb") as f:
                    allure.attach(
                        f.read(),
                        name=name,
                        attachment_type=allure.attachment_type.PNG,
                    )
            except ImportError:
                pass

            return filepath
        except Exception as e:
            logger.error(f"Failed to capture screenshot: {e}")
            return None

    def desktop_screenshot(self, name="desktop"):
        """Capture full desktop screenshot."""
        import mss
        from PIL import Image

        filename = f"{name}.png"
        filepath = os.path.join(self.evidence_dir, filename)

        try:
            with mss.mss() as sct:
                monitor = sct.monitors[0]  # Full virtual screen
                screenshot = sct.grab(monitor)
                img = Image.frombytes(
                    "RGB", screenshot.size, screenshot.bgra, "raw", "BGRX"
                )
                img.save(filepath)

            self.screenshots.append(filepath)
            logger.info(f"Desktop screenshot saved: {filepath}")

            try:
                import allure
                with open(filepath, "rb") as f:
                    allure.attach(
                        f.read(),
                        name=name,
                        attachment_type=allure.attachment_type.PNG,
                    )
            except ImportError:
                pass

            return filepath
        except Exception as e:
            logger.error(f"Failed desktop screenshot: {e}")
            return None

    def attach_text(self, content, name="output"):
        """Attach text content (e.g., console output) to evidence."""
        filepath = os.path.join(self.evidence_dir, f"{name}.txt")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"Text evidence saved: {filepath}")

        try:
            import allure
            allure.attach(content, name=name, attachment_type=allure.attachment_type.TEXT)
        except ImportError:
            pass

        return filepath

    def attach_file(self, filepath, name=None):
        """Attach an existing file to evidence."""
        if name is None:
            name = os.path.basename(filepath)

        try:
            import allure
            ext = os.path.splitext(filepath)[1].lower()
            attachment_map = {
                ".png": allure.attachment_type.PNG,
                ".jpg": allure.attachment_type.JPG,
                ".txt": allure.attachment_type.TEXT,
                ".json": allure.attachment_type.JSON,
                ".xml": allure.attachment_type.XML,
                ".html": allure.attachment_type.HTML,
                ".csv": allure.attachment_type.CSV,
            }
            att_type = attachment_map.get(ext, allure.attachment_type.TEXT)

            with open(filepath, "rb") as f:
                allure.attach(f.read(), name=name, attachment_type=att_type)
        except ImportError:
            pass

    def log(self, message, level="INFO"):
        """Add a log entry to evidence."""
        self.log_entries.append(f"[{level}] {message}")
        getattr(logger, level.lower(), logger.info)(message)

    def finalize(self):
        """Finalize evidence collection and cleanup."""
        if self._finalized:
            return
        self._finalized = True

        # Write summary
        summary_path = os.path.join(self.evidence_dir, "summary.txt")
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(f"Test: {self.test_name}\n")
            f.write(f"Timestamp: {self.timestamp}\n")
            f.write(f"Total Steps: {self.step_count}\n")
            f.write(f"Screenshots: {len(self.screenshots)}\n")
            f.write(f"\n--- Log ---\n")
            for entry in self.log_entries:
                f.write(f"{entry}\n")

        # Cleanup file handler
        self._framework_logger.removeHandler(self._file_handler)
        self._file_handler.close()

        logger.info(
            f"Evidence finalized: {self.step_count} steps, "
            f"{len(self.screenshots)} screenshots"
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.finalize()

    def __del__(self):
        if not self._finalized:
            try:
                self.finalize()
            except Exception:
                pass


class StepTracker:
    """Context manager for tracking test steps with automatic screenshots.

    Args:
        evidence: Evidence instance.
        driver: UIDriver instance.
        description: Step description.
        auto_screenshot: If True (default), capture screenshot on exit.
            Set to False for manual screenshot control within the step.
    """

    def __init__(self, evidence, driver, description, auto_screenshot=True):
        self.evidence = evidence
        self.driver = driver
        self.description = description
        self.auto_screenshot = auto_screenshot

    def __enter__(self):
        self.evidence.step(self.description)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self.auto_screenshot and exc_type is None:
            return  # Skip screenshot on success when manual mode
        # Always capture on failure, even in manual mode
        suffix = "fail" if exc_type else "pass"
        name = f"step_{self.evidence.step_count:03d}_{suffix}"
        result = self.evidence.screenshot(self.driver, name)
        if result is None:
            # Fallback: capture full desktop if window screenshot failed
            logger.warning("Window screenshot failed, falling back to desktop screenshot")
            self.evidence.desktop_screenshot(f"{name}_desktop")


@contextmanager
def tracked_step(evidence, driver, description, auto_screenshot=True):
    """
    Combined allure.step + StepTracker — eliminates double nesting.

    Replaces:
        with allure.step("desc"):
            with StepTracker(evidence, driver, "desc"):
                ...

    With:
        with tracked_step(evidence, driver, "desc"):
            ...

    For manual screenshot control:
        with tracked_step(evidence, driver, "desc", auto_screenshot=False):
            driver.type_text("admin", auto_id="1001")
            evidence.screenshot(driver, "after_username")

    Args:
        evidence: Evidence instance for logging and screenshots.
        driver: UIDriver instance for window screenshots.
        description: Human-readable step description.
        auto_screenshot: If True (default), capture screenshot on step exit.
            Set to False to take screenshots manually within the step.
    """
    try:
        import allure
        _has_allure = True
    except ImportError:
        _has_allure = False

    if _has_allure:
        with allure.step(description):
            with StepTracker(evidence, driver, description,
                             auto_screenshot=auto_screenshot):
                yield
    else:
        with StepTracker(evidence, driver, description,
                         auto_screenshot=auto_screenshot):
            yield
