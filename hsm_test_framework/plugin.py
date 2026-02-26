"""
HSM Test Framework - pytest plugin (auto-registered).

When a consumer repo installs hsm-test-framework, this plugin is automatically
loaded by pytest via the entry point. It provides:

- Platform detection (auto-skip UI tests on Linux)
- Screenshot on failure
- Kiwi TCMS result reporting
- Grafana/Prometheus metrics push
- Shared fixtures: evidence, console, ui_app, config

Consumer repos only need a minimal conftest.py:

    # conftest.py
    from hsm_test_framework.plugin import *  # noqa: re-export fixtures

Or rely on auto-registration (pytest11 entry point).
"""

import datetime
import logging
import os
import platform
import time

import pytest
import yaml
from dotenv import load_dotenv

# Load .env file from project root (auto-loads TCMS credentials etc.)
load_dotenv()

logger = logging.getLogger(__name__)

IS_WINDOWS = platform.system() == "Windows"

# ===========================================================================
# Configuration
# ===========================================================================

_CONFIG_CACHE = None


def load_config(config_path=None):
    """
    Load settings.yaml from the consumer repo.
    Searches: config/settings.yaml (relative to cwd), then env HSM_CONFIG_PATH.
    """
    global _CONFIG_CACHE
    if _CONFIG_CACHE is not None:
        return _CONFIG_CACHE

    search_paths = [
        config_path,
        os.environ.get("HSM_CONFIG_PATH"),
        os.path.join(os.getcwd(), "config", "settings.yaml"),
        os.path.join(os.getcwd(), "settings.yaml"),
    ]

    for path in search_paths:
        if path and os.path.exists(path):
            with open(path, "r") as f:
                _CONFIG_CACHE = yaml.safe_load(f) or {}
                logger.info(f"Config loaded from: {path}")
                return _CONFIG_CACHE

    logger.warning("No settings.yaml found, using defaults")
    _CONFIG_CACHE = {}
    return _CONFIG_CACHE


# ===========================================================================
# Pytest Hooks
# ===========================================================================

def pytest_configure(config):
    """Register custom markers and setup evidence directory."""
    config.addinivalue_line("markers", "ui: Windows UI automation tests")
    config.addinivalue_line("markers", "console: Console/CLI based tests")
    config.addinivalue_line("markers", "pkcs11: PKCS#11 related tests")
    config.addinivalue_line("markers", "smoke: Quick smoke tests")
    config.addinivalue_line("markers", "regression: Full regression tests")
    config.addinivalue_line("markers", "critical: Critical path tests that must pass")
    config.addinivalue_line("markers", "e_admin: E-Admin application specific tests")
    config.addinivalue_line("markers", "slow: Tests that take longer than 30 seconds")

    cfg = load_config()
    evidence_dir = cfg.get("evidence", {}).get("base_dir", "evidence")
    os.makedirs(evidence_dir, exist_ok=True)
    os.makedirs(os.path.join(evidence_dir, "allure-results"), exist_ok=True)
    os.makedirs(os.path.join(evidence_dir, "screenshots"), exist_ok=True)


def pytest_collection_modifyitems(config, items):
    """Auto-skip UI tests on non-Windows platforms."""
    if IS_WINDOWS:
        return

    skip_ui = pytest.mark.skip(reason="UI tests require Windows (pywinauto)")
    for item in items:
        if "ui" in item.keywords:
            item.add_marker(skip_ui)


