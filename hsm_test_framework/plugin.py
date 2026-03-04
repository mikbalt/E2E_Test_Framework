"""
HSM Test Framework - pytest plugin (auto-registered).

When a consumer repo installs hsm-test-framework, this plugin is automatically
loaded by pytest via the entry point. It provides:

- Platform detection (auto-skip UI tests on Linux)
- Pre-execution health checks (--skip-health-check to bypass)
- Smoke gate / fail-fast (--smoke-gate)
- Kiwi TCMS bidirectional integration (--kiwi-run-id)
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
import re
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
    After loading, applies environment variable overrides (see _apply_env_overrides).
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
                _CONFIG_CACHE = _resolve_placeholders(_CONFIG_CACHE)
                _apply_env_overrides(_CONFIG_CACHE)
                return _CONFIG_CACHE

    logger.warning("No settings.yaml found, using defaults")
    _CONFIG_CACHE = {}
    _apply_env_overrides(_CONFIG_CACHE)
    return _CONFIG_CACHE


_PLACEHOLDER_RE = re.compile(r"\$\{([^}]+)\}")


def _resolve_placeholders(obj):
    """
    Walk a nested dict/list and replace all '${VAR}' placeholder strings
    with the corresponding environment variable value (empty string if unset).

    This ensures no literal '${...}' strings survive in the config dict,
    regardless of whether _apply_env_overrides handles that specific key.
    """
    if isinstance(obj, dict):
        return {k: _resolve_placeholders(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_resolve_placeholders(item) for item in obj]
    if isinstance(obj, str) and "${" in obj:
        return _PLACEHOLDER_RE.sub(
            lambda m: os.environ.get(m.group(1), ""), obj
        )
    return obj


def _apply_env_overrides(cfg):
    """
    Replace ${VAR} placeholders and apply environment variable overrides.

    settings.yaml uses ${VAR} placeholders for environment-specific values.
    Actual values are set in .env (loaded via dotenv at startup).

    Supported env vars:
        HSM_IP           → apps.e_admin.connection.ip + health_check.checks[].host
        HSM_PORT         → apps.e_admin.connection.port + health_check tcp check port
        E_ADMIN_PATH     → apps.e_admin.path
        PUSHGATEWAY_URL  → metrics.pushgateway_url
        TCMS_API_URL     → kiwi_tcms.url
        KIWI_PLAN_ID     → kiwi_tcms.plan_id  (only for --kiwi-create-run)
        KIWI_BUILD_ID    → kiwi_tcms.build_id (only for --kiwi-create-run)
    """
    hsm_ip = os.environ.get("HSM_IP", "").strip()
    hsm_port = os.environ.get("HSM_PORT", "").strip()
    e_admin_path = os.environ.get("E_ADMIN_PATH", "").strip()
    pushgateway_url = os.environ.get("PUSHGATEWAY_URL", "").strip()
    tcms_api_url = os.environ.get("TCMS_API_URL", "").strip()
    kiwi_plan_id = os.environ.get("KIWI_PLAN_ID", "").strip()
    kiwi_build_id = os.environ.get("KIWI_BUILD_ID", "").strip()

    # --- E-Admin connection ---
    e_admin = cfg.setdefault("apps", {}).setdefault("e_admin", {})
    conn = e_admin.setdefault("connection", {})
    if hsm_ip:
        conn["ip"] = hsm_ip
    if hsm_port:
        conn["port"] = hsm_port
    if e_admin_path:
        e_admin["path"] = e_admin_path
    e_admin_app_logs = os.environ.get("E_ADMIN_APP_LOGS", "").strip()
    if e_admin_app_logs:
        e_admin["app_logs_dir"] = e_admin_app_logs

    # --- Health check hosts/ports ---
    checks = cfg.get("health_check", {}).get("checks", [])
    for check in checks:
        if hsm_ip:
            check["host"] = hsm_ip
        if hsm_port and check.get("type") == "tcp":
            check["port"] = int(hsm_port)

    # --- Pushgateway ---
    if pushgateway_url:
        cfg.setdefault("metrics", {})["pushgateway_url"] = pushgateway_url

    # --- Kiwi TCMS ---
    kiwi = cfg.setdefault("kiwi_tcms", {})
    if tcms_api_url:
        kiwi["url"] = tcms_api_url
    if kiwi_plan_id:
        kiwi["plan_id"] = int(kiwi_plan_id)
    if kiwi_build_id:
        kiwi["build_id"] = int(kiwi_build_id)


# ===========================================================================
# CLI Options
# ===========================================================================

def pytest_addoption(parser):
    """Register CLI options for HSM Test Framework features."""
    group = parser.getgroup("hsm", "HSM Test Framework options")

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
        "--run-id",
        type=str,
        default=None,
        help="Unique run ID for metrics isolation. Auto-generated if not provided.",
    )


# ===========================================================================
# Pytest Hooks
# ===========================================================================

def pytest_configure(config):
    """Register custom markers, setup directories, init features."""
    # --- Markers ---
    config.addinivalue_line("markers", "ui: Windows UI automation tests")
    config.addinivalue_line("markers", "console: Console/CLI based tests")
    config.addinivalue_line("markers", "pkcs11: PKCS#11 related tests")
    config.addinivalue_line("markers", "smoke: Quick smoke tests")
    config.addinivalue_line("markers", "regression: Full regression tests")
    config.addinivalue_line("markers", "critical: Critical path tests that must pass")
    config.addinivalue_line("markers", "e_admin: E-Admin application specific tests")
    config.addinivalue_line("markers", "slow: Tests that take longer than 30 seconds")
    config.addinivalue_line(
        "markers",
        "tcms(case_id): Map this test to a specific Kiwi TCMS TestCase ID",
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
        from hsm_test_framework.smoke_gate import SmokeGate
        config._smoke_gate = SmokeGate()
        config._smoke_gate.activate()

    # --- Kiwi TCMS Bidirectional ---
    config._kiwi_reporter = None
    config._kiwi_run_cases = None
    kiwi_run_id = config.getoption("--kiwi-run-id", default=None)

    if kiwi_run_id:
        tcms_config = cfg.get("kiwi_tcms", {})
        plan_id_override = config.getoption("--kiwi-plan-id", default=None)

        from hsm_test_framework.kiwi_tcms import KiwiReporter
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
    """Auto-skip UI tests on non-Windows. Reorder for smoke gate. Filter by Kiwi."""
    # --- UI skip on non-Windows ---
    if not IS_WINDOWS:
        skip_ui = pytest.mark.skip(reason="UI tests require Windows (pywinauto)")
        for item in items:
            if "ui" in item.keywords:
                item.add_marker(skip_ui)

    # --- Kiwi bidirectional: filter to only TestRun cases ---
    kiwi_cases = getattr(config, "_kiwi_run_cases", None)
    if kiwi_cases:
        _filter_by_kiwi_run(config, items, kiwi_cases)

    # --- Smoke gate: reorder smoke tests first ---
    smoke_gate = getattr(config, "_smoke_gate", None)
    if smoke_gate and smoke_gate.active:
        from hsm_test_framework.smoke_gate import reorder_smoke_first
        reorder_smoke_first(items)


def pytest_sessionstart(session):
    """Called after session is created, before test collection."""
    session.start_time = time.time()
    session.results = []

    # Generate or use provided run_id for metrics isolation
    run_id = session.config.getoption("--run-id", default=None)
    if not run_id:
        run_id = datetime.datetime.now().strftime("run_%Y%m%d_%H%M%S")
    session.config._run_id = run_id

    logger.info("=" * 60)
    logger.info("HSM Test Framework - Session Started")
    logger.info(f"Run ID: {run_id}")
    # Detect Windows 11 (build >= 22000, still reports as NT 10.0)
    os_name = platform.system()
    os_ver = platform.release()
    if os_name == "Windows" and os_ver == "10":
        build = int(platform.version().split(".")[-1])
        if build >= 22000:
            os_ver = "11"
    logger.info(f"Platform: {os_name} {os_ver}")
    logger.info(f"Timestamp: {datetime.datetime.now().isoformat()}")
    logger.info("=" * 60)

    # --- Health Check ---
    if not session.config.getoption("--skip-health-check", default=False):
        cfg = load_config()
        health_cfg = cfg.get("health_check", {})
        if health_cfg.get("enabled", False):
            from hsm_test_framework.health_check import HealthChecker
            checker = HealthChecker(health_cfg)
            report = checker.run_all()
            logger.info(report.summary())
            if not report.all_passed:
                pytest.exit(report.summary(), returncode=1)


def pytest_runtest_setup(item):
    """Skip non-smoke tests if smoke gate has failed."""
    smoke_gate = getattr(item.config, "_smoke_gate", None)
    if smoke_gate and smoke_gate.gate_failed:
        from hsm_test_framework.smoke_gate import is_smoke_test
        if not is_smoke_test(item):
            pytest.skip("Smoke gate failed: aborting remaining tests")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Track results, capture screenshot on failure, enforce smoke gate."""
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

        # Capture Kiwi case ID for bidirectional reporting
        if hasattr(item, "_kiwi_case"):
            result["_kiwi_case_id"] = item._kiwi_case.get("id")

        if not hasattr(item.session, "results"):
            item.session.results = []
        item.session.results.append(result)

        # Smoke gate tracking
        smoke_gate = getattr(item.config, "_smoke_gate", None)
        if smoke_gate and smoke_gate.active:
            from hsm_test_framework.smoke_gate import is_smoke_test
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


