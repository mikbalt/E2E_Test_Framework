"""Unit tests for Flaky Test Detection module."""

import json
import os

import pytest

from ankole.plugin.flaky_tracker import FlakyTracker


class TestFlakyTracker:
    """Tests for FlakyTracker."""

    def test_record_and_finalize(self, tmp_path):
        history_path = str(tmp_path / "flaky.json")
        tracker = FlakyTracker(history_path=history_path)

        tracker.record("tests/test_a.py::test_one", passed=True)
        tracker.record("tests/test_b.py::test_two", passed=False)
        tracker.finalize()

        assert os.path.exists(history_path)
        with open(history_path) as f:
            data = json.load(f)
        assert data["history"]["tests/test_a.py::test_one"] == [True]
        assert data["history"]["tests/test_b.py::test_two"] == [False]

    def test_is_flaky_detection(self, tmp_path):
        """A test that flips pass/fail >= threshold is flaky."""
        history_path = str(tmp_path / "flaky.json")
        # Pre-populate history with flips
        history = {
            "history": {
                "test_flaky": [True, False, True, False, True],
            }
        }
        with open(history_path, "w") as f:
            json.dump(history, f)

        tracker = FlakyTracker(
            history_path=history_path, flip_threshold=2,
        )
        assert tracker.is_flaky("test_flaky") is True

    def test_stable_test_not_flaky(self, tmp_path):
        """A test that always passes is not flaky."""
        history_path = str(tmp_path / "flaky.json")
        history = {
            "history": {
                "test_stable": [True, True, True, True, True],
            }
        }
        with open(history_path, "w") as f:
            json.dump(history, f)

        tracker = FlakyTracker(history_path=history_path)
        assert tracker.is_flaky("test_stable") is False

    def test_get_flaky_tests(self, tmp_path):
        history_path = str(tmp_path / "flaky.json")
        history = {
            "history": {
                "flaky_one": [True, False, True],
                "stable_one": [True, True, True],
                "flaky_two": [False, True, False, True],
            }
        }
        with open(history_path, "w") as f:
            json.dump(history, f)

        tracker = FlakyTracker(
            history_path=history_path, flip_threshold=2,
        )
        flaky = tracker.get_flaky_tests()
        flaky_ids = {t.nodeid for t in flaky}
        assert "flaky_one" in flaky_ids
        assert "flaky_two" in flaky_ids
        assert "stable_one" not in flaky_ids

    def test_window_size_trimming(self, tmp_path):
        """History is trimmed to window_size after multiple runs."""
        history_path = str(tmp_path / "flaky.json")

        # Simulate 5 separate runs, each recording one result
        for passed in [True, True, True, False, False]:
            tracker = FlakyTracker(
                history_path=history_path, window_size=3,
            )
            tracker.record("test_trim", passed=passed)
            tracker.finalize()

        with open(history_path) as f:
            data = json.load(f)
        assert len(data["history"]["test_trim"]) == 3

    def test_handles_corrupt_file(self, tmp_path):
        history_path = str(tmp_path / "flaky.json")
        with open(history_path, "w") as f:
            f.write("not json{{{")

        tracker = FlakyTracker(history_path=history_path)
        assert tracker._history == {}
