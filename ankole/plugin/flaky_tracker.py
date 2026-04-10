"""Flaky test detection via result history tracking.

Tracks test results across runs in a JSON file and detects flaky tests
(tests that flip between pass/fail)::

    tracker = FlakyTracker(history_path="evidence/flaky_history.json")
    tracker.record("test_login", passed=True)
    tracker.record("test_login", passed=False)
    assert tracker.is_flaky("test_login")  # True — it flipped
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_HISTORY_PATH = "evidence/flaky_history.json"
DEFAULT_WINDOW_SIZE = 10
DEFAULT_FLIP_THRESHOLD = 2


@dataclass
class FlakyTestInfo:
    """Information about a potentially flaky test."""

    nodeid: str
    flip_count: int
    recent_results: list[bool]
    is_flaky: bool


class FlakyTracker:
    """JSON-based test result history tracker with flaky detection.

    Maintains a rolling window of test results and detects "flips"
    (pass->fail or fail->pass transitions).
    """

    def __init__(
        self,
        history_path: str = DEFAULT_HISTORY_PATH,
        window_size: int = DEFAULT_WINDOW_SIZE,
        flip_threshold: int = DEFAULT_FLIP_THRESHOLD,
    ):
        self.history_path = history_path
        self.window_size = window_size
        self.flip_threshold = flip_threshold
        self._history: dict[str, list[bool]] = {}
        self._current_run: dict[str, bool] = {}
        self._load()

    def _load(self) -> None:
        """Load history from JSON file."""
        if os.path.exists(self.history_path):
            try:
                with open(self.history_path, "r") as f:
                    data = json.load(f)
                self._history = data.get("history", {})
                logger.debug(f"Loaded flaky history: {len(self._history)} tests")
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Could not load flaky history: {e}")
                self._history = {}
        else:
            self._history = {}

    def _save(self) -> None:
        """Save history to JSON file."""
        os.makedirs(os.path.dirname(self.history_path) or ".", exist_ok=True)
        try:
            with open(self.history_path, "w") as f:
                json.dump({"history": self._history}, f, indent=2)
            logger.debug(f"Saved flaky history: {len(self._history)} tests")
        except IOError as e:
            logger.warning(f"Could not save flaky history: {e}")

    def record(self, nodeid: str, passed: bool) -> None:
        """Record a test result for the current run."""
        self._current_run[nodeid] = passed

    def _count_flips(self, results: list[bool]) -> int:
        """Count the number of pass/fail transitions in a result sequence."""
        if len(results) < 2:
            return 0
        return sum(1 for a, b in zip(results, results[1:]) if a != b)

    def is_flaky(self, nodeid: str) -> bool:
        """Check if a test is considered flaky based on its history."""
        results = self._history.get(nodeid, [])
        return self._count_flips(results) >= self.flip_threshold

    def get_flaky_tests(self) -> list[FlakyTestInfo]:
        """Get all tests currently flagged as flaky."""
        flaky = []
        for nodeid, results in self._history.items():
            flip_count = self._count_flips(results)
            if flip_count >= self.flip_threshold:
                flaky.append(FlakyTestInfo(
                    nodeid=nodeid,
                    flip_count=flip_count,
                    recent_results=results[-self.window_size:],
                    is_flaky=True,
                ))
        return flaky

    def finalize(self) -> None:
        """Merge current run results into history and save."""
        for nodeid, passed in self._current_run.items():
            if nodeid not in self._history:
                self._history[nodeid] = []
            self._history[nodeid].append(passed)
            # Trim to window size
            if len(self._history[nodeid]) > self.window_size:
                self._history[nodeid] = self._history[nodeid][-self.window_size:]

        self._save()

        flaky_tests = self.get_flaky_tests()
        if flaky_tests:
            logger.warning(
                f"Flaky tests detected ({len(flaky_tests)}): "
                + ", ".join(t.nodeid for t in flaky_tests)
            )

        self._current_run.clear()
