# Sphere E2E Test Framework — Introduction

## What Is This?

The Sphere E2E Test Framework is a **pytest-based automation framework** purpose-built
for end-to-end testing of Sphere HSM (Hardware Security Module) devices and their
supporting applications.

It automates the full test lifecycle: **launch app → execute steps → capture evidence
→ report results** — across Windows desktop apps (E-Admin, CPS, Proxy) and
console/CLI tools (PKCS#11 in Go, Java, C++).

### Who Is This For?

- **QA Engineers** writing new UI or console tests for HSM applications
- **Developers** validating HSM features in CI/CD pipelines
- **Team Leads** tracking test coverage and results via Grafana/TCMS dashboards

---

## What Does It Cover?

### Applications Under Test

| Application | Type | Status | Test Location |
|-------------|------|--------|---------------|
| **E-Admin** | WinForms desktop app | Active (9 test classes) | `tests/ui/e_admin/` |
| **CPS** | WinForms desktop app | Active (4 test classes) | `tests/ui/cps/` |
| **Proxy** | WinForms desktop app | Scaffolded (ready to write) | `tests/ui/proxy/` |
| **PKCS#11 Tools** | CLI (Go, Java, C++, GTest) | Active (6 test classes) | `tests/console/pkcs11/` |

### Test Scenarios (E-Admin)

| Test Case | TCMS ID | What It Tests |
|-----------|---------|---------------|
| Key Ceremony (FIPS) | TC-37509 | Full FIPS key ceremony workflow |
| Key Ceremony (Non-FIPS) | TC-37515 | Non-FIPS key ceremony workflow |
| Operational User Creation | TC-37516 | Create operational users with roles |
| HSM Reset by Super User | TC-37517 | HSM reset via super user privileges |
| Delete Operational User | TC-37520 | User deletion and verification |
| Block User | TC-37522 | Block an operational user |
| Unblock User | TC-37523 | Unblock a previously blocked user |
| Customer Key Ceremony (Generate & Export) | TC-37524 | CKC: create KCPs, generate key, export per KCP |
| Customer Key Ceremony (Import) | TC-XXXXX | CKC: reuse KCPs, import key components per KCP |

---

## Architecture Overview

```mermaid
graph TB
    subgraph Framework["Sphere E2E Test Framework"]
        direction TB

        subgraph FlowStep["Flow / Step Orchestration"]
            FL["Flow<br/><i>composable sequences</i>"]
            ST["Step Factories<br/><i>reusable, data-driven</i>"]
            FC["FlowContext<br/><i>driver + evidence + state</i>"]
            FL --> ST --> FC
        end

        subgraph POM["Page Object Model"]
            BP["BasePage<br/><i>generic WinForms</i>"]
            EAB["EAdminBasePage<br/><i>sidebar, T&C, logout</i>"]
            EA["e_admin/<br/>12 page classes"]
            CP["cps/<br/><i>scaffold</i>"]
            PX["proxy/<br/><i>scaffold</i>"]
            BP --> EAB --> EA
            BP --> CP & PX
        end

        subgraph Core["Core Engines"]
            UI["UI Driver<br/><i>pywinauto</i><br/>WPF / WinForms"]
            DP["DriverProtocol<br/><i>duck-typed interface</i>"]
            CR["Console Runner<br/><i>subprocess</i><br/>CLI tools"]
            EV["Evidence Engine<br/><i>mss + Pillow</i><br/>Screenshots & Logs"]
        end

        subgraph Integrations
            TCMS["Kiwi TCMS<br/><i>Bidirectional sync</i>"]
            GRAF["Grafana<br/><i>Prometheus metrics</i>"]
            LOKI["Loki<br/><i>Remote log collection</i>"]
            RA["Remote Agents<br/><i>Multi-VM orchestration</i>"]
        end

        subgraph Infra["Infrastructure"]
            HC["Health Check<br/><i>Ping + TCP</i>"]
            SG["Smoke Gate<br/><i>Fail-fast</i>"]
            WM["Window Monitor<br/><i>Popup detection</i>"]
            CFG["Config<br/><i>YAML + .env</i>"]
        end
    end

    subgraph Targets["Systems Under Test"]
        EADMIN["E-Admin App<br/><i>WinForms on VM</i>"]
        CPSAPP["CPS App<br/><i>WinForms on VM</i>"]
        PROXYAPP["Proxy App<br/><i>WinForms on VM</i>"]
        PKCS["PKCS#11 CLI<br/><i>Go / Java / C++</i>"]
        HSM[("Sphere HSM<br/>Device")]
    end

    UI --> EADMIN & CPSAPP & PROXYAPP
    CR --> PKCS
    EADMIN & CPSAPP & PROXYAPP & PKCS --> HSM

    style Framework fill:#1a1a2e,stroke:#16213e,color:#e0e0e0
    style Core fill:#0f3460,stroke:#533483,color:#e0e0e0
    style POM fill:#0f3460,stroke:#533483,color:#e0e0e0
    style Integrations fill:#0f3460,stroke:#533483,color:#e0e0e0
    style Infra fill:#0f3460,stroke:#533483,color:#e0e0e0
    style Targets fill:#1a1a2e,stroke:#e94560,color:#e0e0e0
    style HSM fill:#e94560,stroke:#e94560,color:#ffffff
```

---

## Test Execution Lifecycle

Every `pytest` run follows this lifecycle — from environment validation to result reporting:

```mermaid
flowchart LR
    A["pytest invoked"] --> B{"Health Check"}
    B -- Pass --> C["Collect Tests"]
    B -- Fail --> X["Abort with<br/>diagnostics"]
    C --> D{"TCMS Filter?"}
    D -- "--kiwi-run-id" --> E["Pull TCMS cases<br/>Filter to matched"]
    D -- "No flag" --> F["All collected tests"]
    E --> G{"Smoke Gate?"}
    F --> G
    G -- "--smoke-gate" --> H["Reorder: smoke first"]
    G -- "No flag" --> I["Execute Tests"]
    H --> I
    I --> J["Evidence captured<br/>per step"]
    J --> K["Push Results"]
    K --> L["Allure Report"]
    K --> M["TCMS Update"]
    K --> N["Grafana Metrics"]

    style A fill:#2d3436,stroke:#636e72,color:#dfe6e9
    style X fill:#d63031,stroke:#ff7675,color:#ffffff
    style L fill:#0984e3,stroke:#74b9ff,color:#ffffff
    style M fill:#00b894,stroke:#55efc4,color:#ffffff
    style N fill:#fdcb6e,stroke:#ffeaa7,color:#2d3436
```

---

## Core Capabilities

### 1. Windows UI Automation

Automates WinForms and WPF desktop applications using pywinauto:

- **Launch & connect** to applications by path or window class
- **Interact with UI elements** — click buttons, type text, select dropdowns, navigate tabs
- **Wait for elements** — explicit waits instead of `sleep()`, with configurable timeouts
- **Auto-dismiss popups** — configurable button list for automatic popup handling
- **Window monitoring** — background thread detects unexpected windows during tests
- **Element discovery** — `inspect_app.py` tool scans running apps for automation IDs

### 2. Console/CLI Tool Testing

Wraps existing command-line tools (PKCS#11, etc.) without modifying their source code:

- **Subprocess execution** with stdout/stderr capture and timeout
- **Cross-platform** — separate commands for Windows and Linux
- **Built-in assertions** — `assert_success()`, `assert_output_contains()`
- **Language helpers** — `run_java()`, `run_go()`, `run_make()`, `run_executable()`

### 3. Evidence Engine

Every test produces a complete evidence trail — automatically:

```mermaid
flowchart LR
    subgraph Test["Test Execution"]
        S1["Step 1<br/><i>tracked_step()</i>"]
        S2["Step 2"]
        S3["Step N"]
        S1 --> S2 --> S3
    end

    subgraph Evidence["Evidence Collected"]
        SS["Step Screenshots<br/><i>auto per _step()</i>"]
        FS["Failure Screenshot<br/><i>desktop + window</i>"]
        AL["App Logs<br/><i>zipped per test</i>"]
        RL["Remote Logs<br/><i>Loki time-range query</i>"]
        CO["Console Output<br/><i>stdout + stderr</i>"]
    end

    subgraph Output["Attached To"]
        ALLURE["Allure Report"]
        EVDIR["evidence/ folder"]
    end

    S1 --> SS
    S3 --"on failure"--> FS
    S3 --"teardown"--> AL & RL
    S2 --> CO

    SS & FS & AL & RL & CO --> ALLURE
    SS & FS & AL --> EVDIR

    style Test fill:#2d3436,stroke:#636e72,color:#dfe6e9
    style Evidence fill:#0f3460,stroke:#533483,color:#e0e0e0
    style Output fill:#00b894,stroke:#55efc4,color:#ffffff
```

### 4. Flow/Step Orchestration

Complex multi-step workflows (key ceremony, customer key ceremony) are composed
from reusable **Step** factories and executed via **Flow** objects:

```python
# Step factory — returns a reusable Step
def ckc_login_admin(username_attr="admin_username", password_attr="admin_password"):
    def _action(ctx):
        ckc = ctx.get("_ckc_page") or CustomerKeyCeremonyPage(ctx.driver, ctx.evidence)
        ckc.login_admin(getattr(ctx.td, username_attr), getattr(ctx.td, password_attr),
                        step_name="And: Admin logs in for CKC")
    return Step("Admin login for CKC", _action)

# Flow — compose steps into a runnable sequence
customer_key_ceremony_flow = Flow("Customer Key Ceremony", [
    connect(),
    start_ckc(),
    ckc_accept_terms(),
    ckc_login_admin(),
    ckc_create_custodian_parties(),
    ckc_proceed_next(),
    ckc_select_generate_and_export(),
    ckc_configure_key(),
    ckc_generate_key(),
    ckc_export_all_custodian_keys(),
    ckc_verify_key_summary(),
    ckc_finish(),
    ckc_save_export_results(),
])

# Test — run flow with context
def test_customer_key_ceremony(self):
    ctx = FlowContext(self.driver, self.evidence, self.td)
    customer_key_ceremony_flow.run(ctx)
```

```mermaid
flowchart LR
    subgraph FlowLayer["Flow Layer"]
        F["Flow<br/><i>sequence of steps</i>"]
    end

    subgraph StepLayer["Step Layer"]
        S1["Step 1<br/><i>connect()</i>"]
        S2["Step 2<br/><i>login()</i>"]
        S3["Step N<br/><i>finish()</i>"]
    end

    subgraph PageLayer["Page Object Layer"]
        PO["Page Objects<br/><i>UI interactions</i>"]
    end

    subgraph DriverLayer["Driver Layer"]
        DR["UIDriver<br/><i>pywinauto</i>"]
    end

    F --> S1 & S2 & S3
    S1 & S2 & S3 --> PO
    PO --> DR

    style FlowLayer fill:#00b894,stroke:#55efc4,color:#ffffff
    style StepLayer fill:#0984e3,stroke:#74b9ff,color:#ffffff
    style PageLayer fill:#0f3460,stroke:#533483,color:#e0e0e0
    style DriverLayer fill:#2d3436,stroke:#636e72,color:#dfe6e9
```

Key features:
- **`Step(retries=N, retry_delay=T)`** — exponential backoff retry on failure
- **`Step(on_failure=callback)`** — cleanup callback on final failure
- **`Flow(cleanup_steps=[...])`** — always-run steps in finally block
- **`Flow(continue_on_failure=True)`** — tolerate step failures, record in FlowResult
- **`FlowContext`** — carries driver, evidence, test data, and shared state across steps
- **Data-driven** — step factories read from `ctx.td` (test data dataclass)

### 5. Page Object Model (POM)

Each application screen is a Python class that encapsulates UI interactions:

```python
# Fluent navigation — methods return the next page
login = LoginPage(driver, evidence)
dashboard = login.connect_to_hsm(step_name="Connect to HSM")
dashboard.create_user(username="operator1", step_name="Create user")
```

```mermaid
classDiagram
    class BasePage {
        +driver: UIDriver
        +evidence: Evidence
        +_step(description) context manager
        +dismiss_ok(step_name)
        +dismiss_ok_with_message(step_name)
    }

    class EAdminBasePage {
        +agree_and_next(step_name)
        +goto_user_management() UserCreationPage
        +goto_profile_management()
        +logout() LoginPage
    }

    class LoginPage {
        +connect_to_hsm(ip, port) DashboardPage
        +login(username, password) DashboardPage
    }

    class DashboardPage {
        +verify_connected(step_name)
        +navigate_to_key_ceremony() KeyCeremonyFlow
        +navigate_to_user_management() UserManagementPage
    }

    class KeyCeremonyFlow {
        +start_ceremony(data)
        +import_ccmk() CCMKImportPage
    }

    class CustomerKeyCeremonyPage {
        +start_ckc()
        +login_admin(username, password)
        +create_custodian_party(username, password, add_button_id)
        +select_generate_and_export()
        +configure_key(key_label, key_algo, key_length, ...)
        +generate_key()
        +read_export_values(is_last)
        +get_key_summary()
    }

    class UserManagementPage {
        +create_user(data) UserCreationPage
        +delete_user(username)
        +block_user(username)
        +unblock_user(username)
    }

    BasePage <|-- EAdminBasePage
    EAdminBasePage <|-- LoginPage
    EAdminBasePage <|-- DashboardPage
    EAdminBasePage <|-- KeyCeremonyFlow
    EAdminBasePage <|-- CustomerKeyCeremonyPage
    EAdminBasePage <|-- UserManagementPage

    LoginPage --> DashboardPage : returns
    DashboardPage --> KeyCeremonyFlow : navigates
    DashboardPage --> CustomerKeyCeremonyPage : navigates
    DashboardPage --> UserManagementPage : navigates
```

Key patterns:
- **`_step()` context manager** — wraps actions with Allure steps + auto-screenshots
- **Fluent return** — each method returns the next page object
- **Evidence optional** — page objects work with or without evidence tracking
- **`BasePage`** — generic WinForms helpers (dismiss dialogs, `_step()`)
- **`EAdminBasePage`** — E-Admin-specific navigation (sidebar, T&C acceptance, logout)

### 6. Health Checks

Pre-execution verification ensures the test environment is ready before running:

- **Ping check** — HSM device is network-reachable
- **TCP check** — Required ports are open
- **Configurable** in `settings.yaml` → `health_check:`
- **Skip with** `pytest --skip-health-check`

### 7. Smoke Gate

Fail-fast mechanism: if any `@pytest.mark.smoke` test fails, abort remaining tests.

```bash
pytest --smoke-gate      # All smoke tests run first; abort if any fail
```

---

## Integrations

### Kiwi TCMS — Test Case Management

Bidirectional sync between Python tests and Kiwi TCMS test cases:

```mermaid
sequenceDiagram
    participant P as pytest
    participant K as Kiwi TCMS

    Note over P,K: Phase 1 — PULL
    P->>K: Fetch TestRun #123
    K-->>P: Return test cases (case_id, summary, execution_id)

    Note over P,K: Phase 2 — MATCH
    P->>P: Scan @pytest.mark.tcms(case_id=X)<br/>Match collected tests to TCMS cases<br/>Deselect unmatched tests

    Note over P,K: Phase 3 — EXECUTE
    P->>P: Run matched tests<br/>Collect evidence per step

    Note over P,K: Phase 4 — PUSH
    P->>K: Update PASSED / FAILED per case
    P->>K: Mark unmatched TCMS cases as BLOCKED
    P->>K: Attach error details + evidence
```

### Grafana + Prometheus — Metrics Dashboard

Test results are pushed to Prometheus Pushgateway, visualized in Grafana:

```mermaid
flowchart LR
    PT["pytest<br/>--run-id sprint_42"] -->|push metrics| PG["Prometheus<br/>Pushgateway"]
    PG -->|scrape| PROM["Prometheus"]
    PROM -->|query| GF["Grafana Dashboard"]

    subgraph GF["Grafana Panels"]
        G1["Pass Rate Gauge"]
        G2["Duration Trends"]
        G3["Coverage Breakdown"]
        G4["Run Comparison"]
    end

    style PT fill:#2d3436,stroke:#636e72,color:#dfe6e9
    style PG fill:#e17055,stroke:#fab1a0,color:#ffffff
    style PROM fill:#d63031,stroke:#ff7675,color:#ffffff
    style GF fill:#0984e3,stroke:#74b9ff,color:#ffffff
```

### Loki — Remote Log Collection

After each test, the framework queries Loki for logs from all configured VMs
within the test's time range. Logs are saved, zipped, and attached to the Allure report.

Useful for multi-VM scenarios where the HSM, Proxy, and Admin apps run on separate machines.

### Remote Agents — Multi-VM Orchestration

HTTP-based agents running on remote Windows VMs allow the framework to:

- Execute scripts and commands on remote machines
- Capture remote screenshots
- Coordinate multi-VM test scenarios (e.g., Admin on VM1, Proxy on VM2)

---

## Configuration

The framework uses a layered configuration approach:

```mermaid
flowchart TB
    ENV[".env<br/><i>Secrets</i><br/>HSM_IP, passwords, app paths"]
    YAML["config/settings.yaml<br/><i>Structure</i><br/>App config, health checks,<br/>integrations"]
    TOML["pyproject.toml<br/><i>pytest options</i><br/>Markers, timeouts, Allure"]

    ENV -->|"${VAR} substitution"| YAML
    YAML -->|"loaded as dict"| CFG["config fixture<br/><i>available in all tests</i>"]
    TOML -->|"pytest reads"| PYTEST["pytest engine"]

    style ENV fill:#d63031,stroke:#ff7675,color:#ffffff
    style YAML fill:#0984e3,stroke:#74b9ff,color:#ffffff
    style TOML fill:#636e72,stroke:#b2bec3,color:#ffffff
    style CFG fill:#00b894,stroke:#55efc4,color:#ffffff
```

All `${ENV_VAR}` placeholders in `settings.yaml` are resolved from `.env` at runtime.

Additional config mechanisms:
- **`env_overrides`** — data-driven mapping of env vars to dotted config paths (supports `:int` / `:bool` type hints)
- **`env_overrides_list`** — list-based overrides for array config entries (e.g. `health_check.checks`)
- **Config path:** Set `SPHERE_CONFIG_PATH` to override the default config file location (falls back to `HSM_CONFIG_PATH`)

---

## How Tests Are Structured

```
tests/
├── test_data.py                           ← Test data dataclasses (KeyCeremonyData, etc.)
├── ui/
│   ├── conftest.py                        ← COM init, dependency hooks, failure screenshots
│   ├── e_admin/
│   │   ├── conftest.py                    ← App-specific fixtures (e_admin_driver, etc.)
│   │   ├── test_TC-37509_KeyCeremonyFIPS.py
│   │   ├── test_TC-37515_KeyCeremonyNonFIPS.py
│   │   ├── test_TC-37516_AddOperationUser.py
│   │   ├── test_TC-37517_HSMResetBySuperUser.py
│   │   ├── test_TC-37520_DeleteOperationUser.py
│   │   ├── test_TC-37522_BlockUser.py
│   │   ├── test_TC-37523_UnblockUser.py
│   │   ├── test_TC-37524_CustomerKeyCeremony.py
│   │   └── test_TC-XXXXX_CustomerKeyCeremonyImport.py
│   ├── cps/
│   │   ├── conftest.py                    ← CPS fixtures (factory-based)
│   │   ├── test_DP_with_CLI.py
│   │   ├── test_HL_BasicFct.py
│   │   ├── test_HL_BasicFct_with_CLI.py
│   │   └── test_HSM_Init_for_CPS.py
│   └── proxy/
│       └── conftest.py                    ← Scaffolded, ready to write tests
└── console/
    └── pkcs11/
        ├── test_pkcs11_sample.py
        ├── test_hsm_deprovisioning.py
        ├── test_hsm_operational_user_login.py
        ├── test_hsm_provisioning_in_fips_mode.py
        ├── test_hsm_provisioning_in_fips_mode_2_user.py
        └── test_hsm_provisioning_in_nonfips_mode.py
```

### Fixture Loading (Layered Conftest)

```mermaid
flowchart TB
    P["plugin/<br/><i>Auto-registered via pytest11</i><br/>config, evidence, console,<br/>log_collector, ui_app"]
    R["conftest.py<br/><i>Root</i>"]
    T["tests/ui/conftest.py<br/><i>COM init, dependency hooks,<br/>failure screenshots</i>"]
    U["tests/ui/e_admin/conftest.py<br/><i>e_admin_driver, window_monitor,<br/>collect_app_logs (9 tests)</i>"]
    C["tests/ui/cps/conftest.py<br/><i>cps_driver, window_monitor,<br/>collect_app_logs (4 tests)</i>"]

    P --> R --> T
    T --> U
    T --> C

    style P fill:#e17055,stroke:#fab1a0,color:#ffffff
    style U fill:#0984e3,stroke:#74b9ff,color:#ffffff
    style C fill:#00b894,stroke:#55efc4,color:#ffffff
```

Each conftest only loads when tests in that directory are selected — no unnecessary imports.

### Test File Convention

Tests use one of two patterns — **Flow-based** (preferred for complex workflows) or **Page Object** (for simpler tests):

**Flow-based pattern** (Key Ceremony, CKC, HSM Reset):

```python
@allure.epic("Sphere HSM Idemia - E2E Tests - E-Admin")
@allure.feature("Customer Key Ceremony")
@pytest.mark.e_admin
@pytest.mark.flow
class TestCustomerKeyCeremonyFlow:

    @pytest.fixture(autouse=True)
    def setup(self, e_admin_driver, evidence):
        self.driver = e_admin_driver
        self.evidence = evidence
        self.td = CustomerKeyCeremonyData.from_env()
        yield

    def test_customer_key_ceremony(self):
        ctx = FlowContext(self.driver, self.evidence, self.td)
        customer_key_ceremony_flow.run(ctx)
```

**Page Object pattern** (User management, simpler workflows):

```python
@allure.epic("Sphere HSM Idemia - E2E Tests - E-Admin")
@allure.feature("User Management")
@pytest.mark.e_admin
@pytest.mark.tcms(case_id=37516)
class TestAddOperationUser:

    @pytest.fixture(autouse=True)
    def setup(self, e_admin_driver, evidence):
        self.driver = e_admin_driver
        self.evidence = evidence
        yield

    def test_add_operation_user(self):
        login = LoginPage(self.driver, self.evidence)
        dashboard = login.connect_to_hsm(step_name="Connect to HSM")
        # ... test steps with evidence tracking
```

### Naming Convention

- **File**: `test_TC-{TCMS_ID}_{DescriptiveName}.py`
- **Class**: `Test{DescriptiveName}`
- **Method**: `test_{specific_scenario}`
- **Allure tags**: Map directly to TCMS bracket tags: `[E2E][eAdmin][Connect]`

---

## Reporting

### Allure Report

The primary reporting output — rich HTML reports with:

- Step-by-step execution with screenshots
- Pass/fail/skip/broken status per test
- Suite-level and feature-level grouping
- Attached evidence (logs, screenshots, app logs)
- Severity and priority labels
- Links to TCMS test cases

```bash
npx allure open evidence/allure-results    # View report (Allure 3)
```

### CI/CD Pipeline (Jenkins)

```mermaid
flowchart LR
    subgraph Jenkins
        direction LR
        CK["Checkout"] --> ST["Setup<br/><i>venv + deps</i>"]
        ST --> HC["Health Check"]
        HC --> RT["Run Tests<br/><i>pytest -m marker</i>"]
        RT --> AR["Allure Report<br/><i>generate HTML</i>"]
        AR --> PB["Publish<br/><i>artifacts + report</i>"]
    end

    RT -->|"results"| TCMS["Kiwi TCMS"]
    RT -->|"metrics"| GRAF["Grafana"]

    style Jenkins fill:#2d3436,stroke:#636e72,color:#dfe6e9
    style TCMS fill:#00b894,stroke:#55efc4,color:#ffffff
    style GRAF fill:#fdcb6e,stroke:#ffeaa7,color:#2d3436
```

### Kiwi TCMS Report

Test results synced back to TCMS TestRuns — visible in the TCMS web interface with:

- Per-case PASSED/FAILED/BLOCKED status
- Error details and evidence attachments on failure
- Coverage gap warnings for unautomated test cases

### Grafana Dashboard

Import `config/grafana-dashboard.json` for real-time metrics:

- Current run status (pass rate, duration, coverage)
- Historical trends across runs
- Per-test duration tracking
- Run comparison via dropdown selector

---

## Multi-VM Test Environment

```mermaid
graph TB
    subgraph CI["Jenkins Agent (Windows)"]
        FW["Test Framework<br/><i>pytest + pywinauto</i>"]
    end

    subgraph VM1["VM 1 — Admin"]
        EA["E-Admin App"]
        AG1["Remote Agent<br/><i>:5050</i>"]
    end

    subgraph VM2["VM 2 — Proxy"]
        PX["Proxy App"]
        AG2["Remote Agent<br/><i>:5050</i>"]
    end

    subgraph VM3["VM 3 — CPS"]
        CS["CPS App"]
    end

    subgraph Infra["Infrastructure"]
        HSM[("Sphere HSM<br/>Device")]
        LOKI["Loki<br/><i>Log aggregation</i>"]
        PROM["Prometheus<br/><i>Metrics</i>"]
    end

    FW -->|"UI automation"| EA
    FW -->|"HTTP commands"| AG1 & AG2
    FW -->|"UI automation"| CS
    EA & PX & CS -->|"PKCS#11 / API"| HSM

    VM1 & VM2 -->|"ship logs"| LOKI
    FW -->|"query logs"| LOKI
    FW -->|"push metrics"| PROM

    style CI fill:#2d3436,stroke:#636e72,color:#dfe6e9
    style HSM fill:#e94560,stroke:#e94560,color:#ffffff
    style Infra fill:#1a1a2e,stroke:#16213e,color:#e0e0e0
```

---

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Test Framework | pytest 7+ | Test execution, fixtures, markers, hooks |
| UI Automation | pywinauto | Windows desktop app control (WPF/WinForms) |
| Screenshots | mss + Pillow | Desktop and element capture |
| Reporting | Allure 3 | HTML test reports with evidence |
| Test Management | Kiwi TCMS | Bidirectional test case sync |
| Metrics | Prometheus + Grafana | Dashboard and trend visualization |
| Log Aggregation | Grafana Loki | Remote VM log collection |
| Configuration | PyYAML + python-dotenv | YAML config with env var substitution |
| CI/CD | Jenkins (Jenkinsfile) | Multi-platform pipeline execution |
| Language | Python 3.9+ (3.11 recommended) | Framework and test code |

---

## CLI Quick Reference

| Command | Description |
|---------|-------------|
| `pytest tests/ui/e_admin/ -v` | Run all E-Admin tests |
| `pytest -m smoke -v` | Run smoke tests only |
| `pytest -m "e_admin and critical"` | E-Admin critical tests |
| `pytest --kiwi-run-id=123` | Sync with TCMS TestRun #123 |
| `pytest --run-id sprint_42` | Tag run for Grafana |
| `pytest --smoke-gate` | Abort if smoke fails |
| `pytest --skip-health-check` | Skip environment checks |
| `pytest --co -v` | Dry run — list collected tests |
| `python scripts/inspect_app.py "App.exe"` | Discover UI element IDs |

---

## Getting Started

```mermaid
flowchart LR
    A["Install Python 3.11+<br/>Clone repo"] --> B["Run<br/>scripts/setup.bat"]
    B --> C["Configure<br/>.env"]
    C --> D["Verify<br/>pytest --co -v"]
    D --> E{"What next?"}
    E -->|"Run existing tests"| F["pytest -m e_admin -v"]
    E -->|"Write new tests"| G["Read COOKBOOK.md"]
    E -->|"Setup CI"| H["Read SETUP_GUIDE.md"]

    style A fill:#636e72,stroke:#b2bec3,color:#ffffff
    style D fill:#00b894,stroke:#55efc4,color:#ffffff
    style G fill:#0984e3,stroke:#74b9ff,color:#ffffff
```

| Step | Action | Guide |
|------|--------|-------|
| 1 | Install Python 3.11+, clone repo, run `scripts/setup.bat` | [SETUP_GUIDE.md](../SETUP_GUIDE.md) |
| 2 | Configure `.env` with HSM_IP, app paths | [SETUP_GUIDE.md](../SETUP_GUIDE.md) |
| 3 | Run existing tests | [README.md](../README.md) |
| 4 | Write tests for a new app (CPS/Proxy) | [COOKBOOK.md](../COOKBOOK.md) |
| 5 | Set up Jenkins CI pipeline | [SETUP_GUIDE.md](../SETUP_GUIDE.md) |
| 6 | Configure TCMS/Grafana (optional) | [SETUP_GUIDE.md](../SETUP_GUIDE.md) |
| 7 | Set up remote agents for multi-VM | [remote_agent_guide.md](remote_agent_guide.md) |

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **pytest plugin (auto-registered)** | Consumer repos get all fixtures/hooks by just installing the package — zero boilerplate |
| **Page Object Model** | Separates UI locators from test logic; one screen = one class |
| **`_step()` + evidence tracking** | Every action produces Allure steps with screenshots — no manual effort |
| **TCMS as source of truth** | Test procedures live in Kiwi TCMS (human-readable), automation code lives in Python (machine-executable) |
| **Flow/Step orchestration** | Complex ceremonies (20+ steps) are composed from reusable step factories. Steps share state via FlowContext, support retry/cleanup, and remain independently testable |
| **No BDD/Gherkin** | Complex HSM workflows (20-30 steps) don't fit 1:1 step definitions. `tracked_step` provides the same documentation value without the overhead |
| **Health checks before execution** | Fail fast with clear diagnostics if HSM is unreachable, instead of cryptic timeouts during tests |
| **Separated conftest per app** | `tests/ui/e_admin/conftest.py` only loads when running E-Admin tests — no unnecessary imports |
| **Environment-based config** | `.env` for secrets, `settings.yaml` for structure — safe for version control |
| **DriverProtocol (duck typing)** | Enables injection of non-pywinauto drivers (Playwright, mock) without modifying core |
| **EAdminBasePage split** | New apps inherit clean `BasePage` without E-Admin navigation methods |
| **Export artifacts to JSON** | CKC Generate & Export saves key data to `output/ckc_export.json` for reuse by Import tests — decouples test execution order |

---

## Glossary

| Term | Meaning |
|------|---------|
| **E-Admin** | HSM Administration Application (WinForms desktop app) |
| **CPS** | Certificate Provisioning System |
| **Proxy** | HSM Proxy Application |
| **PKCS#11** | Cryptographic Token Interface Standard — the API HSMs expose |
| **POM** | Page Object Model — design pattern for UI test automation |
| **TCMS** | Test Case Management System (Kiwi TCMS) |
| **Evidence** | Screenshots, logs, and attachments collected during test execution |
| **tracked_step** | Context manager that creates an Allure step with auto-screenshot |
| **Flow** | Composable sequence of Steps executed via FlowContext — supports retry, cleanup, continue-on-failure |
| **Step** | Reusable action factory that takes a FlowContext — the building block of Flows |
| **FlowContext** | Runtime context carrying driver, evidence, test data, and shared state across Steps |
| **CKC** | Customer Key Ceremony — key generation/export/import workflow in E-Admin |
| **KCP** | Key Custodian Party — user role responsible for key components during CKC |
| **Smoke Gate** | Mechanism to abort test suite if critical smoke tests fail |
| **Health Check** | Pre-execution verification that the test environment is ready |
| **UIDriver** | Framework's pywinauto wrapper with popup handling and retry logic |
| **ConsoleRunner** | Framework's subprocess wrapper for CLI tool execution |
| **BasePage** | Generic WinForms base page with `_step()`, `dismiss_ok` — no app-specific methods |
| **EAdminBasePage** | E-Admin-specific base page with sidebar navigation and T&C acceptance |
| **DriverProtocol** | Runtime-checkable Protocol defining the driver interface for dependency injection |
