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

## Step-by-Step: Setting Up a PKCS#11 Consumer Repo

For wrapping **existing PKCS#11 tests** (Java, C++, Go, Google Test):

### 1. Copy the PKCS#11 Template

```bash
cp -r /path/to/hsm-test-framework/examples/pkcs11-consumer-template/ /path/to/pkcs11-tests/
cd /path/to/pkcs11-tests/
```

### 2. Place Your Binaries and Source

```
bin/                          # Put pre-compiled binaries here
  pkcs11-keygen.jar           # Java JAR (ready to run)
  pkcs11_encrypt.exe          # C++ executable (ready to run)

src/                          # Put source code here (if needs compilation)
  java/signing/pom.xml        # Java Maven project
  go/slot/main.go             # Go source
  cpp/gtest_crypto/Makefile   # Google Test + Makefile
```

### 3. Configure `settings.yaml`

Edit `config/settings.yaml` — set paths and log locations for each tool:

```yaml
console_tools:
  pkcs11_java_keygen:
    command_windows: "bin\\pkcs11-keygen.jar"
    command_linux: "bin/pkcs11-keygen.jar"
    needs_build: false
    log_path_linux: "logs/java_keygen.log"     # <-- tool's own log file

  pkcs11_cpp_encrypt:
    command_windows: "bin\\pkcs11_encrypt.exe"
    command_linux: "bin/pkcs11_encrypt"
    needs_build: false
    log_dir_linux: "logs/cpp/"                 # <-- or a directory of logs
    log_pattern: "*.log"

  pkcs11_gtest_crypto:
    command_linux: "bin/pkcs11_gtest_crypto"
    needs_build: true
    makefile_dir: "src/cpp/gtest_crypto"
    gtest_xml_linux: "evidence/gtest_results.xml"  # <-- GTest XML report
```

### 4. Install and Build

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Build source code (Java/Go/GTest)
chmod +x scripts/build.sh
./scripts/build.sh
```

### 5. Run Tests

```bash
# Run all PKCS#11 tests
./scripts/run_tests.sh

# Run by language
./scripts/run_tests.sh java        # Java tests only
./scripts/run_tests.sh cpp         # C++ tests only
./scripts/run_tests.sh go_test     # Go tests only
./scripts/run_tests.sh gtest       # Google Test only

# Build + test in one command
./scripts/run_tests.sh build_and_test
```

### 6. Log Collection

The framework **automatically collects** each tool's log files:

| Config Key | What It Does |
|-----------|-------------|
| `log_path_linux` / `log_path_windows` | Collects a single log file |
| `log_dir_linux` / `log_dir_windows` | Collects all files from a directory |
| `log_pattern` | File pattern for directory (default: `*.log`) |
| `gtest_xml_linux` / `gtest_xml_windows` | Parses GTest XML and creates summary |

All collected logs are attached to the Allure report automatically.

You can also monitor logs in real-time during test execution:

```python
with log_collector.monitor("/path/to/app.log") as mon:
    result = console.run_executable(exe_path=tool["command"], args=["--test"])
# mon.captured contains only lines written during execution
log_collector.collect_text(mon.captured, "runtime_log")
```

### 7. How It Works (The Wrapper Concept)

Python does NOT replace your Java/C++/Go code. It **wraps** them:

```
Python Wrapper                    Your Existing Code
─────────────────                 ──────────────────
1. [Optional] Build               Java/C++/Go source unchanged
2. Run binary via subprocess      Binary runs normally
3. Capture stdout + stderr        Output captured for evidence
4. Collect log files              Tool's own logs attached to report
5. Assert exit code + output      Validate results
6. Attach to Allure report        Evidence in HTML report
```

### Available PKCS#11 Markers

| Marker | What it runs |
|--------|-------------|
| `java` | Java JAR-based PKCS#11 tests |
| `cpp` | C++ native executable tests |
| `go_test` | Go compiled binary tests |
| `gtest` | Google Test (C++) suite tests |
| `pkcs11` | All PKCS#11 tests (any language) |
| `needs_build` | Tests that require compilation first |
| `smoke` | Quick verification tests |

---

## Running Tests Per-Part

By default, `run_tests.bat` or `pytest` runs **everything**. To run step by step:

### Via run script

```cmd
REM Windows: run UI tests first, then console tests
scripts\run_tests.bat ui
scripts\run_tests.bat console

REM Or chain them (console only runs if UI passes):
scripts\run_tests.bat ui && scripts\run_tests.bat console
```

```bash
# Linux: same pattern
./scripts/run_tests.sh console
./scripts/run_tests.sh pkcs11
```

### Via pytest directly

```bash
# Activate venv first
venv\Scripts\activate.bat         # Windows
source venv/bin/activate          # Linux

# Run by marker
pytest -m ui                      # Windows UI tests only
pytest -m console                 # Console/CLI tests only
pytest -m pkcs11                  # PKCS#11 tests only
pytest -m smoke                   # Quick smoke tests (UI + console)
pytest -m regression              # Full regression

# Run a specific test file
pytest tests/ui/test_sample_app.py -v

# Run a specific test class
pytest tests/ui/test_sample_app.py::TestCalculatorDemo -v

# Run a single test method
pytest tests/ui/test_sample_app.py::TestCalculatorDemo::test_basic_addition -v

