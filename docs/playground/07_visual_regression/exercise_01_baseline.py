"""Exercise: Visual Regression Testing.

TODO: Create a visual baseline for the login page and compare.
"""

import pytest

from ankole.driver.visual import VisualComparator


@pytest.fixture
def comparator(tmp_path):
    return VisualComparator(
        baseline_dir=str(tmp_path / "baselines"),
        actual_dir=str(tmp_path / "actual"),
        diff_dir=str(tmp_path / "diff"),
    )


@pytest.mark.web
@pytest.mark.visual
class TestVisualBaseline:
    """Visual regression exercises."""

    def test_login_page_baseline(self, web_driver, comparator, base_url):
        """TODO: Create baseline on first run, compare on second."""
        web_driver.goto(f"{base_url}/login")
        web_driver.wait_for_selector("form")

        # First comparison creates the baseline
        result = comparator.compare(web_driver, "playground_login")
        assert result.match is True

        # Second comparison should match the baseline
        result2 = comparator.compare(web_driver, "playground_login")
        result2.assert_match(threshold=0.01)
