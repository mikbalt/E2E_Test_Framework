"""Solution: Visual Regression Testing."""

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
class TestVisualBaselineSolution:
    def test_login_page_baseline(self, web_driver, comparator, base_url):
        web_driver.goto(f"{base_url}/login")
        web_driver.wait_for_selector("form")
        result = comparator.compare(web_driver, "sol_login")
        assert result.match is True
        result2 = comparator.compare(web_driver, "sol_login")
        result2.assert_match(threshold=0.01)
