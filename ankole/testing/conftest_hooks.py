"""Shared dependency-tracking hooks for TCMS case ordering.

Import these into ``tests/ui/conftest.py`` (the shared parent) to avoid
duplicate hook registration when running multiple app suites::

    from ankole.testing.conftest_hooks import *  # noqa: F401
"""

import logging

import pytest

logger = logging.getLogger(__name__)

# Track passed TCMS case IDs across the session for dependency checking
_passed_cases: set[int] = set()
# TCMS case IDs present in the current collection (populated by pytest_collection_modifyitems)
_collected_cases: set[int] = set()


@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(items):
    """Sort by @pytest.mark.order(N) and record collected TCMS case IDs.

    trylast=True ensures this runs AFTER the plugin's Kiwi filter and
    pytest-ordering, so:
    1. Items already survived filtering (Kiwi, smoke gate, etc.)
    2. We enforce @pytest.mark.order(N) regardless of which ordering
       plugin is installed (pytest-ordering 0.6 only recognizes
       @pytest.mark.run(order=N), not @pytest.mark.order(N)).

    Tests with order(N) are sorted by N (ascending).
    Tests without order() keep their original relative position,
    placed after all ordered tests.
    """
    # --- Sort by @pytest.mark.order(N) ---
    ordered = []
    unordered = []
    for item in items:
        marker = item.get_closest_marker("order")
        if marker and marker.args:
            ordered.append((marker.args[0], item))
        else:
            unordered.append(item)

    if ordered:
        ordered.sort(key=lambda x: x[0])
        items[:] = [item for _, item in ordered] + unordered

    # --- Record collected TCMS case IDs ---
    for item in items:
        marker = item.get_closest_marker("tcms")
        if marker:
            case_id = marker.kwargs.get("case_id")
            if case_id:
                _collected_cases.add(case_id)


def track_passed_case(item, report):
    """Record a passed TCMS case ID for dependency checking.

    Call this from your ``pytest_runtest_makereport`` hook after obtaining the
    report.  Extracted as a helper so consumers that define their own
    ``pytest_runtest_makereport`` can invoke it without hook shadowing.
    """
    if report.when == "call" and report.passed:
        marker = item.get_closest_marker("tcms")
        if marker:
            case_id = marker.kwargs.get("case_id")
            if case_id:
                _passed_cases.add(case_id)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Record passed TCMS case IDs for dependency checking."""
    outcome = yield
    report = outcome.get_result()
    track_passed_case(item, report)


def pytest_runtest_setup(item):
    """Skip test if any depends_on case_id did not pass.

    Only enforced when the dependency is in the current collection.
    If the dependency test was not collected (e.g. not in Kiwi run),
    assume the precondition is already satisfied externally.
    """
    marker = item.get_closest_marker("depends_on")
    if marker:
        for case_id in marker.args:
            if case_id in _collected_cases and case_id not in _passed_cases:
                pytest.skip(
                    f"Dependency TC-{case_id} did not pass"
                )
