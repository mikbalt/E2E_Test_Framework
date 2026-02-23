# HSM Test Framework - Setup Guide

## Python Version Requirement

This framework requires **Python 3.9+**. Python 3.8 is EOL (end-of-life since Oct 2024)
and several dependencies no longer support it.

**If your PC has Python 3.8 installed**, install a newer version **side-by-side**:

### Windows (side-by-side install)
```
1. Download Python 3.11 from https://python.org/downloads
2. During install: check "Add Python to PATH" (optional if py launcher exists)
3. Both Python 3.8 and 3.11 will coexist
4. The setup script auto-detects the best version via the `py` launcher
```

Verify:
```cmd
py -3.11 --version        # Should show Python 3.11.x
py -3.8 --version         # Your old version still works
py --list                 # Shows all installed versions
```

### Linux (side-by-side install)
```bash
# Ubuntu/Debian
sudo apt install python3.11 python3.11-venv

# RHEL/CentOS
sudo dnf install python3.11

# macOS
brew install python@3.11
```

Verify:
```bash
python3.11 --version      # New version
python3.8 --version       # Old version still works
```

The `scripts/setup.sh` and `scripts/setup.bat` will **automatically find** the best
Python version on your system. You don't need to change PATH or remove 3.8.

> **venv is not heavy.** It's just a folder (~30MB) with a Python copy and isolated
> packages. Zero runtime overhead. Zero CPU/RAM cost. It's the Python standard for
> production environments.

---

## Prerequisites

### Windows (for UI + Console tests)

| # | Software | Version | How to Install | Verify |
|---|----------|---------|----------------|--------|
| 1 | Python | >= 3.9 (3.11 recommended) | https://python.org/downloads → check "Add to PATH" | `py --list` |
| 2 | Git | any | https://git-scm.com/download/win | `git --version` |
| 3 | pip | latest | comes with Python | `pip --version` |
| 4 | Allure CLI | >= 2.x | `scoop install allure` or https://github.com/allure-framework/allure2/releases | `allure --version` |
| 5 | Java (JRE) | >= 11 | https://adoptium.net (needed by Allure CLI) | `java --version` |

> **Note:** `pywinauto` (for UI tests) is installed automatically via pip. No manual install needed.

### Linux (for Console/PKCS11 tests only)

| # | Software | Version | How to Install | Verify |
|---|----------|---------|----------------|--------|
| 1 | Python | >= 3.9 | `sudo apt install python3 python3-pip python3-venv` | `python3 --version` |
| 2 | Git | any | `sudo apt install git` | `git --version` |
| 3 | Allure CLI | >= 2.x | `sudo snap install allure` or manual download | `allure --version` |
| 4 | Java (JRE) | >= 11 | `sudo apt install default-jre` | `java --version` |

### Infrastructure (already available per your setup)

| Service | Purpose | Required? |
|---------|---------|-----------|
| GitLab | Source code repository | Yes |
| Jenkins | CI/CD pipeline runner | Yes (needs Windows + Linux agents) |
| Kiwi TCMS | Test case management & reporting | Optional (enable in settings.yaml) |
| Grafana + Prometheus | Test metrics dashboard | Optional (enable in settings.yaml) |

---

## Step-by-Step: First Time Setup

### 1. Clone the Repository

```bash
# On the new PC
git clone <your-gitlab-url>/hsm-test-framework.git
cd hsm-test-framework
```

### 2. Run Setup Script

**Windows:**
```cmd
scripts\setup.bat
```

**Linux/macOS:**
```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

This will:
- Create a Python virtual environment (`venv/`)
- Install all dependencies
- Create evidence directories

### 3. Configure Your Application

Edit `config/settings.yaml`:

```yaml
apps:
  hsm_admin:
    path: "C:\\actual\\path\\to\\YourApp.exe"   # <-- change this
    title: "Your App Window Title*"               # <-- change this
    backend: "uia"                                # uia=WPF, win32=WinForms

console_tools:
  pkcs11_native:
    command_windows: "C:\\actual\\path\\pkcs11-tool.exe"  # <-- change this
    command_linux: "/usr/bin/pkcs11-tool"                  # <-- change this
```

### 4. Run a Quick Test

**Windows (smoke test with Calculator as demo):**
```cmd
scripts\run_tests.bat smoke
```

**Linux (console tests only, UI auto-skipped):**
```bash
./scripts/run_tests.sh smoke
```

### 5. View Results

```bash
# Allure report (if Allure CLI is installed)
allure open evidence/allure-report

