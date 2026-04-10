"""Shared pytest fixtures provided by the Ankole Framework plugin."""

import logging
import platform

import pytest

from ankole.plugin.config import load_config

logger = logging.getLogger(__name__)

IS_WINDOWS = platform.system() == "Windows"


@pytest.fixture(scope="session")
def config():
    """Provide test configuration from settings.yaml."""
    return load_config()


@pytest.fixture
def evidence(request):
    """Provide Evidence collector for the current test."""
    from ankole.driver.evidence import Evidence

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
    from ankole.driver.console_runner import ConsoleRunner
    return ConsoleRunner()


@pytest.fixture
def log_collector(evidence):
    """Provide LogCollector instance linked to current test's evidence."""
    from ankole.driver.log_collector import LogCollector
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

    from ankole.driver.ui_driver import UIDriver

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


# -- Phase 1 fixtures --------------------------------------------------------

@pytest.fixture
def cleanup_tracker():
    """Provide a CleanupTracker for test data lifecycle management."""
    from ankole.testing.data_factory import CleanupTracker

    tracker = CleanupTracker()
    yield tracker
    tracker.cleanup_all()


@pytest.fixture
def data_factory():
    """Provide a DataFactory with automatic cleanup after test."""
    from ankole.testing.data_factory import DataFactory

    factory = DataFactory()
    yield factory
    factory.cleanup_all()


@pytest.fixture
def db_driver(config):
    """Provide a DBDriver for database assertions."""
    from ankole.driver.db_driver import DBDriver

    dsn = (
        config.get("workspace", {})
        .get("database", {})
        .get("dsn", "postgresql://localhost/test")
    )
    autorollback = (
        config.get("workspace", {})
        .get("database", {})
        .get("autorollback", True)
    )
    driver = DBDriver(dsn=dsn, autorollback=autorollback)
    driver.connect()
    yield driver
    driver.close()


# -- Phase 2 fixtures --------------------------------------------------------

@pytest.fixture
def visual_comparator(config):
    """Provide a VisualComparator for visual regression testing."""
    from ankole.driver.visual import VisualComparator

    vis_cfg = config.get("visual_regression", {})
    return VisualComparator(
        baseline_dir=vis_cfg.get("baseline_dir", "baselines"),
        actual_dir=vis_cfg.get("actual_dir", "evidence/visual/actual"),
        diff_dir=vis_cfg.get("diff_dir", "evidence/visual/diff"),
        threshold=vis_cfg.get("threshold", 0.01),
    )


@pytest.fixture
def a11y_scanner(config):
    """Provide an A11yScanner for accessibility testing."""
    from ankole.driver.a11y import A11yScanner

    a11y_cfg = config.get("accessibility", {})
    return A11yScanner(
        default_tags=a11y_cfg.get("tags", ["wcag2a", "wcag2aa"]),
        disabled_rules=a11y_cfg.get("disabled_rules", []),
    )


# -- Phase 3 fixtures --------------------------------------------------------

@pytest.fixture
def api_mocker():
    """Provide an APIMocker for httpx request mocking."""
    from ankole.driver.api_mock import APIMocker

    mocker = APIMocker()
    mocker.start()
    yield mocker
    mocker.stop()


@pytest.fixture
def browser_mocker(web_driver):
    """Provide a BrowserMocker for Playwright route interception.

    Requires the `web_driver` fixture to be active.
    """
    from ankole.driver.api_mock import BrowserMocker

    mocker = BrowserMocker(page=web_driver.page)
    yield mocker
    mocker.clear_all()
