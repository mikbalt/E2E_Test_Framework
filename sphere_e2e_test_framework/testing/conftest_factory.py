"""Fixture factories for per-app conftest files.

Each factory returns a pytest fixture function ready to be assigned
at module level in a conftest.py::

    from sphere_e2e_test_framework.testing.conftest_factory import (
        make_app_config_fixture, make_driver_fixture,
        make_window_monitor_fixture, make_app_logs_fixture,
    )

    cps_config = make_app_config_fixture("cps")
    cps_driver = make_driver_fixture("cps")
    window_monitor = make_window_monitor_fixture("cps")
    collect_app_logs = make_app_logs_fixture("cps")
"""

import logging
import os

import pytest

from sphere_e2e_test_framework.testing.conftest_utils import (
    get_tc_label,
    zip_app_logs,
    attach_zip_to_allure,
)

logger = logging.getLogger(__name__)


def make_app_config_fixture(app_name):
    """Create a session-scoped fixture that extracts app config from settings.yaml."""

    @pytest.fixture(scope="session")
    def app_config(config):
        return config.get("apps", {}).get(app_name, {})

    app_config.__doc__ = f"Extract {app_name} app config once per session."
    return app_config


def make_driver_fixture(app_name, pre_launch_hook=None, driver_class=None):
    """Create a function-scoped driver fixture for the given app.

    Args:
        app_name: Key in settings.yaml ``apps`` section.
        pre_launch_hook: Optional callable(app_config) run before driver.start().
        driver_class: Driver class to instantiate. If ``None`` (default),
            lazily imports and uses ``UIDriver``.
    """

    @pytest.fixture
    def app_driver(request):
        cls = driver_class
        if cls is None:
            from sphere_e2e_test_framework.driver.ui_driver import UIDriver
            cls = UIDriver

        app_config = request.getfixturevalue(f"{app_name}_config")

        if pre_launch_hook:
            pre_launch_hook(app_config)

        driver = cls(
            app_path=app_config.get("path"),
            class_name=app_config.get("class_name"),
            backend=app_config.get("backend", "uia"),
            startup_wait=app_config.get("startup_wait", 5),
            popup_dismiss_buttons=app_config.get("popup_dismiss_buttons"),
            popup_dismiss_auto_ids=app_config.get("popup_dismiss_auto_ids"),
        )
        driver.start()
        driver.dismiss_startup_popups()

        retry_cfg = app_config.get("retry", {})
        if retry_cfg:
            driver.set_retry_config(retry_cfg)

        yield driver
        driver.close()
        logger.info(f"{app_name}_driver fixture finalized - app closed")

    app_driver.__doc__ = f"Driver for {app_name} application."
    return app_driver


def make_window_monitor_fixture(app_name):
    """Create an autouse fixture that monitors for unexpected windows."""

    @pytest.fixture(autouse=True)
    def window_monitor(request, evidence):
        app_config = request.getfixturevalue(f"{app_name}_config")
        app_driver = request.getfixturevalue(f"{app_name}_driver")

        monitor_cfg = app_config.get("window_monitor", {})
        if not monitor_cfg.get("enabled", True):
            yield None
            return

        from sphere_e2e_test_framework.driver.window_monitor import WindowMonitor

        pid = app_driver.app.process
        monitor = WindowMonitor(app_pid=pid, evidence=evidence)
        monitor.snapshot_baseline()
        monitor.add_whitelist(app_driver._main_handle)
        app_driver.set_window_monitor(monitor)

        interval = monitor_cfg.get("interval", 1.0)
        monitor.start(interval=interval)
        yield monitor

        detected = monitor.stop()
        app_driver.set_window_monitor(None)
        if detected:
            logger.warning(
                f"Test '{request.node.name}' finished with "
                f"{len(detected)} unexpected window(s) detected"
            )

    window_monitor.__doc__ = f"Background monitor for unexpected windows ({app_name})."
    return window_monitor


def make_app_logs_fixture(app_name):
    """Create an autouse fixture that collects app logs PRE + POST each test."""

    @pytest.fixture(autouse=True)
    def collect_app_logs(request, evidence):
        app_config = request.getfixturevalue(f"{app_name}_config")
        # Ensure the driver is started (implicit dependency)
        request.getfixturevalue(f"{app_name}_driver")

        app_logs_dir = app_config.get("app_logs_dir", "")
        tc_label = get_tc_label(request)

        # PRE-snapshot
        if app_logs_dir and os.path.isdir(app_logs_dir):
            pre_zip, pre_count = zip_app_logs(
                app_logs_dir, evidence.evidence_dir, f"{tc_label}_PRE",
            )
            if pre_zip:
                attach_zip_to_allure(pre_zip, f"AppLogs {tc_label} PRE")
                logger.info(
                    f"Pre-test log snapshot: {pre_count} files -> "
                    f"{os.path.basename(pre_zip)}"
                )
        else:
            logger.warning(
                f"App logs dir not available for '{request.node.name}' - "
                f"check {app_name.upper()}_APP_LOGS (got: '{app_logs_dir}')"
            )

        yield

        # POST-snapshot
        if not app_logs_dir or not os.path.isdir(app_logs_dir):
            logger.warning(
                f"App logs dir disappeared after test '{request.node.name}' - "
                f"directory may have been wiped by test operations"
            )
            return

        try:
            post_zip, post_count = zip_app_logs(
                app_logs_dir, evidence.evidence_dir, f"{tc_label}_POST",
            )
            if post_zip:
                attach_zip_to_allure(post_zip, f"AppLogs {tc_label} POST")
                logger.info(
                    f"Post-test log snapshot: {post_count} files -> "
                    f"{os.path.basename(post_zip)}"
                )
            else:
                logger.warning(
                    f"App logs empty after '{request.node.name}' - "
                    f"pre-test snapshot was preserved as evidence."
                )
        except Exception as e:
            logger.warning(f"Failed to collect post-test app logs: {e}")

    collect_app_logs.__doc__ = f"Auto-collect {app_name} AppLogs (PRE + POST) per test."
    return collect_app_logs
