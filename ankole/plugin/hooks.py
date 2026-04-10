"""Pytest hooks for Ankole Framework plugin."""

import datetime
import logging
import os
import platform
import time

import pytest

from ankole.plugin.config import load_config
from ankole.plugin.kiwi_hooks import (
    _filter_by_kiwi_run,
    _push_to_kiwi,
)
from ankole.plugin.metrics import _push_metrics

logger = logging.getLogger(__name__)

IS_WINDOWS = platform.system() == "Windows"


# ===========================================================================
# CLI Options
# ===========================================================================

def pytest_addoption(parser):
    """Register CLI options for Ankole Framework features."""
    group = parser.getgroup("ankole", "Ankole Framework options")

    # Health Check
    group.addoption(
        "--skip-health-check",
        action="store_true",
        default=False,
        help="Skip pre-execution environment health checks.",
    )

    # Smoke Gate
    group.addoption(
        "--smoke-gate",
        action="store_true",
        default=False,
        help="Run smoke tests first; abort remaining tests if any smoke test fails.",
    )

    # Kiwi TCMS Bidirectional
    group.addoption(
        "--kiwi-run-id",
        type=int,
        default=None,
        help="Kiwi TCMS TestRun ID: pull test cases from this run, "
             "execute only matching tests, push results back.",
    )
    group.addoption(
        "--kiwi-plan-id",
        type=int,
        default=None,
        help="Override kiwi_tcms.plan_id from settings.yaml.",
    )
    group.addoption(
        "--kiwi-create-run",
        action="store_true",
        default=False,
        help="Force create a new Kiwi TCMS test run (explicit opt-in).",
    )

    # Metrics Run ID
    group.addoption(
        "--metrics-run-id",
        "--run-id",
        type=str,
        default=None,
        dest="metrics_run_id",
        help="Unique run ID for Grafana/Prometheus metrics isolation. "
             "Auto-generated if not provided. "
             "(Alias: --run-id for backward compatibility)",
    )


# ===========================================================================
# Pytest Hooks
# ===========================================================================

def pytest_configure(config):
    """Register custom markers, setup directories, init features."""
    # --- Markers ---
    config.addinivalue_line("markers", "web: Web UI automation tests (Playwright)")
    config.addinivalue_line("markers", "api: REST API tests (httpx)")
    config.addinivalue_line("markers", "cli: CLI tool tests (subprocess)")
    config.addinivalue_line("markers", "desktop: Windows desktop UI tests (pywinauto)")
    config.addinivalue_line("markers", "smoke: Quick smoke tests")
    config.addinivalue_line("markers", "regression: Full regression tests")
    config.addinivalue_line("markers", "critical: Critical path tests that must pass")
    config.addinivalue_line("markers", "slow: Tests that take longer than 30 seconds")
    config.addinivalue_line(
        "markers",
        "tcms(case_id): Map this test to a specific Kiwi TCMS TestCase ID",
    )
    config.addinivalue_line(
        "markers",
        "depends_on(*case_ids): Skip if dependency TCMS case did not pass",
    )
    config.addinivalue_line(
        "markers",
        "order(index): Execution order hint (pytest-ordering)",
    )

    # --- Evidence directories ---
    cfg = load_config()
    evidence_dir = cfg.get("evidence", {}).get("base_dir", "evidence")
    os.makedirs(evidence_dir, exist_ok=True)
    os.makedirs(os.path.join(evidence_dir, "allure-results"), exist_ok=True)
    os.makedirs(os.path.join(evidence_dir, "screenshots"), exist_ok=True)

    # --- Smoke Gate ---
    config._smoke_gate = None
    if config.getoption("--smoke-gate", default=False):
        from ankole.driver.smoke_gate import SmokeGate
        config._smoke_gate = SmokeGate()
        config._smoke_gate.activate()

    # --- Kiwi TCMS Bidirectional ---
    config._kiwi_reporter = None
    config._kiwi_run_cases = None
    kiwi_run_id = config.getoption("--kiwi-run-id", default=None)

    if kiwi_run_id:
        tcms_config = cfg.get("kiwi_tcms", {})
        plan_id_override = config.getoption("--kiwi-plan-id", default=None)

        from ankole.driver.kiwi_tcms import KiwiReporter
        reporter = KiwiReporter(
            url=tcms_config.get("url"),
            plan_id=plan_id_override or tcms_config.get("plan_id"),
            build_id=tcms_config.get("build_id"),
            status_ids=tcms_config.get("status_ids"),
        )
        if reporter.connect():
            if reporter.use_existing_run(kiwi_run_id):
                config._kiwi_reporter = reporter
                config._kiwi_run_cases = reporter.get_cases_from_run(kiwi_run_id)
                logger.info(
                    f"Kiwi bidirectional mode: "
                    f"{len(config._kiwi_run_cases)} cases from run #{kiwi_run_id}"
                )
            else:
                logger.warning(
                    f"Could not attach to Kiwi TestRun #{kiwi_run_id}, "
                    f"continuing without bidirectional filtering"
                )
        else:
            logger.warning(
                "Could not connect to Kiwi TCMS for bidirectional mode, "
                "continuing without filtering"
            )


