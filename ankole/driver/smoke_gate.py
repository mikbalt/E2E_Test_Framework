"""
Smoke Gate - Fail-fast mechanism for smoke tests.

When --smoke-gate is enabled:
1. Smoke-marked tests are reordered to run before all other tests.
2. If any smoke test fails, remaining non-smoke tests are skipped.
3. A clear abort message is printed.

The gate runs ALL smoke tests before deciding whether to proceed --
it does not abort mid-smoke-suite, giving better diagnostics.

Usage:
    pytest --smoke-gate -v
"""

import logging

logger = logging.getLogger(__name__)


class SmokeGate:
    """Tracks smoke test outcomes and controls the gate."""

    def __init__(self):
        self.active = False
        self.smoke_failed = False
        self.smoke_count = 0
        self.smoke_passed = 0
        self.smoke_failures = []

    def activate(self):
        """Enable the smoke gate."""
        self.active = True
        logger.info("Smoke gate ACTIVATED: smoke tests will run first")

    @property
    def gate_failed(self):
        """True if any smoke test has failed."""
        return self.active and self.smoke_failed

    def record_smoke_result(self, nodeid, passed):
        """Record a smoke test result."""
        self.smoke_count += 1
        if passed:
            self.smoke_passed += 1
        else:
            self.smoke_failed = True
            self.smoke_failures.append(nodeid)

    def summary(self):
        """Return summary message for the gate status."""
        failed_count = len(self.smoke_failures)
        lines = [
            "=" * 60,
            "SMOKE GATE FAILED",
            "=" * 60,
            f"Smoke tests: {self.smoke_count} total, "
            f"{self.smoke_passed} passed, {failed_count} failed",
            "",
            "Failed smoke tests:",
        ]
        for nodeid in self.smoke_failures:
            lines.append(f"  - {nodeid}")
        lines.append("")
        lines.append("Remaining non-smoke tests were SKIPPED.")
        lines.append("=" * 60)
        return "\n".join(lines)


def reorder_smoke_first(items):
    """
    Reorder test items so that smoke-marked tests run before others.

    Preserves relative order within each group (stable partition).

    Args:
        items: List of pytest Item objects (mutated in place).
    """
    smoke_items = []
    other_items = []

    for item in items:
        if is_smoke_test(item):
            smoke_items.append(item)
        else:
            other_items.append(item)

    items[:] = smoke_items + other_items
    logger.info(
        f"Smoke gate reorder: {len(smoke_items)} smoke tests first, "
        f"{len(other_items)} other tests after"
    )


def is_smoke_test(item):
    """Check if a test item has the @pytest.mark.smoke marker."""
    return "smoke" in item.keywords
