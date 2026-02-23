# HSM Test Framework

Reusable, cross-platform E2E test framework for Windows desktop applications and console-based tools (PKCS#11 via Golang, Java, C++).

Designed as a **shared base package** — install once, use across multiple test repositories.

---

## What's Inside

### Core Framework (`hsm_test_framework/`)

| Module | What It Does |
|--------|-------------|
| `ui_driver.py` | Windows UI automation via pywinauto. Supports WPF, WinForms, Win32. Wraps common actions: click, type, get text, select menu/tab/combobox. |
| `console_runner.py` | Subprocess wrapper for CLI tools. Captures stdout/stderr/duration. Built-in assertions (`assert_success`, `assert_output_contains`). Cross-platform path resolution. |
| `evidence.py` | Collects screenshots (per step + on failure), logs, and text output. Auto-attaches to Allure reports. `StepTracker` context manager for step-by-step evidence. |
| `kiwi_tcms.py` | Reports test results to Kiwi TCMS. Auto-creates test runs, syncs pass/fail per test case. |
| `grafana_push.py` | Pushes metrics (pass rate, duration, trends) to Prometheus Pushgateway for Grafana dashboards. |
| `plugin.py` | pytest plugin (auto-registered via `pytest11` entry point). Provides fixtures, platform guards, screenshot-on-failure, TCMS and Grafana hooks. Consumer repos get everything for free. |

### Sample Tests (`tests/`)

| File | Purpose |
|------|---------|
| `tests/ui/test_sample_app.py` | Demo: opens Windows Calculator, clicks buttons, verifies result. Template for HSM Admin app included. |
| `tests/console/test_pkcs11_sample.py` | Demo: runs PKCS#11 tools (native, Go, Java, C++). Cross-platform with `resolve_platform_config()`. |

### CI/CD & Infrastructure

| File | Purpose |
|------|---------|
| `Jenkinsfile` | Multi-platform pipeline. Runs Windows + Linux agents in parallel, merges Allure results. |
| `config/settings.yaml` | Central config: app paths (per-platform), tool paths, evidence, TCMS, Grafana settings. |
| `config/grafana-dashboard.json` | Ready-to-import Grafana dashboard with pass rate gauge, duration trends, test history. |
| `scripts/setup.bat` / `setup.sh` | One-command setup. Auto-detects best Python version (supports side-by-side installs). |
| `scripts/run_tests.bat` / `run_tests.sh` | Quick test runner with marker selection, Allure report generation. |

### Consumer Repo Template (`examples/consumer-repo-template/`)

Minimal boilerplate for a **new test repository** that uses this framework as a dependency. Contains `requirements.txt`, `conftest.py`, `config/settings.yaml`, sample tests, and `Jenkinsfile` — ready to copy and customize.

---

## Architecture

```
                    ┌─────────────────────────────────┐
                    │   hsm-test-framework (GitLab)   │
                    │   pip-installable package        │
                    └──────────┬──────────────────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
    ┌─────────▼──────┐ ┌──────▼───────┐ ┌──────▼───────┐
    │ hsm-admin-tests│ │ pkcs11-tests │ │ other-tests  │
    │ (consumer repo)│ │(consumer repo)│ │(consumer repo)│
    └────────────────┘ └──────────────┘ └──────────────┘

Each consumer repo:
  - pip install git+<this-repo>
  - Gets all fixtures & hooks automatically
  - Only writes its own tests + config/settings.yaml
```

## Platform Support

| Component | Windows | Linux |
|-----------|---------|-------|
| UI tests (pywinauto) | Runs | Auto-skipped |
| Console tests (PKCS#11) | Runs | Runs |
| Evidence / screenshots | Runs | Runs (if display available) |
| Allure reporting | Runs | Runs |
| Kiwi TCMS | Runs | Runs |
| Grafana metrics | Runs | Runs |
| Jenkins pipeline | `bat` commands | `sh` commands |

## Quick Start

```bash
# 1. Clone
git clone <gitlab-url>/hsm-test-framework.git
cd hsm-test-framework

# 2. Setup (auto-detects Python, creates venv, installs deps)
scripts/setup.bat        # Windows
./scripts/setup.sh       # Linux/macOS

# 3. Configure
#    Edit config/settings.yaml with your app/tool paths

# 4. Run
scripts/run_tests.bat smoke     # Windows
./scripts/run_tests.sh smoke    # Linux
```

## Using as a Base in Another Repo

```bash
# In your new test repo
pip install git+https://gitlab.yourcompany.com/qa/hsm-test-framework.git
```

```python
# In your test files
from hsm_test_framework import UIDriver, ConsoleRunner, Evidence, StepTracker

# Fixtures available automatically: config, evidence, console, ui_app
```

See `examples/consumer-repo-template/` for a complete working example.

## Documentation

- **[SETUP_GUIDE.md](SETUP_GUIDE.md)** — Full setup instructions, prerequisites, Jenkins/Grafana/TCMS configuration
- **[TODO.md](TODO.md)** — Roadmap and future improvement ideas
- **[config/settings.yaml](config/settings.yaml)** — Configuration reference with comments