# Run with keyword filter
pytest -k "pkcs11 and not java" -v
```

### Available markers (defined in pyproject.toml)

| Marker | What it runs | Platform |
|--------|-------------|----------|
| `ui` | Windows UI automation tests | Windows only (auto-skipped on Linux) |
| `console` | Console/CLI tests | Windows + Linux |
| `pkcs11` | PKCS#11 specific tests | Windows + Linux |
| `smoke` | Quick verification tests | Both |
| `regression` | Full regression suite | Both |

---

## Discovering UI Element IDs

Before writing UI tests, you need to know the **button names**, **automation IDs**,
and **control types** of your application. Use the included inspector tool:

### Quick Inspect (launch app and scan)

```cmd
REM Inspect Windows Calculator
python scripts\inspect_app.py "calc.exe"

REM Inspect your app by path
python scripts\inspect_app.py "C:\Program Files\YourApp\App.exe"

REM Inspect an already running app by window title
python scripts\inspect_app.py --title "My Application"
```

### Save to File (for reference while writing tests)

```cmd
python scripts\inspect_app.py --title "Calculator" --output controls.txt
```

### Deep Scan (more nested levels)

```cmd
python scripts\inspect_app.py --title "Calculator" --depth 5
```

### Interactive Mode (hover to identify)

```cmd
python scripts\inspect_app.py --title "Calculator" --interactive
```
Move your mouse over elements in the app — the terminal prints the element info in real time.

### Try Different Backends

If no elements are found, switch the backend:
```cmd
REM uia = WPF / modern apps (default)
python scripts\inspect_app.py --title "My App" --backend uia

REM win32 = WinForms / classic apps
python scripts\inspect_app.py --title "My App" --backend win32
```

### Reading the Output

The inspector outputs three sections:

**1. CLICKABLE ELEMENTS** — buttons, menus, tabs, checkboxes
```
Type                 Name/Title              AutomationId            How to Use in Test
Button               Seven                   num7Button              driver.click_button(auto_id="num7Button")
Button               Plus                    plusButton               driver.click_button(auto_id="plusButton")
```

**2. INPUT FIELDS** — text boxes, dropdowns
```
Type                 Name/Title              AutomationId            How to Use in Test
Edit                 Search                  SearchBox               driver.type_text("hello", auto_id="SearchBox")
ComboBox             Language                LanguageSelector        driver.select_combobox(auto_id="LanguageSelector", value="English")
```

**3. TEXT / STATUS ELEMENTS** — labels, status bars
```
Type                 Text Content                     AutomationId            How to Use in Test
Text                 Display is 0                     CalculatorResults       driver.get_text(auto_id="CalculatorResults")
```

### Priority: AutomationId > Name

- **Use `auto_id=`** whenever available — it's stable across app updates
- **Use `name=`** as fallback — it may change if the UI text changes
- If neither works, use `control_type=` + `found_index=`

---

## Quick Reference: Common Commands

```bash
# Activate virtual environment
source venv/bin/activate          # Linux/macOS
venv\Scripts\activate.bat         # Windows

# Run all tests
pytest

# Run per-part (recommended order)
pytest -m ui                      # Step 1: Windows UI tests
pytest -m console                 # Step 2: Console tests
pytest -m pkcs11                  # Step 3: PKCS#11 tests

# Run by language (PKCS#11 consumer repos)
pytest -m java                    # Java JAR tests only
pytest -m cpp                     # C++ native tests only
pytest -m go_test                 # Go binary tests only
pytest -m gtest                   # Google Test suite only
pytest -m "pkcs11 and not gtest"  # PKCS#11 but exclude GTest

# Run specific file / class / method
pytest tests/ui/test_sample_app.py -v
pytest tests/ui/test_sample_app.py::TestCalculatorDemo -v
pytest tests/ui/test_sample_app.py::TestCalculatorDemo::test_basic_addition -v

# Run with keyword filter
pytest -k "slot" -v               # Runs any test with "slot" in the name
pytest -k "keygen or signing" -v  # Keygen or signing tests

# Build source code (PKCS#11 consumer repos)
./scripts/build.sh                # Build all (Java + Go + GTest)
./scripts/build.sh java           # Build Java only
./scripts/build.sh go             # Build Go only
./scripts/build.sh gtest          # Build GTest/C++ only
./scripts/build.sh clean          # Clean build artifacts

# Inspect app UI (discover element IDs)
python scripts/inspect_app.py "calc.exe"
python scripts/inspect_app.py --title "My App" --output controls.txt
python scripts/inspect_app.py --title "My App" --interactive

# Allure report
allure serve evidence/allure-results     # Live preview
allure generate evidence/allure-results  # Static HTML

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
| Build script fails (Java) | Ensure Maven is installed: `mvn --version`. Check `pom.xml` path in settings.yaml |
| Build script fails (Go) | Ensure Go is installed: `go version`. Check source path in settings.yaml |
| Build script fails (GTest) | Ensure Make + GCC installed: `make --version`, `g++ --version` |
| Binary not found (test skipped) | Run `scripts/build.sh` first, or place pre-built binary in `bin/` |
| Log files not collected | Check `log_path` / `log_dir` in settings.yaml. Ensure paths are correct for your OS |
| GTest XML empty | Ensure `--gtest_output=xml:path` flag is passed. Check the binary runs without errors |
| `BUILD_SKIP` not working | Set env var: `export BUILD_SKIP=1` (Linux) or `set BUILD_SKIP=1` (Windows) |
