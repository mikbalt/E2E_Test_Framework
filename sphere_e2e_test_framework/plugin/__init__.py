"""Sphere E2E Test Framework - pytest plugin (auto-registered).

When a consumer repo installs sphere-e2e-test-framework, this plugin is automatically
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
    from sphere_e2e_test_framework.plugin import *  # noqa: re-export fixtures

Or rely on auto-registration (pytest11 entry point).
"""

from sphere_e2e_test_framework.plugin.hooks import (  # noqa: F401
    pytest_addoption,
    pytest_configure,
    pytest_collection_modifyitems,
    pytest_sessionstart,
    pytest_runtest_setup,
    pytest_runtest_makereport,
    pytest_sessionfinish,
)
from sphere_e2e_test_framework.plugin.fixtures import (  # noqa: F401
    config,
    evidence,
    console,
    log_collector,
    ui_app,
)
from sphere_e2e_test_framework.plugin.config import load_config  # noqa: F401
