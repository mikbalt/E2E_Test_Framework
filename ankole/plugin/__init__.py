"""Ankole Framework - pytest plugin (auto-registered).

When a consumer repo installs ankole-framework, this plugin is automatically
loaded by pytest via the entry point. It provides:

- Platform detection (auto-skip desktop tests on non-Windows)
- Pre-execution health checks (--skip-health-check to bypass)
- Smoke gate / fail-fast (--smoke-gate)
- Kiwi TCMS bidirectional integration (--kiwi-run-id)
- Screenshot on failure
- Kiwi TCMS result reporting
- Grafana/Prometheus metrics push
- Shared fixtures: evidence, console, ui_app, config

Consumer repos only need a minimal conftest.py:

    # conftest.py
    from ankole.plugin import *  # noqa: re-export fixtures

Or rely on auto-registration (pytest11 entry point).
"""

from ankole.plugin.hooks import (  # noqa: F401
    pytest_addoption,
    pytest_configure,
    pytest_collection_modifyitems,
    pytest_sessionstart,
    pytest_runtest_setup,
    pytest_runtest_makereport,
    pytest_sessionfinish,
)
from ankole.plugin.fixtures import (  # noqa: F401
    config,
    evidence,
    console,
    log_collector,
    ui_app,
)
from ankole.plugin.config import load_config  # noqa: F401
