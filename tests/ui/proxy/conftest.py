"""
tests/ui/proxy/conftest.py -- Proxy-specific fixtures.

Provides:
- proxy_config: session-scoped config extracted from settings.yaml
- proxy_driver: function-scoped UIDriver
- window_monitor: background monitor for unexpected windows
- collect_app_logs: auto-collects Proxy AppLogs (PRE + POST snapshots) per test

See COOKBOOK.md for a full walkthrough of how this conftest works.
"""

from sphere_e2e_test_framework.testing.conftest_factory import (
    make_app_config_fixture,
    make_driver_fixture,
    make_window_monitor_fixture,
    make_app_logs_fixture,
)

proxy_config = make_app_config_fixture("proxy")
proxy_driver = make_driver_fixture("proxy")
window_monitor = make_window_monitor_fixture("proxy")
collect_app_logs = make_app_logs_fixture("proxy")
