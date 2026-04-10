# Ankole Framework

Multi-driver E2E test framework with full observability stack. Supports 4 automation engines (Playwright, pywinauto, httpx, subprocess) with Protocol-based driver abstraction.

---

## Architecture Highlights

- **Multi-driver**: Web (Playwright), Desktop (pywinauto), API (httpx), CLI (subprocess)
- **Design patterns**: Page Object Model, Flow/Step orchestration, Fixture factories, Strategy pattern
- **Observability**: Grafana + Prometheus + Loki + Allure (all Dockerized)
- **Infrastructure**: One `docker-compose up` for complete environment
- **CI/CD**: GitHub Actions with matrix builds and artifact collection
- **Multi-layer testing**: Unit, API, Web E2E, CLI, Desktop
- **TCMS integration**: Bidirectional Kiwi TCMS sync

---

## Quick Start

```bash
# 1. Start infrastructure + sample apps
docker-compose up -d

# 2. Install framework
pip install -e ".[all]"
playwright install chromium

# 3. Run tests
pytest tests/unit/ -v                    # Framework core tests
pytest tests/api/ -v                     # API tests
pytest tests/web/ -v                     # Web UI tests
pytest tests/cli/ -v                     # CLI tests
pytest tests/ -v --alluredir=evidence/allure-results  # Full suite

# 4. View results
# Grafana:  http://localhost:3000
# Allure:   http://localhost:5050 (with --profile reporting)
```

---

## Project Structure

```
ankole/                           # Framework package
  driver/
    base.py                       # Protocol definitions (Driver, Web, API)
    ui_driver.py                  # pywinauto desktop driver
    web_driver.py                 # Playwright web driver
    api_driver.py                 # httpx API driver
    console_runner.py             # Subprocess CLI runner
    evidence.py                   # Screenshots & step tracking
    grafana_push.py               # Prometheus metrics push
    health_check.py               # Pre-execution environment checks
    kiwi_tcms.py                  # Kiwi TCMS integration
    ...
  plugin/                         # Pytest plugin (auto-registered)
    config.py, fixtures.py, hooks.py, metrics.py, kiwi_hooks.py
  pages/
    base_page.py                  # Generic page object base
    web/                          # Playwright page objects
      login_page.py, dashboard_page.py, member_management_page.py
      role_management_page.py, project_approval_page.py
  flows/
    base.py                       # FlowContext, Step, Flow engine
    workspace/                    # Pre-composed workspace flows
  steps/workspace/                # Reusable step factories
  testing/                        # Conftest utilities & fixture factories

tests/
  web/                            # Playwright web UI tests
  api/                            # httpx API tests
  cli/                            # CLI subprocess tests
  desktop/                        # pywinauto desktop tests
  unit/                           # Framework unit tests

sample_apps/                      # Docker target applications
  web_app/                        # Flask + Bootstrap 5
  api/                            # FastAPI REST API
  cli/                            # Click CLI tool
  db/init.sql                     # PostgreSQL schema + seeds

config/
  settings.yaml                   # Main configuration
  settings.docker.yaml            # Docker-specific overrides
  prometheus.yml, loki-config.yml, promtail-config.yml
  grafana-dashboard.json          # Pre-built Grafana dashboard

docker-compose.yml                # Full stack
.github/workflows/ci.yml          # GitHub Actions CI
```

---

## Sample Applications

The `sample_apps/` directory contains three target applications that share a PostgreSQL database:

| App | Technology | Port | Description |
|-----|-----------|------|-------------|
| **Web App** | Flask + Jinja2 + Bootstrap 5 | 5000 | Workspace management UI |
| **REST API** | FastAPI + JWT | 8000 | REST API with full CRUD |
| **CLI** | Python Click | N/A | CLI calling the REST API |

### Domain: Workspace Management

- **Member Management**: CRUD + Suspend/Reactivate
- **Role Management**: CRUD with permissions
- **Project Approval Workflow**: Multi-step approval (3 approvers)

---

## Driver Architecture

```
           DriverProtocol              WebDriverProtocol          APIDriverProtocol
               (desktop)                    (web)                      (api)
                  |                          |                          |
              UIDriver                   WebDriver                  APIDriver
            (pywinauto)               (Playwright)                  (httpx)
```

All drivers follow the Protocol pattern for structural typing. Page objects accept any compatible driver.

---

## Flow/Step Orchestration

```python
from ankole.flows.base import FlowContext, Step, Flow

ctx = FlowContext(driver, evidence, test_data)
flow = Flow("Approve Project", [
    Step("Login", login_action),
    Step("Create Project", create_action),
    Step("Approve Step 1", approve_action, retries=2),
])
flow.run(ctx)
```

Flows compose with `+` operator:

```python
combined = login_flow + create_member_flow + verify_flow
combined.run(ctx)
```

---

## Configuration

Settings are loaded from `config/settings.yaml` with environment variable overrides:

```yaml
workspace:
  web:
    base_url: "${WORKSPACE_WEB_URL}"
    browser: "chromium"
    headless: true
  api:
    base_url: "${WORKSPACE_API_URL}"
    timeout: 30
```

Override via env vars or `ANKOLE_CONFIG_PATH`:

```bash
export WORKSPACE_WEB_URL=http://localhost:5000
export WORKSPACE_API_URL=http://localhost:8000
```

---

## License

MIT