# ===========================================================================
# Kiwi TCMS Integration Helpers
# ===========================================================================

def _filter_by_kiwi_run(config, items, kiwi_cases):
    """
    Filter test items to only those matching Kiwi TestRun cases.

    Matching strategy:
        Only @pytest.mark.tcms(case_id=X) is used for matching.
        Name-based matching is intentionally not supported because TCMS
        summaries use bracket-tag format (e.g. "[E2E][PKCS11][Sign] ...")
        which never matches Python function names.

    After matching, two types of gaps are detected and reported:
        - Unmatched TCMS cases: cases in the TestRun with no automation test
        - Unmatched Python tests: tests with @pytest.mark.tcms pointing to
          case IDs not present in the TestRun (deselected)
    """
    case_ids = {c["id"]: c for c in kiwi_cases}
    matched_case_ids = set()

    selected = []
    deselected = []

    for item in items:
        matched = False

        tcms_marker = item.get_closest_marker("tcms")
        if tcms_marker:
            marker_case_id = tcms_marker.kwargs.get("case_id")
            if marker_case_id and marker_case_id in case_ids:
                item._kiwi_case = case_ids[marker_case_id]
                matched_case_ids.add(marker_case_id)
                matched = True

        if matched:
            selected.append(item)
        else:
            deselected.append(item)

    # --- Detect unmatched TCMS cases (no automation test exists) ---
    unmatched_cases = [c for c in kiwi_cases if c["id"] not in matched_case_ids]
    config._kiwi_unmatched_cases = unmatched_cases

    if unmatched_cases:
        logger.warning("=" * 60)
        logger.warning(
            f"TCMS COVERAGE GAP: {len(unmatched_cases)} test case(s) in "
            f"TestRun have no matching automation test"
        )
        for case in unmatched_cases:
            logger.warning(f"  - Case #{case['id']}: {case['summary']}")
        logger.warning(
            "Add @pytest.mark.tcms(case_id=X) to a Python test to link it."
        )
        logger.warning("=" * 60)

    if deselected:
        config.hook.pytest_deselected(items=deselected)
        items[:] = selected

    logger.info(
        f"Kiwi filter: {len(selected)} matched, "
        f"{len(deselected)} deselected, "
        f"{len(unmatched_cases)} TCMS cases without automation"
    )


