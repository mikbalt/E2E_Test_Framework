"""Unit tests for Visual Regression module."""

import os
from unittest.mock import MagicMock

import pytest

from ankole.driver.visual import VisualCompareResult, VisualComparator


class TestVisualCompareResult:
    """Tests for VisualCompareResult."""

    def test_assert_match_passes(self):
        result = VisualCompareResult(
            match=True, diff_ratio=0.005,
            baseline_path="b.png", actual_path="a.png",
        )
        assert result.assert_match(threshold=0.01) is result

    def test_assert_match_fails(self):
        result = VisualCompareResult(
            match=False, diff_ratio=0.05,
            baseline_path="b.png", actual_path="a.png",
        )
        with pytest.raises(AssertionError, match="Visual mismatch"):
            result.assert_match(threshold=0.01)


class TestVisualComparator:
    """Tests for VisualComparator."""

    def test_creates_directories(self, tmp_path):
        comp = VisualComparator(
            baseline_dir=str(tmp_path / "baselines"),
            actual_dir=str(tmp_path / "actual"),
            diff_dir=str(tmp_path / "diff"),
        )
        assert os.path.isdir(str(tmp_path / "baselines"))
        assert os.path.isdir(str(tmp_path / "actual"))
        assert os.path.isdir(str(tmp_path / "diff"))

    def test_compare_creates_baseline_when_missing(self, tmp_path):
        """First run creates baseline and returns match=True."""
        from PIL import Image

        comp = VisualComparator(
            baseline_dir=str(tmp_path / "baselines"),
            actual_dir=str(tmp_path / "actual"),
            diff_dir=str(tmp_path / "diff"),
        )

        # Create mock driver with page that takes a screenshot
        mock_driver = MagicMock()

        def fake_screenshot(path=None):
            img = Image.new("RGBA", (100, 100), (255, 0, 0, 255))
            img.save(path)

        mock_driver.page.screenshot = fake_screenshot

        result = comp.compare(mock_driver, "test_page")
        assert result.match is True
        assert result.diff_ratio == 0.0
        assert os.path.exists(result.baseline_path)

    def test_compare_detects_identical(self, tmp_path):
        """Second run with identical screenshot returns match=True."""
        from PIL import Image

        comp = VisualComparator(
            baseline_dir=str(tmp_path / "baselines"),
            actual_dir=str(tmp_path / "actual"),
            diff_dir=str(tmp_path / "diff"),
        )

        # Create baseline manually
        baseline_img = Image.new("RGBA", (100, 100), (255, 0, 0, 255))
        baseline_path = str(tmp_path / "baselines" / "identical_page.png")
        baseline_img.save(baseline_path)

        mock_driver = MagicMock()

        def fake_screenshot(path=None):
            img = Image.new("RGBA", (100, 100), (255, 0, 0, 255))
            img.save(path)

        mock_driver.page.screenshot = fake_screenshot

        result = comp.compare(mock_driver, "identical_page")
        assert result.diff_ratio == 0.0
