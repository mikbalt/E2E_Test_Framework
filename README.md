# Sphere E2E Test Framework

Pip-installable pytest plugin for end-to-end testing of Sphere HSM devices.
Supports Windows desktop UI automation (via pywinauto) and console/CLI tools (PKCS#11).

---

## Quick Start

```bash
# 1. Clone
git clone <gitlab-url>/sphere-e2e-test-framework.git
cd sphere-e2e-test-framework

# 2. Setup (creates venv, installs deps)
scripts\setup.bat          # Windows
./scripts/setup.sh         # Linux

# 3. Configure
#    Copy .env.example → .env, fill in HSM_IP, E_ADMIN_PATH, etc.

# 4. Verify test collection
pytest tests/ui/e_admin/ -v --co
```

---

## Project Structure

```
e2e_test_framework/
├── sphere_e2e_test_framework/              # Core framework (pip-installable)
│   ├── plugin/                      # pytest plugin (auto-registered subpackage)
│   │   ├── __init__.py              # Re-exports hooks/fixtures for backward compat
│   │   ├── config.py                # Config loading, env_overrides, placeholders
│   │   ├── hooks.py                 # pytest hooks + screenshot capture
│   │   ├── fixtures.py              # config, evidence, console, ui_app fixtures
│   │   ├── kiwi_hooks.py            # Kiwi TCMS filter/push helpers
│   │   └── metrics.py               # Prometheus metrics push
│   ├── driver/                      # Infrastructure modules
│   │   ├── base.py                  # DriverProtocol (runtime-checkable interface)
│   │   ├── ui_driver.py             # pywinauto wrapper (configurable timing)
│   │   ├── evidence.py              # Screenshots, logs, StepTracker
│   │   ├── console_runner.py        # CLI subprocess wrapper
│   │   ├── window_monitor.py        # Background popup detection daemon
│   │   ├── health_check.py          # Pre-session ping + TCP checks
│   │   ├── smoke_gate.py            # Fail-fast smoke gate mechanism
│   │   ├── kiwi_tcms.py             # Kiwi TCMS bidirectional sync
│   │   ├── grafana_push.py          # Prometheus Pushgateway metrics
│   │   ├── log_collector.py         # External log file collection
│   │   ├── loki_collector.py        # Grafana Loki remote log queries
│   │   └── remote_trigger.py        # HTTP client for remote VM agents
│   ├── flows/                       # Composable test flows
│   │   ├── base.py                  # FlowContext, Step, Flow
│   │   └── e_admin.py               # Pre-composed E-Admin flows
│   ├── steps/                       # Reusable step factories
│   │   └── e_admin.py               # E-Admin step factories
│   ├── testing/                     # Conftest abstraction layer
│   │   ├── conftest_factory.py      # Fixture factories (make_driver_fixture, etc.)
│   │   ├── conftest_hooks.py        # TCMS dependency-tracking hooks (shared)
│   │   └── conftest_utils.py        # Helpers: get_tc_label, zip_app_logs
│   └── pages/                       # Page Object Model
│       ├── base_page.py             # Generic WinForms base (all apps)
│       ├── e_admin/                 # E-Admin page classes
│       │   ├── e_admin_base_page.py # E-Admin navigation base (sidebar, T&C, logout)
│       │   └── ...                  # 10 page classes inheriting EAdminBasePage
│       ├── cps/                     # CPS page classes (scaffold)
│       └── proxy/                   # Proxy page classes (scaffold)
│
├── tests/
│   ├── ui/
│   │   ├── conftest.py              # Shared hooks (dependency tracking, COM init)
│   │   ├── e_admin/                 # E-Admin UI tests (reference)
│   │   ├── cps/                     # CPS tests (see COOKBOOK.md)
│   │   └── proxy/                   # Proxy tests (see COOKBOOK.md)
│   ├── console/pkcs11/              # PKCS#11 CLI tests
│   └── unit/                        # Unit tests (config, factory, decoupling)
│
├── config/settings.yaml             # Central configuration
├── .env                             # Secrets (HSM_IP, passwords) — gitignored
├── scripts/
│   ├── setup.bat / setup.sh         # First-time setup
│   └── inspect_app.py               # UI element inspector
│
├── COOKBOOK.md                       # How to add tests for a new app
├── SETUP_GUIDE.md                   # Environment setup & CI/CD
└── docs/
    ├── INTRODUCTION.md              # Architecture overview & onboarding
    └── remote_agent_guide.md        # Multi-VM remote agent setup
```

---

## Writing a Test

```python
"""
E-Admin UI Test — Key Ceremony (FIPS)

Run: pytest tests/ui/e_admin/test_TC-37509_KeyCeremonyFIPS.py -v -s
"""
import logging

import allure
import pytest

from sphere_e2e_test_framework.pages.e_admin import LoginPage, DashboardPage

logger = logging.getLogger(__name__)


@allure.epic("Sphere HSM")
@allure.feature("E-Admin - Key Ceremony")
@allure.suite("Key Ceremony FIPS")
@allure.tag("e-admin", "windows", "ui")
@pytest.mark.ui
@pytest.mark.e_admin
@pytest.mark.tcms(case_id=37509)
class TestKeyCeremonyFIPS:

    @pytest.fixture(autouse=True)
    def setup(self, e_admin_driver, evidence, e_admin_config):
        self.driver = e_admin_driver
        self.evidence = evidence
        self.config = e_admin_config
        yield

    @allure.title("Execute FIPS Key Ceremony")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.critical
    def test_key_ceremony_fips(self):
        login = LoginPage(self.driver, self.evidence)

        # Page objects use fluent navigation — methods return next page
        dashboard = login.connect_to_hsm(step_name="Connect to HSM")
        dashboard.verify_connected(step_name="Verify connection")
```

### Key Patterns

- **Page Object Model** — Each UI screen is a class extending `BasePage` (generic WinForms) or an app-specific base like `EAdminBasePage`
- **`_step()` context manager** — Wraps actions with Allure steps + auto-screenshots
- **Fluent navigation** — Page methods return the next page object
- **`tracked_step()`** — Combines `allure.step()` + `StepTracker` in one call
- **Explicit waits** — Use `driver.wait_for_element()`, never `time.sleep()`

---

## Running Tests

| Command | What it does |
|---------|-------------|
| `pytest tests/ui/e_admin/ -v` | Run all E-Admin tests |
| `pytest -m smoke -v` | Run smoke tests only |
| `pytest -m "e_admin and critical" -v` | E-Admin critical tests |
| `pytest -m cps -v` | Run CPS tests |
| `pytest -k "KeyCeremony" -v` | Filter by keyword |
| `pytest --kiwi-run-id=123` | Run linked to TCMS TestRun #123 |
| `pytest --run-id sprint_42` | Tag run for Grafana metrics |
| `pytest --skip-health-check` | Skip pre-execution health checks |

### View Reports

```bash
npx allure open evidence/allure-results      # Allure 3 (recommended)
allure serve evidence/allure-results          # Allure 2 (requires Java)
```

---

## Available Fixtures

### Framework Fixtures (auto-provided by the plugin package)

| Fixture | Scope | Description |
|---------|-------|-------------|
| `config` | session | `settings.yaml` loaded as Python dict |
| `evidence` | per-test | Screenshot + log evidence collector |
| `console` | per-test | `ConsoleRunner` for CLI commands |
| `log_collector` | per-test | `LogCollector` linked to evidence dir |

### E-Admin Fixtures (from `tests/ui/e_admin/conftest.py`)

| Fixture | Scope | Description |
|---------|-------|-------------|
| `e_admin_config` | session | App config from `settings.yaml` |
| `e_admin_driver` | per-test | UIDriver instance (launches app) |
| `window_monitor` | per-test (autouse) | Detects unexpected popup windows |
| `collect_app_logs` | per-test (autouse) | Zips AppLogs into evidence |
| `collect_remote_logs` | per-test (autouse) | Queries Loki for remote VM logs |

---

## Markers

| Marker | Description |
|--------|-------------|
| `ui` | Windows UI automation tests (auto-skipped on Linux) |
| `console` | Console/CLI tests |
| `pkcs11` | PKCS#11 related tests |
| `e_admin` | E-Admin application tests |
| `cps` | CPS application tests |
| `proxy` | Proxy application tests |
| `smoke` | Quick verification tests |
| `critical` | Critical path tests |
| `regression` | Full regression suite |
| `slow` | Tests > 30 seconds |
| `tcms(case_id=N)` | Link to Kiwi TCMS TestCase |
| `depends_on(*ids)` | Skip if dependency TC did not pass |
| `order(index)` | Execution order (pytest-ordering) |

---

## Key Concepts

### Page Object Model (POM)

Each UI screen → one class in `sphere_e2e_test_framework/pages/<app>/`. Extends `BasePage`
(generic WinForms helpers) or an app-specific base like `EAdminBasePage` (E-Admin navigation).
Uses `_step()` for evidence-tracked actions, returns next page for fluent navigation.

### Evidence & tracked_step

Every `with self._step("description"):` block creates an Allure step with an
auto-screenshot. On test failure, a desktop + window screenshot is captured automatically.

### TCMS Integration

Mark tests with `@pytest.mark.tcms(case_id=N)`. Run with `--kiwi-run-id=X` for
bidirectional sync: framework pulls cases from TCMS, runs matched tests, pushes
PASSED/FAILED/BLOCKED back.

### Health Checks

Pre-execution ping + TCP checks ensure HSM is reachable before tests start.
Configured in `settings.yaml` under `health_check:`. Skip with `--skip-health-check`.

### Grafana Metrics

Test results are pushed to Prometheus Pushgateway with `--run-id` labels.
Import `config/grafana-dashboard.json` into Grafana for pass rate, trends, and duration panels.

---

## Adding Tests for a New Application (CPS, Proxy, etc.)

See **[COOKBOOK.md](COOKBOOK.md)** for a step-by-step guide covering:
1. Discover UI elements with `inspect_app.py`
2. Add app config to `settings.yaml`
3. Create page objects
4. Write conftest fixtures
5. Write your first test

---

## Further Reading

| Document | Contents |
|----------|----------|
| [COOKBOOK.md](COOKBOOK.md) | Step-by-step: adding tests for a new app |
| [SETUP_GUIDE.md](SETUP_GUIDE.md) | Prerequisites, Jenkins CI, TCMS, Grafana setup |
| [docs/INTRODUCTION.md](docs/INTRODUCTION.md) | Architecture overview & onboarding |
| [docs/remote_agent_guide.md](docs/remote_agent_guide.md) | Multi-VM remote agent setup |
| [config/settings.yaml](config/settings.yaml) | Full configuration reference (inline comments) |
