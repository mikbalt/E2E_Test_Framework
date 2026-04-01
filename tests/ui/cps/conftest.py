"""
tests/ui/cps/conftest.py -- CPS-specific fixtures.

Provides:
- e_admin_config / e_admin_driver: E-Admin app (for HSM init)
- testhsm_config / testhsm_driver: TestHSM app (for CPS tests)
- app_drivers: dynamic multi-app fixture via @pytest.mark.apps("app1", "app2")
"""

import logging
import time

import pytest

from sphere_e2e_test_framework.testing.conftest_factory import (
    make_app_config_fixture,
    make_driver_fixture,
)
from sphere_e2e_test_framework.driver.appmanager import UIAppManager

logger = logging.getLogger(__name__)

# --- Factory-generated fixtures (for single-app tests) ---
e_admin_config = make_app_config_fixture("e_admin")
e_admin_driver = make_driver_fixture("e_admin")
testhsm_config = make_app_config_fixture("testhsm")
testhsm_driver = make_driver_fixture("testhsm")


# --- Multi-app fixture (for @pytest.mark.apps tests) ---

@pytest.fixture
def app_drivers(request, config, evidence):
    """Start UI drivers dynamically based on @pytest.mark.apps marker.

    Usage::

        @pytest.mark.apps("e_admin", "testhsm")
        def test_flow(app_drivers):
            e_admin = app_drivers["e_admin"]
            testhsm = app_drivers["testhsm"]
    """
    marker = request.node.get_closest_marker("apps")
    if not marker:
        raise RuntimeError(
            "Test must define apps using @pytest.mark.apps('app1', 'app2')"
        )

    apps = marker.args
    managers = {}
    drivers = {}
    monitors = {}

    buffer_sec = config.get("remote_logs", {}).get("time_buffer", 60)
    test_start = time.time() - buffer_sec

    for app_name in apps:
        manager = UIAppManager(app_name, config)
        driver = manager.create_driver()
        monitor = manager.setup_window_monitor(driver, evidence)
        managers[app_name] = manager
        drivers[app_name] = driver
        monitors[app_name] = monitor

    yield drivers

    test_end = time.time() + buffer_sec
    for app_name in drivers:
        manager = managers[app_name]
        manager.stop_window_monitor(drivers[app_name], monitors[app_name])
        manager.collect_app_logs(evidence, request.node.name)
        manager.collect_remote_logs(
            test_start, test_end, evidence, request.node.name,
        )
