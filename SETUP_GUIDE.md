# Setup Guide

## Prerequisites

### Windows (UI + Console tests)

| # | Software | Version | Install | Verify |
|---|----------|---------|---------|--------|
| 1 | Python | >= 3.9 (3.11 recommended) | https://python.org/downloads | `py --list` |
| 2 | Git | any | https://git-scm.com/download/win | `git --version` |
| 3 | Allure CLI | 3.x (recommended) or 2.x | `npm install -g allure` | `npx allure --version` |
| 4 | Node.js | >= 18 | https://nodejs.org | `node --version` |

> `pywinauto` is installed automatically via pip. Allure 3 uses Node.js (no Java needed).
> If using Allure 2, also install Java JRE >= 11.

### Linux (Console/PKCS#11 tests only)

| # | Software | Version | Install | Verify |
|---|----------|---------|---------|--------|
| 1 | Python | >= 3.9 | `sudo apt install python3 python3-pip python3-venv` | `python3 --version` |
| 2 | Git | any | `sudo apt install git` | `git --version` |
| 3 | Allure CLI | 3.x | `npm install -g allure` | `npx allure --version` |
| 4 | Node.js | >= 18 | `sudo apt install nodejs npm` | `node --version` |

### Python Side-by-Side Install

If your PC has Python 3.8, install a newer version alongside it:

```cmd
:: Windows — download Python 3.11 from python.org, both versions coexist
py -3.11 --version        # New version
py --list                 # Shows all installed versions
```

```bash
# Linux
sudo apt install python3.11 python3.11-venv
```

The setup scripts auto-detect the best Python version.

---

## First-Time Setup

### 1. Clone the Repository

```bash
git clone <your-gitlab-url>/sphere-e2e-test-framework.git
cd sphere-e2e-test-framework
```

### 2. Run Setup Script

```cmd
:: Windows
scripts\setup.bat
```

```bash
# Linux
chmod +x scripts/setup.sh && ./scripts/setup.sh
```

This creates a Python venv, installs all dependencies, and creates evidence directories.

### 3. Configure Environment

Copy `.env.example` to `.env` and fill in your values:

```bash
HSM_IP=10.66.1.10
HSM_PORT=52000
E_ADMIN_PATH=C:\SPHERE_HSM\Admin Application\AdminApp.exe
E_ADMIN_APP_LOGS=C:\SPHERE_HSM\Admin Application\AppLogs

# Optional: override config file location (default: config/settings.yaml)
SPHERE_CONFIG_PATH=C:\custom\path\settings.yaml
```

> **Config path resolution:** The framework looks for `SPHERE_CONFIG_PATH` first.
> If not set, it falls back to `HSM_CONFIG_PATH` for backward compatibility.

### 4. Verify

```bash
# Activate venv
venv\Scripts\activate.bat         # Windows
source venv/bin/activate          # Linux

# Check test collection (should list tests without errors)
pytest tests/ui/e_admin/ --co -v

# Run smoke tests
pytest -m smoke -v
```

### 5. View Results

```bash
# Allure 3 (recommended)
npx allure open evidence/allure-results

# Allure 2 (legacy, requires Java)
allure serve evidence/allure-results
```

---

## Jenkins CI Setup

### 1. Install Jenkins Plugins

- **Allure Jenkins Plugin** — report generation
- **Pipeline Plugin** — Jenkinsfile support (usually pre-installed)

### 2. Configure Credentials (if using Kiwi TCMS)

Jenkins > Manage Jenkins > Credentials > Add:

| ID | Type | Value |
|----|------|-------|
| `tcms-api-url` | Secret text | `https://kiwi.yourcompany.com/xml-rpc/` |
| `tcms-username` | Secret text | TCMS username |
| `tcms-password` | Secret text | TCMS password |

### 3. Create Pipeline Job

