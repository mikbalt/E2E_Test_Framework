# Cookbook: Adding Tests for a New Application

This guide walks you through adding UI tests for a new Windows application (e.g., CPS, Proxy)
using the existing E-Admin tests as a reference.

**Time estimate:** ~30 minutes for a basic test running end-to-end.

---

## Before You Start

- Framework installed (`pip install -e .`) and `.env` configured
- The target application (.exe) is available on your Windows machine
- Tool: `scripts/inspect_app.py` for discovering UI element IDs

---

## Step 1: Discover UI Elements

Before writing any page objects, you need to know the automation IDs, control types,
and element names in your target application.

```cmd
:: Launch and scan the app
python scripts\inspect_app.py "C:\Path\To\YourApp.exe"

:: Scan an already-running app by window title
python scripts\inspect_app.py --title "Your App Title"

:: Deep scan (more nesting levels)
python scripts\inspect_app.py --title "Your App Title" --depth 5

:: Save output to file for reference
python scripts\inspect_app.py --title "Your App Title" --output controls.txt

:: Interactive mode — hover over elements to identify them
python scripts\inspect_app.py --title "Your App Title" --interactive

:: Try different backend if elements aren't found
python scripts\inspect_app.py --title "Your App Title" --backend win32
```

The output shows three sections:

| Section | Contains | Example |
|---------|----------|---------|
| **Clickable** | Buttons, menus, tabs | `Button "Login" auto_id="btnLogin"` |
| **Inputs** | Text boxes, dropdowns | `Edit auto_id="txtUsername"` |
| **Text/Status** | Labels, status bars | `Text "Connected" auto_id="lblStatus"` |

**Priority:** Always prefer `auto_id` (stable) over `name` (may change with UI text).

---

## Step 2: Add App Config to `settings.yaml`

Add your application under `apps:` in `config/settings.yaml`:

```yaml
apps:
  e_admin:
    # ... existing config ...

  # New application
  cps:
    path: "${CPS_APP_PATH}"                      # Set in .env
    class_name: "WindowsForms10\\.Window.*"       # WinForms pattern (adjust for your app)
    startup_wait: 5                               # Seconds to wait after launch
    backend: "uia"                                # "uia" (WPF/modern) or "win32" (WinForms)
    app_logs_dir: "${CPS_APP_LOGS}"               # Optional: app log directory
    popup_dismiss_buttons: ["OK", "Yes", "Close"] # Buttons to auto-dismiss popups
    popup_dismiss_auto_ids: ["2"]                 # Auto IDs for popup dismiss buttons
    connection:
      ip: "${HSM_IP}"
      port: "${HSM_PORT}"
```

---

## Step 3: Add Environment Variables to `.env`

```bash
# --- CPS ---
CPS_APP_PATH=C:\SPHERE_HSM\CPS\CPS.exe
CPS_APP_LOGS=C:\SPHERE_HSM\CPS\AppLogs
```

---

## Step 4: Create Page Objects

Create a new directory under `sphere_e2e_test_framework/pages/` for your app:

```
sphere_e2e_test_framework/pages/cps/
    __init__.py
    login_page.py
    main_page.py
```

### `__init__.py`

```python
"""CPS Page Object Model (POM) classes."""
from sphere_e2e_test_framework.pages.cps.login_page import LoginPage

__all__ = ["LoginPage"]
```

### `login_page.py` — Minimal Example

```python
"""CPS Login page object."""
import logging
from sphere_e2e_test_framework.pages.base_page import BasePage

logger = logging.getLogger(__name__)
TIMEOUT = 120


class LoginPage(BasePage):
    """CPS login screen — connect to HSM and authenticate."""

    def connect_to_hsm(self, ip, port, step_name=None):
        """Fill HSM connection fields and click Connect.

        Returns: next page object (e.g., MainPage) after connection.
        """
        with self._step(step_name or "Connect to HSM"):
            self.driver.type_text(ip, auto_id="txtIP")
            self.driver.type_text(str(port), auto_id="txtPort")
            self.driver.click_button(auto_id="btnConnect")

        # Fluent navigation — return the next page
        from sphere_e2e_test_framework.pages.cps.main_page import MainPage
        return MainPage(self.driver, self.evidence)
```

### Key Patterns

| Pattern | How | Why |
|---------|-----|-----|
| **`_step()` context manager** | `with self._step("description"):` | Auto-screenshot + Allure step |
| **Fluent return** | Method returns next page object | Enables `main = login.connect(...)` |
| **Evidence optional** | `BasePage.__init__(driver, evidence=None)` | Page objects work with or without evidence |
| **Lazy import** | Import next page inside method | Avoids circular imports |

