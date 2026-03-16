"""
tests/ui/e_admin/conftest.py -- E-Admin specific fixtures.

Provides:
- e_admin_config: session-scoped config extracted from settings.yaml
- e_admin_driver: function-scoped UIDriver that does NOT auto-close
- collect_app_logs: auto-collects E-Admin AppLogs into a zip after each test
- collect_remote_logs: auto-queries Loki for remote VM logs after each test
"""

import datetime
import logging
import os
import time
import zipfile

import pytest

logger = logging.getLogger(__name__)

# Track passed TCMS case IDs across the session for dependency checking
_passed_cases = set()
# TCMS case IDs present in the current collection (populated by pytest_collection_modifyitems)
_collected_cases = set()


@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(items):
    """Record which TCMS case IDs are in the current test collection.

    trylast=True ensures this runs AFTER the plugin's Kiwi filter,
    so _collected_cases only contains cases that survived filtering.
    """
    for item in items:
        marker = item.get_closest_marker("tcms")
        if marker:
            case_id = marker.kwargs.get("case_id")
            if case_id:
                _collected_cases.add(case_id)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Record passed TCMS case IDs for dependency checking."""
    outcome = yield
    report = outcome.get_result()
    if report.when == "call" and report.passed:
        marker = item.get_closest_marker("tcms")
        if marker:
            case_id = marker.kwargs.get("case_id")
            if case_id:
                _passed_cases.add(case_id)


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


@pytest.fixture(scope="session")
def e_admin_config(config):
    """Extract e-admin app config once per session."""
    return config.get("apps", {}).get("e_admin", {})


@pytest.fixture
def e_admin_driver(e_admin_config):
    """
    UIDriver for E-Admin that does NOT auto-close the app.

    E-Admin tests require the app to remain open between tests
    for inspection. Only evidence is finalized; the app stays running.
    """
    from hsm_test_framework.ui_driver import UIDriver

    # Clear compact logs to prevent "Log File Signature Verification" popup
    import glob
    import shutil
    compact_logs = e_admin_config.get(
        "compact_logs_dir",
        r"C:\SPHERE_HSM\Admin Application\AppLogs\Compact",
    )
    if os.path.isdir(compact_logs):
        for f in glob.glob(os.path.join(compact_logs, "*")):
            try:
                os.remove(f) if os.path.isfile(f) else shutil.rmtree(f)
            except Exception as e:
                logger.warning(f"Could not remove {f}: {e}")
        logger.info(f"Cleared compact logs: {compact_logs}")

    driver = UIDriver(
        app_path=e_admin_config.get("path"),
        class_name=e_admin_config.get("class_name"),
        backend=e_admin_config.get("backend", "uia"),
        startup_wait=e_admin_config.get("startup_wait", 5),
        popup_dismiss_buttons=e_admin_config.get("popup_dismiss_buttons"),
        popup_dismiss_auto_ids=e_admin_config.get("popup_dismiss_auto_ids"),
    )
    driver.start()

    retry_cfg = e_admin_config.get("retry", {})
    if retry_cfg:
        driver.set_retry_config(retry_cfg)

    yield driver
    driver.close()
    logger.info("e_admin_driver fixture finalized - app closed")


@pytest.fixture(autouse=True)
def window_monitor(request, e_admin_config, e_admin_driver, evidence):
    """Background monitor for unexpected windows during test."""
    monitor_cfg = e_admin_config.get("window_monitor", {})
    if not monitor_cfg.get("enabled", True):
        yield None
        return

    from hsm_test_framework.window_monitor import WindowMonitor

    pid = e_admin_driver.app.process
    monitor = WindowMonitor(app_pid=pid, evidence=evidence)
    monitor.snapshot_baseline()
    monitor.add_whitelist(e_admin_driver._main_handle)
    e_admin_driver.set_window_monitor(monitor)

    interval = monitor_cfg.get("interval", 1.0)
    monitor.start(interval=interval)
    yield monitor

    detected = monitor.stop()
    e_admin_driver.set_window_monitor(None)
    if detected:
        logger.warning(
            f"Test '{request.node.name}' finished with "
            f"{len(detected)} unexpected window(s) detected"
        )


@pytest.fixture(autouse=True)
def collect_app_logs(request, e_admin_config, evidence):
    """Auto-collect E-Admin AppLogs into a zip after each test (pass or fail).

    The zip is saved in the test's evidence directory and attached to Allure.
    Configure the logs path via E_ADMIN_APP_LOGS env var or
    apps.e_admin.app_logs_dir in settings.yaml.
    """
    yield

    app_logs_dir = e_admin_config.get("app_logs_dir", "")
    if not app_logs_dir or not os.path.isdir(app_logs_dir):
        logger.debug(f"App logs dir not found or not configured: {app_logs_dir}")
        return

    try:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_name = f"AppLogs_{request.node.name}_{timestamp}.zip"
        zip_path = os.path.join(evidence.evidence_dir, zip_name)

        file_count = 0
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, _dirs, files in os.walk(app_logs_dir):
                for fname in files:
                    full_path = os.path.join(root, fname)
                    arcname = os.path.relpath(full_path, app_logs_dir)
                    zf.write(full_path, arcname)
                    file_count += 1

        if file_count == 0:
            os.remove(zip_path)
            logger.info("App logs dir is empty, skipped zip")
            return

        logger.info(f"Collected {file_count} app log files -> {zip_path}")

        # Attach to Allure
        try:
            import allure
            with open(zip_path, "rb") as f:
                allure.attach(
                    f.read(),
                    name=zip_name,
                    attachment_type="application/zip",
                    extension="zip",
                )
        except ImportError:
            pass

    except Exception as e:
        logger.warning(f"Failed to collect app logs: {e}")


@pytest.fixture(autouse=True)
def collect_remote_logs(request, config, evidence):
    """Auto-query Loki for remote VM logs after each test (pass or fail).

    Collects logs from all configured Loki queries for the duration of the
    test. The results are zipped and attached to the Allure report.
    Configure via remote_logs section in settings.yaml and LOKI_URL in .env.
    """
    remote_cfg = config.get("remote_logs", {})
    if not remote_cfg.get("enabled", False):
        yield
        return

    # Record test start time with buffer for clock skew between VMs
    buffer_sec = remote_cfg.get("time_buffer", 60)
    test_start = time.time() - buffer_sec
    yield
    test_end = time.time() + buffer_sec

    try:
        from hsm_test_framework.loki_collector import LokiLogCollector

        collector = LokiLogCollector(
            loki_url=remote_cfg.get("loki_url", ""),
            queries=remote_cfg.get("queries", []),
            default_limit=remote_cfg.get("default_limit", 5000),
            timeout=remote_cfg.get("timeout", 30),
        )
        collector.collect(
            start_time=test_start,
            end_time=test_end,
            evidence=evidence,
            test_name=request.node.name,
        )
    except Exception as e:
        logger.warning(f"Failed to collect remote logs: {e}")
