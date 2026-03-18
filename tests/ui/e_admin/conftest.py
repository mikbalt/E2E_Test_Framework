"""
tests/ui/e_admin/conftest.py -- E-Admin specific fixtures.

Provides:
- e_admin_config: session-scoped config extracted from settings.yaml
- e_admin_driver: function-scoped UIDriver that does NOT auto-close
- window_monitor: background monitor for unexpected windows
- collect_app_logs: auto-collects E-Admin AppLogs (PRE + POST snapshots) per test
- collect_remote_logs: auto-queries Loki for remote VM logs after each test
"""

import glob
import logging
import os
import shutil
import subprocess
import time

import pytest

from sphere_e2e_test_framework.testing.conftest_factory import (
    make_app_config_fixture,
    make_driver_fixture,
    make_window_monitor_fixture,
    make_app_logs_fixture,
)

logger = logging.getLogger(__name__)


# --- E-Admin-specific pre-launch hook ---

def _kill_lingering_app(app_config):
    """Kill any lingering eAdmin process to release file handles."""
    app_path = app_config.get("path", "")
    if not app_path:
        return
    exe_name = os.path.basename(app_path)
    result = subprocess.run(
        ["taskkill", "/f", "/im", exe_name],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        logger.info(f"Killed lingering process: {exe_name}")
        time.sleep(2)  # wait for file handles to be released


def _clear_compact_logs(app_config):
    """Clear compact logs to prevent 'Log File Signature Verification' popup.

    First kills any lingering app process to release file handles,
    then retries deletion up to 5 times with 1-second delays for
    any remaining WinError 32 (file locked).
    """
    _kill_lingering_app(app_config)

    compact_logs = app_config.get(
        "compact_logs_dir",
        r"C:\SPHERE_HSM\Admin Application\AppLogs\Compact",
    )
    if os.path.isdir(compact_logs):
        max_retries = 5
        for f in glob.glob(os.path.join(compact_logs, "*")):
            for attempt in range(max_retries):
                try:
                    os.remove(f) if os.path.isfile(f) else shutil.rmtree(f)
                    break  # success
                except PermissionError:
                    if attempt < max_retries - 1:
                        logger.debug(f"File locked, retrying in 1s ({attempt + 1}/{max_retries}): {f}")
                        time.sleep(1)
                    else:
                        logger.warning(f"Could not remove {f} after {max_retries} attempts (file locked)")
                except Exception as e:
                    logger.warning(f"Could not remove {f}: {e}")
                    break
        logger.info(f"Cleared compact logs: {compact_logs}")


# --- Factory-generated fixtures ---

e_admin_config = make_app_config_fixture("e_admin")
e_admin_driver = make_driver_fixture("e_admin", pre_launch_hook=_clear_compact_logs)
window_monitor = make_window_monitor_fixture("e_admin")
collect_app_logs = make_app_logs_fixture("e_admin")


# --- E-Admin-only: remote log collection ---

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
        from sphere_e2e_test_framework.driver.loki_collector import LokiLogCollector

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