> **Note:** `BasePage` contains only generic WinForms helpers (`dismiss_ok`, `_step`,
> `dismiss_ok_with_message`). E-Admin-specific navigation (`logout`, `agree_and_next`,
> `goto_user_management`) lives in `EAdminBasePage`. New apps should inherit from
> `BasePage` directly — they get a clean base without E-Admin methods.

### WinForms Quirks

| Issue | Solution |
|-------|----------|
| **ComboBox selection** | `driver.select_combobox(auto_id="cmbType", value="RSA")` |
| **Async popup** | `driver.wait_for_element(timeout=30, auto_id="2", control_type="Button")` |
| **Reading popup text** | `self.dismiss_ok_with_message(step_name="...")` — inherited from BasePage |
| **Element not found** | Try `--backend win32` in inspect_app.py; some WinForms controls need it |
| **Stale window handle** | Call `driver.refresh_window()` after major navigation |

---

## Step 5: Create conftest.py for Your Test Suite

Create `tests/ui/cps/conftest.py` — this provides fixtures specific to your app.

### Option A: Factory Pattern (Recommended)

The framework provides fixture factories that generate all standard fixtures in a few lines:

```python
"""
tests/ui/cps/conftest.py -- CPS-specific fixtures (factory approach).
"""
from sphere_e2e_test_framework.testing.conftest_factory import (
    make_app_config_fixture,
    make_driver_fixture,
    make_window_monitor_fixture,
    make_app_logs_fixture,
)

cps_config = make_app_config_fixture("cps")
cps_driver = make_driver_fixture("cps")
window_monitor = make_window_monitor_fixture("cps")
collect_app_logs = make_app_logs_fixture("cps")
```

This gives you `cps_config`, `cps_driver`, `window_monitor`, and `collect_app_logs` fixtures
with all the same behavior as the manual approach below. Use `pre_launch_hook` or
`driver_class` arguments to `make_driver_fixture()` for customization.

### Option B: Manual Fixtures

Copy the pattern from `tests/ui/e_admin/conftest.py` and adapt:

```python
"""
tests/ui/cps/conftest.py -- CPS-specific fixtures.

Provides:
- cps_config: session-scoped config extracted from settings.yaml
- cps_driver: function-scoped UIDriver
- window_monitor: background monitor for unexpected windows
- collect_app_logs: auto-collects CPS AppLogs after each test
"""
import datetime
import logging
import os
import zipfile

import pytest

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def cps_config(config):
    """Extract CPS app config once per session."""
    return config.get("apps", {}).get("cps", {})


@pytest.fixture
def cps_driver(cps_config):
    """UIDriver for CPS application."""
    from sphere_e2e_test_framework.driver.ui_driver import UIDriver

    driver = UIDriver(
        app_path=cps_config.get("path"),
        class_name=cps_config.get("class_name"),
        backend=cps_config.get("backend", "uia"),
        startup_wait=cps_config.get("startup_wait", 5),
        popup_dismiss_buttons=cps_config.get("popup_dismiss_buttons"),
        popup_dismiss_auto_ids=cps_config.get("popup_dismiss_auto_ids"),
    )
    driver.start()

    retry_cfg = cps_config.get("retry", {})
    if retry_cfg:
        driver.set_retry_config(retry_cfg)

    yield driver
    driver.close()
    logger.info("cps_driver fixture finalized - app closed")


@pytest.fixture(autouse=True)
def window_monitor(request, cps_config, cps_driver, evidence):
    """Background monitor for unexpected windows during test."""
    monitor_cfg = cps_config.get("window_monitor", {})
    if not monitor_cfg.get("enabled", True):
        yield None
        return

    from sphere_e2e_test_framework.driver.window_monitor import WindowMonitor

    pid = cps_driver.app.process
    monitor = WindowMonitor(app_pid=pid, evidence=evidence)
    monitor.snapshot_baseline()
    monitor.add_whitelist(cps_driver._main_handle)
    cps_driver.set_window_monitor(monitor)

    interval = monitor_cfg.get("interval", 1.0)
    monitor.start(interval=interval)
    yield monitor

    detected = monitor.stop()
    cps_driver.set_window_monitor(None)
    if detected:
        logger.warning(
            f"Test '{request.node.name}' finished with "
            f"{len(detected)} unexpected window(s) detected"
        )


@pytest.fixture(autouse=True)
def collect_app_logs(request, cps_config, evidence):
    """Auto-collect CPS AppLogs into a zip after each test."""
    yield

    app_logs_dir = cps_config.get("app_logs_dir", "")
    if not app_logs_dir or not os.path.isdir(app_logs_dir):
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
            return

        logger.info(f"Collected {file_count} app log files -> {zip_path}")

        try:
            import allure
            with open(zip_path, "rb") as f:
                allure.attach(
                    f.read(), name=zip_name,
                    attachment_type="application/zip", extension="zip",
                )
        except ImportError:
            pass
    except Exception as e:
        logger.warning(f"Failed to collect app logs: {e}")
```