def _push_to_kiwi(results, cfg, config=None):
    """Push results to Kiwi TCMS if enabled."""
    # Bidirectional mode: use the reporter initialized during configure
    bidir_reporter = getattr(config, "_kiwi_reporter", None) if config else None

    if bidir_reporter:
        _push_to_kiwi_bidirectional(results, bidir_reporter, config=config)
        return

    # Standard push-only mode
    tcms_config = cfg.get("kiwi_tcms", {})
    if not tcms_config.get("enabled"):
        return

    try:
        from hsm_test_framework.kiwi_tcms import KiwiReporter

        reporter = KiwiReporter(
            url=tcms_config.get("url"),
            plan_id=tcms_config.get("plan_id"),
            build_id=tcms_config.get("build_id"),
            status_ids=tcms_config.get("status_ids"),
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
            )

        reporter.finalize()
    except Exception as e:
        logger.warning(f"Kiwi TCMS reporting failed: {e}")


def _push_to_kiwi_bidirectional(results, reporter, config=None):
    """Push results to an existing Kiwi TestRun (bidirectional mode).

    Three actions:
    1. Push PASSED/FAILED for matched (executed) tests.
    2. Mark unmatched TCMS cases as BLOCKED with explanation.
    3. Log a summary of matched vs unmatched.
    """
    try:
        # 1. Report executed test results
        for result in results:
            case_id = result.get("_kiwi_case_id")
            if case_id:
                reporter.report_result_by_case_id(
                    case_id=case_id,
                    status=result["status"],
                    comment=result.get("error", ""),
                    duration=result.get("duration", 0),
                    nodeid=result.get("nodeid"),
                )

        # 2. Mark unmatched TCMS cases as BLOCKED
        unmatched = getattr(config, "_kiwi_unmatched_cases", []) if config else []
        if unmatched:
            reporter.mark_unmatched_as_blocked(unmatched)

        # 3. Summary
        executed = sum(1 for r in results if r.get("_kiwi_case_id"))
        reporter.finalize()

        logger.info("=" * 60)
        logger.info("Kiwi TCMS Bidirectional Summary")
        logger.info(f"  Executed (matched):  {executed}")
        logger.info(f"  No automation test:  {len(unmatched)}")
        if unmatched:
            for case in unmatched:
                logger.info(f"    BLOCKED  Case #{case['id']}: {case['summary']}")
        logger.info("=" * 60)

    except Exception as e:
        logger.warning(f"Kiwi TCMS bidirectional reporting failed: {e}")


def _push_metrics(results, session_duration, cfg, config=None):
    """Push metrics to Prometheus/Grafana if enabled."""
    metrics_config = cfg.get("metrics", {})
    if not metrics_config.get("enabled"):
        return

    try:
        from hsm_test_framework.grafana_push import MetricsPusher

        run_id = getattr(config, "_run_id", None) if config else None
        pusher = MetricsPusher(
            pushgateway_url=metrics_config.get("pushgateway_url"),
            job_name=metrics_config.get("job_name", "hsm_tests"),
            labels=metrics_config.get("labels", {}),
            run_id=run_id,
        )

        total = len(results)
        passed = sum(1 for r in results if r["status"] == "PASSED")

        # Count blocked cases from Kiwi bidirectional mode
        blocked = 0
        if config:
            unmatched = getattr(config, "_kiwi_unmatched_cases", [])
            blocked = len(unmatched)

        for result in results:
            pusher.record_test(
                test_name=result["name"],
                passed=(result["status"] == "PASSED"),
                duration=result.get("duration", 0),
            )

        pusher.record_suite("hsm", total, passed, session_duration,
                            blocked=blocked)
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
