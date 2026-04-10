"""Visual regression testing with baseline comparison.

Compares screenshots against baselines using pixel-level diffing::

    comparator = VisualComparator(baseline_dir="baselines")
    result = comparator.compare(driver, "login_page")
    result.assert_match(threshold=0.01)
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class VisualCompareResult:
    """Result of a visual comparison."""

    match: bool
    diff_ratio: float
    baseline_path: str
    actual_path: str
    diff_path: str | None = None

    def assert_match(self, threshold: float = 0.01) -> "VisualCompareResult":
        """Assert the visual difference is within threshold.

        Args:
            threshold: Maximum acceptable diff ratio (0.0 = exact, 1.0 = all different).
        """
        if self.diff_ratio > threshold:
            raise AssertionError(
                f"Visual mismatch: {self.diff_ratio:.4f} exceeds threshold {threshold:.4f}. "
                f"Baseline: {self.baseline_path}, Actual: {self.actual_path}"
                f"{f', Diff: {self.diff_path}' if self.diff_path else ''}"
            )
        return self

    def attach_to_allure(self) -> "VisualCompareResult":
        """Attach comparison images to Allure report."""
        try:
            import allure

            for path, name in [
                (self.baseline_path, "Baseline"),
                (self.actual_path, "Actual"),
                (self.diff_path, "Diff"),
            ]:
                if path and os.path.exists(path):
                    with open(path, "rb") as f:
                        allure.attach(
                            f.read(), name=name,
                            attachment_type=allure.attachment_type.PNG,
                        )
        except ImportError:
            pass
        return self


class VisualComparator:
    """Baseline-based visual regression comparator.

    Manages baseline images, compares screenshots, generates diff images.
    Set env var UPDATE_VISUAL_BASELINES=1 to auto-update baselines.
    """

    def __init__(
        self,
        baseline_dir: str = "baselines",
        actual_dir: str = "evidence/visual/actual",
        diff_dir: str = "evidence/visual/diff",
        threshold: float = 0.01,
    ):
        self.baseline_dir = baseline_dir
        self.actual_dir = actual_dir
        self.diff_dir = diff_dir
        self.default_threshold = threshold
        self._update_baselines = os.environ.get("UPDATE_VISUAL_BASELINES", "").lower() in (
            "1", "true", "yes",
        )

        for d in (self.baseline_dir, self.actual_dir, self.diff_dir):
            os.makedirs(d, exist_ok=True)

    def compare(
        self,
        driver: Any,
        name: str,
        selector: str | None = None,
        mask_selectors: list[str] | None = None,
        threshold: float | None = None,
    ) -> VisualCompareResult:
        """Compare a screenshot against its baseline.

        Args:
            driver: WebDriver instance with a `page` property.
            name: Unique name for this visual checkpoint.
            selector: CSS selector to screenshot a specific element.
            mask_selectors: Selectors for regions to mask (ignore) in comparison.
            threshold: Override default threshold for this comparison.

        Returns:
            VisualCompareResult with comparison details.
        """
        from PIL import Image

        effective_threshold = threshold if threshold is not None else self.default_threshold

        # Capture actual screenshot
        actual_path = os.path.join(self.actual_dir, f"{name}.png")
        if selector:
            element = driver.page.locator(selector)
            element.screenshot(path=actual_path)
        else:
            driver.page.screenshot(path=actual_path)

        baseline_path = os.path.join(self.baseline_dir, f"{name}.png")

        # Update baseline mode
        if self._update_baselines or not os.path.exists(baseline_path):
            import shutil
            shutil.copy2(actual_path, baseline_path)
            logger.info(f"Baseline {'updated' if self._update_baselines else 'created'}: {name}")
            return VisualCompareResult(
                match=True,
                diff_ratio=0.0,
                baseline_path=baseline_path,
                actual_path=actual_path,
            )

        # Load images
        baseline_img = Image.open(baseline_path).convert("RGBA")
        actual_img = Image.open(actual_path).convert("RGBA")

        # Resize actual to baseline dimensions if different
        if baseline_img.size != actual_img.size:
            actual_img = actual_img.resize(baseline_img.size)

        # Apply masks if specified
        if mask_selectors and hasattr(driver, "page"):
            for mask_sel in mask_selectors:
                try:
                    box = driver.page.locator(mask_sel).bounding_box()
                    if box:
                        from PIL import ImageDraw
                        for img in (baseline_img, actual_img):
                            draw = ImageDraw.Draw(img)
                            draw.rectangle(
                                [box["x"], box["y"],
                                 box["x"] + box["width"], box["y"] + box["height"]],
                                fill=(0, 0, 0, 255),
                            )
                except Exception:
                    pass

        # Compare using pixelmatch
        diff_path = os.path.join(self.diff_dir, f"{name}_diff.png")
        try:
            from pixelmatch import pixelmatch
            from pixelmatch.contrib.PIL import pixelmatch as pil_pixelmatch

            diff_img = Image.new("RGBA", baseline_img.size)
            num_diff_pixels = pil_pixelmatch(
                baseline_img, actual_img, diff_img,
                threshold=0.1, includeAA=True,
            )
            diff_img.save(diff_path)
            total_pixels = baseline_img.size[0] * baseline_img.size[1]
            diff_ratio = num_diff_pixels / total_pixels if total_pixels > 0 else 0.0
        except ImportError:
            # Fallback: simple pixel comparison without pixelmatch
            logger.warning("pixelmatch not installed, using basic comparison")
            baseline_data = list(baseline_img.getdata())
            actual_data = list(actual_img.getdata())
            num_diff = sum(1 for a, b in zip(baseline_data, actual_data) if a != b)
            total_pixels = len(baseline_data)
            diff_ratio = num_diff / total_pixels if total_pixels > 0 else 0.0
            diff_path = None

        is_match = diff_ratio <= effective_threshold
        logger.info(
            f"Visual compare '{name}': diff={diff_ratio:.4f}, "
            f"threshold={effective_threshold:.4f}, match={is_match}"
        )

        return VisualCompareResult(
            match=is_match,
            diff_ratio=diff_ratio,
            baseline_path=baseline_path,
            actual_path=actual_path,
            diff_path=diff_path,
        )