---

## Step 6: Write Your First Test

Create `tests/ui/cps/test_TC-XXXXX_YourTestName.py`:

```python
"""
CPS UI Test - Connect and Verify Dashboard

Scenario:
    Given CPS application is launched
    When operator connects to HSM
    Then dashboard loads successfully

Run:
    pytest tests/ui/cps/test_TC-XXXXX_YourTestName.py -v -s
"""
import logging

import allure
import pytest

from sphere_e2e_test_framework.pages.cps import LoginPage

logger = logging.getLogger(__name__)


@allure.epic("Sphere HSM")
@allure.feature("CPS")
@allure.suite("CPS - Connection")
@allure.tag("cps", "windows", "ui")
@pytest.mark.ui
@pytest.mark.cps
@pytest.mark.tcms(case_id=99999)  # Replace with actual TCMS case ID
class TestCPSConnection:

    @pytest.fixture(autouse=True)
    def setup(self, cps_driver, evidence, cps_config):
        """Wire shared fixtures into test instance."""
        self.driver = cps_driver
        self.evidence = evidence
        self.config = cps_config
        yield

    @allure.title("CPS - Connect to HSM and Load Dashboard")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    @pytest.mark.critical
    def test_connect_and_load_dashboard(self):
        driver = self.driver
        evidence = self.evidence

        # Background: app is launched (handled by cps_driver fixture)
        login = LoginPage(driver, evidence)

        # Scenario: Connect to HSM
        hsm_ip = self.config.get("connection", {}).get("ip", "")
        hsm_port = self.config.get("connection", {}).get("port", "")

        main_page = login.connect_to_hsm(
            ip=hsm_ip, port=hsm_port,
            step_name="Given: Connect to HSM",
        )

        # Verify dashboard loaded
        # TODO: Replace with actual assertions for your app
        assert driver.main_window.is_visible(), (
            "CPS main window is not visible after connection"
        )
        logger.info("CPS dashboard loaded successfully")
```

---

## Step 7: Run & Verify

```bash
# Verify test collection (no import errors)
pytest tests/ui/cps/ --co -v

# Run the test
pytest tests/ui/cps/ -v -s

# View Allure report
npx allure open evidence/allure-results
```

---

## Reference: Mapping E-Admin Fixtures to Your App

When adapting from E-Admin tests, use this mapping:

| E-Admin | Your App (e.g., CPS) | Location |
|---------|----------------------|----------|
| `e_admin_config` | `cps_config` | `tests/ui/cps/conftest.py` |
| `e_admin_driver` | `cps_driver` | `tests/ui/cps/conftest.py` |
| `LoginPage` (e_admin) | `LoginPage` (cps) | `sphere_e2e_test_framework/pages/cps/` |
| `DashboardPage` (e_admin) | `MainPage` (cps) | `sphere_e2e_test_framework/pages/cps/` |
| `@pytest.mark.e_admin` | `@pytest.mark.cps` | Test class decorator |
| `apps.e_admin` in yaml | `apps.cps` in yaml | `config/settings.yaml` |
| `E_ADMIN_PATH` in .env | `CPS_APP_PATH` in .env | `.env` |

---

## Reference: Test Dependencies

If your tests must run in a specific order (e.g., login before operations):

```python
@pytest.mark.tcms(case_id=100)
class TestCPSLogin:
    def test_login(self): ...

@pytest.mark.tcms(case_id=101)
@pytest.mark.depends_on(100)       # Skipped if TC-100 did not pass
class TestCPSOperation:
    def test_do_operation(self): ...
```

The `depends_on` marker is enforced by the shared dependency-tracking hooks in
`tests/ui/conftest.py`. These hooks are inherited by all app-specific test directories
(`e_admin/`, `cps/`, `proxy/`) — no need to duplicate them in your per-app conftest.
