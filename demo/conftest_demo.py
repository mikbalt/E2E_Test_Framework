"""
Runtime pytest plugin for demo — injects @pytest.mark.tcms markers.

Loaded as a plugin by run_demo.py via pytest.main(plugins=[module]).
Reads tcms_marker_map from .demo_state.json and injects tcms(case_id=X)
markers onto matching test items BEFORE the framework's bidirectional
filter runs (tryfirst=True).

This avoids editing test files directly — markers are injected at
collection time, transparent to the test code.
"""

import json
import logging
import os

import pytest

logger = logging.getLogger(__name__)

STATE_FILE = os.path.join(os.path.dirname(__file__), ".demo_state.json")

_marker_map = {}


def _load_marker_map():
    """Load function_name → case_id mapping from demo state."""
    global _marker_map
    if _marker_map:
        return _marker_map

    if not os.path.exists(STATE_FILE):
        logger.warning(f"Demo state file not found: {STATE_FILE}")
        return {}

    with open(STATE_FILE, "r") as f:
        state = json.load(f)

    _marker_map = state.get("tcms_marker_map", {})
    if _marker_map:
        logger.info(
            f"Demo conftest: loaded {len(_marker_map)} TCMS marker mapping(s)"
        )
    return _marker_map


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(config, items):
    """Inject @pytest.mark.tcms(case_id=X) onto tests matching the marker map."""
    marker_map = _load_marker_map()
    if not marker_map:
        return

    injected = 0
    for item in items:
        # Match by function name (e.g. "test_connect_and_load_dashboard")
        func_name = item.originalname or item.name
        case_id = marker_map.get(func_name)

        if case_id is not None:
            # Override existing marker so demo uses its own case IDs
            existing = item.get_closest_marker("tcms")
            if existing:
                real_id = existing.kwargs.get("case_id")
                # Remove the real marker so demo's marker takes precedence
                item.own_markers = [
                    m for m in item.own_markers
                    if m.name != "tcms"
                ]
                logger.info(
                    f"Demo override: tcms case_id {real_id} -> {case_id} "
                    f"on {item.nodeid}"
                )
            item.add_marker(pytest.mark.tcms(case_id=case_id))
            injected += 1
            logger.info(
                f"Injected @pytest.mark.tcms(case_id={case_id}) "
                f"onto {item.nodeid}"
            )

    if injected:
        print(f"[demo] Injected TCMS markers on {injected} test(s)")