1. New Item > Pipeline
2. Pipeline > Definition: "Pipeline script from SCM"
3. SCM: Git > your GitLab repo URL
4. Script Path: `Jenkinsfile`
5. Ensure agent labels: `windows` for Windows agent, `linux` for Linux agent

---

## Kiwi TCMS Setup (Optional)

Set environment variables in `.env`:

```bash
TCMS_API_URL=https://kiwi.yourcompany.com/xml-rpc/
TCMS_USERNAME=your_user
TCMS_PASSWORD=your_pass
```

### Bidirectional Mode

Run tests linked to a specific TCMS TestRun:

```bash
pytest --kiwi-run-id=123
```

The framework pulls test cases from the run, executes matched tests, and pushes
PASSED/FAILED/BLOCKED back to TCMS.

### Push-Only Mode

Auto-create a new TestRun and push all results:

```bash
pytest --kiwi-create-run
```

Requires `plan_id` in `config/settings.yaml`:

```yaml
kiwi_tcms:
  enabled: true
  plan_id: 1
  auto_create_run: true
```

---

## Grafana / Prometheus Setup (Optional)

### 1. Start Prometheus Pushgateway

```bash
docker run -d -p 9091:9091 prom/pushgateway
```

### 2. Configure Prometheus

Add to `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'pushgateway'
    static_configs:
      - targets: ['localhost:9091']
```

### 3. Import Grafana Dashboard

Grafana > Dashboards > Import > Upload `config/grafana-dashboard.json`

### 4. Enable in Framework

Set in `.env`:

```bash
PUSHGATEWAY_URL=http://your-pushgateway-host:9091
```

And in `config/settings.yaml`:

```yaml
metrics:
  enabled: true
  metric_prefix: "hsm"       # Prefix for all Prometheus metric names (default: "e2e")
  suite_name: "hsm"           # Label value for the suite dimension
```

### 5. Tag Test Runs

```bash
pytest tests/ -v --run-id sprint_42
```

Each `--run-id` creates an isolated data series in Grafana. The dashboard dropdown
lets you select individual runs or view all runs on trend charts.

---

## Quick Reference Commands

```bash
# Activate virtual environment
source venv/bin/activate          # Linux
venv\Scripts\activate.bat         # Windows

# Run tests
pytest                            # All tests
pytest -m ui -v                   # UI tests only
pytest -m console -v              # Console tests only
pytest -m "e_admin and smoke" -v  # E-Admin smoke
pytest -k "KeyCeremony" -v        # Filter by keyword

# Run specific test
pytest tests/ui/e_admin/test_TC-37509_KeyCeremonyFIPS.py -v

# Inspect UI elements
python scripts/inspect_app.py "C:\Path\To\App.exe"
python scripts/inspect_app.py --title "App Title" --interactive

# View report
npx allure open evidence/allure-results
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Python version too old | Install Python 3.11 side-by-side (see above). Setup script auto-detects. |
| `ModuleNotFoundError: pywinauto` | Run on Windows, or: `pip install pywinauto` |
| `ModuleNotFoundError: sphere_e2e_test_framework` | Run `pip install -e .` in the framework repo |
| UI tests skipped on Windows | Check `backend` in settings.yaml. Try `"win32"` instead of `"uia"` |
| Cannot find window | Check `class_name` pattern in settings.yaml. Use inspect_app.py to verify |
| Allure report empty | Check `evidence/allure-results/` has JSON files |
| `allure serve` not working (v3) | Allure 3 uses `npx allure open` instead of `allure serve` |
| ANSI color codes in logs | `--color=no` is set in pyproject.toml. Override locally: `pytest --color=yes` |
| Kiwi TCMS connection failed | Check `.env`: `TCMS_API_URL`, `TCMS_USERNAME`, `TCMS_PASSWORD` |
| Health check fails | Verify HSM is reachable. Skip with `pytest --skip-health-check` |
| Jenkins pipeline fails | Ensure Python is in PATH on agent. Check agent labels match Jenkinsfile |
