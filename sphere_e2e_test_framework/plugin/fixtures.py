"""Shared pytest fixtures provided by the Sphere E2E Test Framework plugin."""

import logging
import platform

import pytest

from sphere_e2e_test_framework.plugin.config import load_config

logger = logging.getLogger(__name__)

IS_WINDOWS = platform.system() == "Windows"


@pytest.fixture(scope="session")
def config():
    """Provide test configuration from settings.yaml."""
    return load_config()


@pytest.fixture
def evidence(request):
    """Provide Evidence collector for the current test."""
    from sphere_e2e_test_framework.driver.evidence import Evidence

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
    from sphere_e2e_test_framework.driver.console_runner import ConsoleRunner
    return ConsoleRunner()


@pytest.fixture
def log_collector(evidence):
    """Provide LogCollector instance linked to current test's evidence."""
    from sphere_e2e_test_framework.driver.log_collector import LogCollector
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

    from sphere_e2e_test_framework.driver.ui_driver import UIDriver

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
