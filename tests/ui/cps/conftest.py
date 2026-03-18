"""
tests/ui/cps/conftest.py -- CPS-specific fixtures.

Provides:
- cps_config: session-scoped config extracted from settings.yaml
- cps_driver: function-scoped UIDriver
- window_monitor: background monitor for unexpected windows
- collect_app_logs: auto-collects CPS AppLogs (PRE + POST snapshots) per test

See COOKBOOK.md for a full walkthrough of how this conftest works.
"""

from sphere_e2e_test_framework.testing.conftest_factory import (
    make_app_config_fixture,
    make_driver_fixture,
    make_window_monitor_fixture,
    make_app_logs_fixture,
)

cps_config = make_app_config_fixture("cps")
cps_driver = make_driver_fixture("cps")
window_monitor = make_window_monitor_fixture("cps")
collect_app_logs = make_app_logs_fixture("cps")