def pytest_sessionstart(session):
    """Called after session is created, before test collection."""
    session.start_time = time.time()
    session.results = []
    logger.info("=" * 60)
    logger.info("HSM Test Framework - Session Started")
    logger.info(f"Platform: {platform.system()} {platform.release()}")
    logger.info(f"Timestamp: {datetime.datetime.now().isoformat()}")
    logger.info("=" * 60)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Track results and capture screenshot on failure."""
    outcome = yield
    report = outcome.get_result()

    if report.when == "call":
        result = {
            "name": item.name,
            "nodeid": item.nodeid,
            "status": "PASSED" if report.passed else "FAILED",
            "duration": call.duration,
            "evidence_dir": None,
        }
        if report.failed and call.excinfo:
            result["error"] = str(call.excinfo.value)

        # Extract evidence_dir: fixture-based or instance-based
        if hasattr(item, "funcargs") and "evidence" in item.funcargs:
            result["evidence_dir"] = item.funcargs["evidence"].evidence_dir
        elif hasattr(item, "instance") and hasattr(getattr(item, "instance", None), "evidence"):
            ev = item.instance.evidence
            if hasattr(ev, "evidence_dir"):
                result["evidence_dir"] = ev.evidence_dir

        if not hasattr(item.session, "results"):
            item.session.results = []
        item.session.results.append(result)

        cfg = load_config()
        if report.failed and cfg.get("evidence", {}).get("screenshot_on_failure", True):
            _capture_failure_screenshot(item, cfg)


def _capture_failure_screenshot(item, cfg):
    """Capture desktop screenshot when a test fails."""
    if not IS_WINDOWS and not os.environ.get("DISPLAY"):
        return

    try:
        import mss
        from PIL import Image

        evidence_dir = cfg.get("evidence", {}).get("base_dir", "evidence")
        screenshots_dir = os.path.join(evidence_dir, "screenshots")
        os.makedirs(screenshots_dir, exist_ok=True)

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"FAIL_{item.name}_{timestamp}.png"
        filepath = os.path.join(screenshots_dir, filename)

        with mss.mss() as sct:
            monitor = sct.monitors[0]
            screenshot = sct.grab(monitor)
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            img.save(filepath)

        logger.info(f"Failure screenshot saved: {filepath}")

        try:
            import allure
            with open(filepath, "rb") as f:
                allure.attach(
                    f.read(),
                    name=f"FAILURE_{item.name}",
                    attachment_type=allure.attachment_type.PNG,
                )
        except ImportError:
            pass
    except Exception as e:
        logger.warning(f"Could not capture failure screenshot: {e}")


def pytest_sessionfinish(session, exitstatus):
    """Push results to Kiwi TCMS and Grafana after session ends."""
    duration = time.time() - getattr(session, "start_time", time.time())
    results = getattr(session, "results", [])
    total = len(results)
    passed = sum(1 for r in results if r["status"] == "PASSED")
    failed = total - passed

    logger.info("=" * 60)
    logger.info(f"Session Complete: {total} tests | {passed} passed | {failed} failed")
    logger.info(f"Duration: {duration:.1f}s")
    logger.info("=" * 60)

    cfg = load_config()
    _push_to_kiwi(results, cfg)
    _push_metrics(results, duration, cfg)


def _push_to_kiwi(results, cfg):
    """Push results to Kiwi TCMS if enabled."""
    tcms_config = cfg.get("kiwi_tcms", {})
    if not tcms_config.get("enabled"):
        return

    try:
        from hsm_test_framework.kiwi_tcms import KiwiReporter

        reporter = KiwiReporter(
            url=tcms_config.get("url"),
            product=tcms_config.get("product"),
            plan_id=tcms_config.get("plan_id"),
            build_id=tcms_config.get("build_id"),
        )

        if not reporter.connect():
            return

        if tcms_config.get("auto_create_run"):
            reporter.create_test_run()

        for result in results:
            reporter.report_result(
                test_name=result["name"],
                status=result["status"],
                comment=result.get("error", ""),
                duration=result.get("duration", 0),
                evidence_dir=result.get("evidence_dir"),
            )

        reporter.finalize()
    except Exception as e:
        logger.warning(f"Kiwi TCMS reporting failed: {e}")


def _push_metrics(results, session_duration, cfg):
    """Push metrics to Prometheus/Grafana if enabled."""
    metrics_config = cfg.get("metrics", {})
    if not metrics_config.get("enabled"):
        return

    try:
        from hsm_test_framework.grafana_push import MetricsPusher

        pusher = MetricsPusher(
            pushgateway_url=metrics_config.get("pushgateway_url"),
            job_name=metrics_config.get("job_name", "hsm_tests"),
            labels=metrics_config.get("labels", {}),
        )

        total = len(results)
        passed = sum(1 for r in results if r["status"] == "PASSED")

        for result in results:
            pusher.record_test(
                test_name=result["name"],
                passed=(result["status"] == "PASSED"),
                duration=result.get("duration", 0),
            )

        pusher.record_suite("hsm", total, passed, session_duration)
        pusher.push()
    except Exception as e:
        logger.warning(f"Metrics push failed: {e}")


# ===========================================================================
# Fixtures (available to all consumer repos automatically)
# ===========================================================================

@pytest.fixture(scope="session")
def config():
    """Provide test configuration from settings.yaml."""
    return load_config()


@pytest.fixture
def evidence(request):
    """Provide Evidence collector for the current test."""
    from hsm_test_framework.evidence import Evidence

    cfg = load_config()
    ev = Evidence(
        test_name=request.node.name,
        base_dir=cfg.get("evidence", {}).get("base_dir", "evidence"),
    )
    yield ev
    ev.finalize()


@pytest.fixture
def console():
    """Provide ConsoleRunner instance."""
    from hsm_test_framework.console_runner import ConsoleRunner
    return ConsoleRunner()


@pytest.fixture
def log_collector(evidence):
    """Provide LogCollector instance linked to current test's evidence."""
    from hsm_test_framework.log_collector import LogCollector
    return LogCollector(evidence=evidence)


@pytest.fixture
def ui_app(request):
    """
    Generic UI app fixture. Auto-skips on non-Windows.

    Usage:
        @pytest.mark.parametrize("ui_app", ["calculator"], indirect=True)
        def test_calc(ui_app):
            ui_app.click_button("Seven")
    """
    if not IS_WINDOWS:
        pytest.skip("UI tests require Windows")

    from hsm_test_framework.ui_driver import UIDriver

    cfg = load_config()
    app_name = getattr(request, "param", "calculator")
    app_config = cfg.get("apps", {}).get(app_name, {})

    driver = UIDriver(
        app_path=app_config.get("path", "calc.exe"),
        title=app_config.get("title"),
        backend=app_config.get("backend", "uia"),
        startup_wait=app_config.get("startup_wait", 3),
    )
    driver.start()
    yield driver
    driver.close()