def pytest_collection_modifyitems(config, items):
    """Auto-skip desktop tests on non-Windows. Reorder for smoke gate. Filter by Kiwi."""
    # --- Desktop skip on non-Windows ---
    if not IS_WINDOWS:
        skip_desktop = pytest.mark.skip(reason="Desktop tests require Windows (pywinauto)")
        for item in items:
            if "desktop" in item.keywords:
                item.add_marker(skip_desktop)

    # --- Kiwi bidirectional: filter to only TestRun cases ---
    kiwi_cases = getattr(config, "_kiwi_run_cases", None)
    if kiwi_cases:
        _filter_by_kiwi_run(config, items, kiwi_cases)

    # --- Smoke gate: reorder smoke tests first ---
    smoke_gate = getattr(config, "_smoke_gate", None)
    if smoke_gate and smoke_gate.active:
        from ankole.driver.smoke_gate import reorder_smoke_first
        reorder_smoke_first(items)


def pytest_sessionstart(session):
    """Called after session is created, before test collection."""
    session.start_time = time.time()
    session.results = []

    # Generate or use provided run_id for metrics isolation
    run_id = session.config.getoption("metrics_run_id", default=None)
    if not run_id:
        run_id = datetime.datetime.now().strftime("run_%Y%m%d_%H%M%S")
    session.config._run_id = run_id

    logger.info("=" * 60)
    logger.info("Ankole Framework - Session Started")
    logger.info(f"Run ID: {run_id}")
    # Detect Windows 11 (build >= 22000, still reports as NT 10.0)
    os_name = platform.system()
    os_ver = platform.release()
    if os_name == "Windows" and os_ver == "10":
        try:
            build = int(platform.version().split(".")[-1])
            if build >= 22000:
                os_ver = "11"
        except (ValueError, IndexError):
            pass
    logger.info(f"Platform: {os_name} {os_ver}")
    logger.info(f"Timestamp: {datetime.datetime.now().isoformat()}")
    logger.info("=" * 60)

    # --- Health Check ---
    if not session.config.getoption("--skip-health-check", default=False):
        cfg = load_config()
        health_cfg = cfg.get("health_check", {})
        if health_cfg.get("enabled", False):
            from ankole.driver.health_check import HealthChecker
            checker = HealthChecker(health_cfg)
            report = checker.run_all()
            logger.info(report.summary())
            if not report.all_passed:
                pytest.exit(report.summary(), returncode=1)


def pytest_runtest_setup(item):
    """Skip non-smoke tests if smoke gate has failed."""
    smoke_gate = getattr(item.config, "_smoke_gate", None)
    if smoke_gate and smoke_gate.gate_failed:
        from ankole.driver.smoke_gate import is_smoke_test
        if not is_smoke_test(item):
            pytest.skip("Smoke gate failed: aborting remaining tests")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Track results, capture screenshot on failure, enforce smoke gate."""
    outcome = yield
    report = outcome.get_result()

    # Record result on "call" phase, or on "setup"/"teardown" if they failed.
    is_call = report.when == "call"
    is_fixture_failure = report.when in ("setup", "teardown") and report.failed

    if is_call or is_fixture_failure:
        if not hasattr(item.session, "results"):
            item.session.results = []

        already_recorded = any(
            r["nodeid"] == item.nodeid for r in item.session.results
        )
        if already_recorded:
            pass
        else:
            if is_fixture_failure:
                phase = "setup" if report.when == "setup" else "teardown"
                status = "FAILED"
                error_msg = str(call.excinfo.value) if call.excinfo else f"Fixture {phase} failed"
            else:
                status = "PASSED" if report.passed else "FAILED"
                error_msg = str(call.excinfo.value) if report.failed and call.excinfo else ""

            result = {
                "name": item.name,
                "nodeid": item.nodeid,
                "status": status,
                "duration": call.duration,
                "evidence_dir": None,
            }
            if error_msg:
                result["error"] = error_msg

            if hasattr(item, "funcargs") and "evidence" in item.funcargs:
                result["evidence_dir"] = item.funcargs["evidence"].evidence_dir
            elif hasattr(item, "instance") and hasattr(getattr(item, "instance", None), "evidence"):
                ev = item.instance.evidence
                if hasattr(ev, "evidence_dir"):
                    result["evidence_dir"] = ev.evidence_dir

            if hasattr(item, "_kiwi_case"):
                result["_kiwi_case_id"] = item._kiwi_case.get("id")

            item.session.results.append(result)

            if is_fixture_failure:
                logger.warning(
                    f"Fixture {phase} failure recorded for {item.nodeid}: "
                    f"{error_msg[:200]}"
                )

        # Smoke gate tracking
        smoke_gate = getattr(item.config, "_smoke_gate", None)
        if smoke_gate and smoke_gate.active:
            from ankole.driver.smoke_gate import is_smoke_test
            if is_smoke_test(item):
                smoke_gate.record_smoke_result(item.nodeid, report.passed)

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

    # Smoke gate summary
    smoke_gate = getattr(session.config, "_smoke_gate", None)
    if smoke_gate and smoke_gate.gate_failed:
        logger.warning(smoke_gate.summary())

    cfg = load_config()

    # Handle --kiwi-create-run explicitly
    if session.config.getoption("--kiwi-create-run", default=False):
        cfg.setdefault("kiwi_tcms", {})["auto_create_run"] = True
        cfg.setdefault("kiwi_tcms", {})["enabled"] = True

    # Handle --kiwi-plan-id override
    plan_id_override = session.config.getoption("--kiwi-plan-id", default=None)
    if plan_id_override:
        cfg.setdefault("kiwi_tcms", {})["plan_id"] = plan_id_override

    _push_to_kiwi(results, cfg, config=session.config)
    _push_metrics(results, duration, cfg, config=session.config)