# Or just check the raw files
ls evidence/
```

---

## Step-by-Step: Setting Up a New Consumer Test Repo

For testing a **different application** using this framework as a base:

### 1. Create a New Repo

```bash
mkdir my-app-tests && cd my-app-tests
git init
```

### 2. Copy the Template

Copy everything from `examples/consumer-repo-template/` into your new repo:

```bash
cp -r /path/to/hsm-test-framework/examples/consumer-repo-template/* .
cp /path/to/hsm-test-framework/examples/consumer-repo-template/.* . 2>/dev/null
```

### 3. Edit `requirements.txt`

Replace the GitLab URL with your actual repo URL:

```
hsm-test-framework @ git+https://gitlab.yourcompany.com/qa/hsm-test-framework.git
```

### 4. Install and Run

```bash
python3 -m venv venv
source venv/bin/activate        # Linux
# or: venv\Scripts\activate.bat  # Windows

pip install -r requirements.txt
```

### 5. Write Your Tests

```python
from hsm_test_framework import UIDriver, ConsoleRunner, Evidence, StepTracker
# All fixtures (config, evidence, console, ui_app) are available automatically
```

---

## Jenkins Setup

### 1. Install Required Jenkins Plugins

- **Allure Jenkins Plugin** - for report generation
- **JUnit Plugin** - for test result tracking (usually pre-installed)
- **Pipeline Plugin** - for Jenkinsfile support (usually pre-installed)

### 2. Configure Jenkins Credentials (if using Kiwi TCMS)

Go to Jenkins → Manage Jenkins → Credentials → Add:

| ID | Type | Value |
|----|------|-------|
| `tcms-api-url` | Secret text | `https://kiwi.yourcompany.com/xml-rpc/` |
| `tcms-username` | Secret text | your TCMS username |
| `tcms-password` | Secret text | your TCMS password |

### 3. Create Jenkins Job

1. New Item → Pipeline
2. Pipeline → Definition: "Pipeline script from SCM"
3. SCM: Git → Repository URL: your GitLab repo URL
4. Script Path: `Jenkinsfile`
5. Save and Build

### 4. Agent Labels

Ensure your Jenkins agents have the correct labels:
- Windows agent: label = `windows`
- Linux agent: label = `linux`

---

## Grafana Setup (Optional)

### 1. Install Prometheus Pushgateway

```bash
# Docker
docker run -d -p 9091:9091 prom/pushgateway

# Or download binary from https://github.com/prometheus/pushgateway/releases
```

### 2. Configure Prometheus to Scrape Pushgateway

Add to `prometheus.yml`:
```yaml
scrape_configs:
  - job_name: 'pushgateway'
    static_configs:
      - targets: ['localhost:9091']
```

### 3. Import Dashboard to Grafana

1. Grafana → Dashboards → Import
2. Upload `config/grafana-dashboard.json`
3. Select your Prometheus datasource
4. Save

### 4. Enable in Framework

Edit `config/settings.yaml`:
```yaml
metrics:
  enabled: true
  pushgateway_url: "http://your-pushgateway-host:9091"
```

---

## Kiwi TCMS Setup (Optional)

### 1. Create Test Plan in Kiwi TCMS

1. Log in to Kiwi TCMS
2. Create a Product (e.g., "HSM Suite")
3. Create a Test Plan under that product
4. Note the Plan ID

### 2. Enable in Framework

Edit `config/settings.yaml`:
```yaml
kiwi_tcms:
  enabled: true
  url: "https://kiwi.yourcompany.com"
  product: "HSM Suite"
  plan_id: 1          # <-- your plan ID
  auto_create_run: true
```

Set environment variables (or `.env` file):
```bash
export TCMS_API_URL=https://kiwi.yourcompany.com/xml-rpc/
export TCMS_USERNAME=your_user
export TCMS_PASSWORD=your_pass
```

---

## Quick Reference: Common Commands

```bash
# Activate virtual environment
source venv/bin/activate          # Linux/macOS
venv\Scripts\activate.bat         # Windows

# Run all tests
pytest

# Run by marker
pytest -m smoke                   # Quick smoke tests
pytest -m ui                      # Windows UI tests only
pytest -m console                 # Console/CLI tests only
pytest -m pkcs11                  # PKCS#11 tests only
pytest -m regression              # Full regression

# Run specific test file
pytest tests/ui/test_sample_app.py -v

# Run with Allure report
pytest --alluredir=evidence/allure-results
allure serve evidence/allure-results     # Live preview
allure generate evidence/allure-results  # Static HTML

# Debug: print UI control tree of an app
python -c "
from hsm_test_framework import UIDriver
d = UIDriver('calc.exe', title='Calculator')
d.start()
d.print_control_tree(depth=3)
d.close()
"

# Upgrade the framework in a consumer repo
pip install --upgrade git+https://gitlab.yourcompany.com/qa/hsm-test-framework.git
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Python 3.8 detected / version too old | Install Python 3.11 side-by-side (see top of this guide). Don't remove 3.8. |
| `ModuleNotFoundError: pywinauto` | Run on Windows, or install: `pip install pywinauto` |
| `ModuleNotFoundError: hsm_test_framework` | Run `pip install -e .` (in framework repo) or `pip install -r requirements.txt` (in consumer repo) |
| UI tests skipped on Windows | Check `backend` in settings.yaml. Try `"win32"` instead of `"uia"` |
| Cannot find window | Check `title` pattern in settings.yaml. Use `*` wildcard. Run `print_control_tree()` to debug |
| Allure report empty | Ensure `--alluredir=evidence/allure-results` is passed. Check `evidence/allure-results/` has JSON files |
| Kiwi TCMS connection failed | Verify env vars: `TCMS_API_URL`, `TCMS_USERNAME`, `TCMS_PASSWORD` |
| Metrics not showing in Grafana | Check Pushgateway is running: `curl http://localhost:9091/metrics` |
| Jenkins pipeline fails at setup | Ensure Python is in PATH on the agent. Check agent labels match Jenkinsfile |
