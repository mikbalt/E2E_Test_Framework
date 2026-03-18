"""Testing utilities for consumer test suites.

Provides conftest hooks, utility functions, and fixture factories
to eliminate boilerplate in per-app conftest.py files.
"""

from sphere_e2e_test_framework.testing.conftest_factory import (
    make_app_config_fixture,
    make_driver_fixture,
    make_window_monitor_fixture,
    make_app_logs_fixture,
)

__all__ = [
    "make_app_config_fixture",
    "make_driver_fixture",
    "make_window_monitor_fixture",
    "make_app_logs_fixture",
]
