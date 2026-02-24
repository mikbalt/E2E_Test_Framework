# HSM E2E Test Framework

Reusable, cross-platform E2E test framework for Windows desktop applications and console-based tools (PKCS#11 via Golang, Java, C++, Google Test).

Designed as a **shared base package** — install once, use across multiple test repositories.

---

## What's Inside

### Core Framework (`hsm_test_framework/`)

| Module | What It Does |
|--------|-------------|
| `ui_driver.py` | Windows UI automation via pywinauto. Supports WPF, WinForms, Win32. Wraps common actions: click, type, get text, select menu/tab/combobox. |
| `console_runner.py` | Subprocess wrapper for CLI tools. Captures stdout/stderr/duration. Built-in assertions (`assert_success`, `assert_output_contains`). Helpers for Java, Go, Make, CMake, and generic executables. Cross-platform path resolution. |
| `evidence.py` | Collects screenshots (per step + on failure), logs, and text output. Auto-attaches to Allure reports. `StepTracker` context manager for step-by-step evidence. |
| `log_collector.py` | **Collects external log files** from test tools. Supports single files, directories, real-time monitoring, and GTest XML parsing. Auto-attaches to Allure. |
| `kiwi_tcms.py` | Reports test results to Kiwi TCMS. Auto-creates test runs, syncs pass/fail per test case. |
| `grafana_push.py` | Pushes metrics (pass rate, duration, trends) to Prometheus Pushgateway for Grafana dashboards. |
| `plugin.py` | pytest plugin (auto-registered via `pytest11` entry point). Provides fixtures, platform guards, screenshot-on-failure, TCMS and Grafana hooks. Consumer repos get everything for free. |

### Auto-Provided Fixtures

When a consumer repo installs this framework, these fixtures are **automatically available** in every test — no configuration needed:

| Fixture | Type | What It Provides |
|---------|------|-----------------|
| `config` | `session` | `settings.yaml` loaded as a Python dict |
| `evidence` | `per-test` | Evidence collector (screenshots, logs, text) for current test |
| `console` | `per-test` | `ConsoleRunner` instance for executing CLI commands |
| `log_collector` | `per-test` | `LogCollector` linked to current test's evidence directory |
| `ui_app` | `per-test` | `UIDriver` instance (auto-skipped on non-Windows) |

### Sample Tests (`tests/`)

| File | Purpose |
|------|---------|
| `tests/ui/test_sample_app.py` | Demo: opens Windows Calculator, clicks buttons, verifies result. Template for HSM Admin app included. |
| `tests/console/test_pkcs11_sample.py` | Demo: runs PKCS#11 tools (native, Go, Java, C++). Cross-platform with `resolve_platform_config()`. |

### Tools & Scripts

| File | Purpose |
|------|---------|
| `scripts/setup.bat` / `setup.sh` | One-command setup. Auto-detects best Python version (supports side-by-side installs). |
| `scripts/run_tests.bat` / `run_tests.sh` | Quick test runner with marker selection and Allure report generation. |
| `scripts/inspect_app.py` | **UI Inspector** — discover element IDs, control types, automation IDs before writing UI tests. Supports quick scan, deep scan, save-to-file, and interactive hover mode. |

### CI/CD & Infrastructure

| File | Purpose |
|------|---------|
| `Jenkinsfile` | Multi-platform pipeline. Runs Windows + Linux agents in parallel, merges Allure results. |
| `config/settings.yaml` | Central config: app paths (per-platform), tool paths, log paths, evidence, TCMS, Grafana settings. |
| `config/grafana-dashboard.json` | Ready-to-import Grafana dashboard with pass rate gauge, duration trends, test history. |

### Consumer Repo Templates (`examples/`)

| Template | For | Contents |
|----------|-----|----------|
| `examples/consumer-repo-template/` | **UI + general console** tests — new repos for Windows app testing or simple CLI tools | `requirements.txt`, `conftest.py`, `settings.yaml`, sample UI + console tests, `Jenkinsfile` |
| `examples/pkcs11-consumer-template/` | **PKCS#11 tests** — wrapping existing Java, C++, Go, and Google Test binaries | Build scripts, 4 test wrapper files (Java/C++/Go/GTest), log collection config, `Jenkinsfile` with build stage |

---

## Architecture

```
                    ┌─────────────────────────────────┐
                    │   hsm-test-framework (GitLab)   │
                    │   pip-installable package        │
                    └──────────┬──────────────────────┘
                               │
         ┌─────────────────────┼─────────────────────┐
         │                     │                     │
  ┌──────▼───────┐   ┌────────▼────────┐   ┌────────▼────────┐
  │ hsm-admin    │   │ pkcs11-java     │   │ pkcs11-gtest    │
  │ tests (UI)   │   │ tests (JAR)     │   │ tests (C++)     │
  └──────────────┘   └─────────────────┘   └─────────────────┘
         │                     │                     │
         │              ┌──────▼───────┐   ┌────────▼────────┐
         │              │ pkcs11-go    │   │ future-app      │
         │              │ tests (Go)   │   │ tests           │
         │              └──────────────┘   └─────────────────┘
         │
  Each consumer repo:
    - pip install git+<this-repo>
    - Gets all fixtures & hooks automatically (config, evidence, console, log_collector, ui_app)
    - Only writes its own tests + config/settings.yaml
```

---

## Key Features

### 1. Multi-Language Test Wrapping

Python wraps your **existing** test binaries — Java/C++/Go source code stays unchanged:

```
Python Wrapper                    Your Existing Code
─────────────────                 ──────────────────
1. [Optional] Build               Java/C++/Go source unchanged
2. Run binary via subprocess       Binary runs as-is
3. Capture stdout + stderr         Output captured for evidence
4. Collect external log files      Tool's own logs → Allure report
5. Assert exit code + output       Validate results
6. Attach everything to Allure     Full evidence trail
```

### 2. Log Collection (`LogCollector`)

Each test tool can write its own log files. The framework **automatically collects** them:

```python
# In your test
def test_keygen(config, console, evidence, log_collector):
    tool = resolve_platform_config(config["console_tools"]["pkcs11_java"])

    # Monitor log file in real-time (captures only new lines)
    with log_collector.monitor(tool["log_path"]) as mon:
        result = console.run_java(jar_path=tool["command"], args=["--keygen"])

    # Collect evidence
    evidence.attach_text(result.output, "stdout")
    log_collector.collect_text(mon.captured, "runtime_log")
    log_collector.collect_from_config(tool)  # auto-picks log_path, log_dir, gtest_xml
```

Configure log paths in `settings.yaml`:

```yaml
console_tools:
  pkcs11_java_keygen:
    command_linux: "bin/pkcs11-keygen.jar"
    log_path_linux: "logs/java_keygen.log"        # Single log file
    log_dir_linux: "logs/java/"                    # Or a directory
    log_pattern: "*.log"                           # File pattern
    gtest_xml_linux: "evidence/results.xml"        # GTest XML report
```

| Method | What It Does |
|--------|-------------|
| `collect(path)` | Copy a single log file + attach to Allure |
| `collect_dir(dir, pattern)` | Collect all matching files from a directory |
| `monitor(path)` | Context manager — capture only lines written during test execution |
| `collect_gtest_xml(path)` | Parse GTest XML report, create readable summary + attach both |
| `collect_from_config(tool)` | Auto-collect based on `log_path`, `log_dir`, `gtest_xml` from settings.yaml |
| `collect_text(content, name)` | Save raw text as a log file and attach |

### 3. Build Support for Source Code

For tools that need compilation (Java Maven, Go build, C++ Makefile/CMake):

```bash
# Build everything
./scripts/build.sh              # or scripts\build.bat

# Build by language
./scripts/build.sh java         # Maven
./scripts/build.sh go           # go build
./scripts/build.sh gtest        # Makefile

# Clean build artifacts
./scripts/build.sh clean
```

The `conftest.py` in PKCS#11 template includes a **session-scoped auto-build fixture** that compiles before tests run. Skip with `BUILD_SKIP=1`.

### 4. ConsoleRunner Helpers

| Method | For |
|--------|-----|
| `run(command, args)` | Run any command with output capture |
| `run_java(jar_path, args)` | Run Java JARs or classes |
| `run_go(binary_path, args)` | Run Go compiled binaries |
| `run_make(target, makefile_dir)` | Run Makefile targets |
| `run_cmake_build(build_dir)` | Run CMake builds |
| `run_executable(exe_path, args)` | Run any compiled binary (auto-handles .exe on Windows) |
| `run_script(script_path)` | Run .bat, .cmd, .ps1, or shell scripts |

### 5. UI Inspector Tool

Discover element IDs before writing UI tests:

```cmd
python scripts/inspect_app.py "calc.exe"                        # Quick scan
python scripts/inspect_app.py --title "My App" --depth 5        # Deep scan
python scripts/inspect_app.py --title "My App" --output ids.txt # Save to file
python scripts/inspect_app.py --title "My App" --interactive    # Hover to identify
```

### 6. Test Markers (Run Per-Part)

| Marker | What it runs | Platform |
|--------|-------------|----------|
| `ui` | Windows UI automation tests | Windows only (auto-skipped on Linux) |
| `console` | Console/CLI tests | Windows + Linux |
| `pkcs11` | All PKCS#11 tests | Windows + Linux |
| `java` | Java JAR-based tests | Windows + Linux |
| `cpp` | C++ native executable tests | Windows + Linux |
| `go_test` | Go compiled binary tests | Windows + Linux |
| `gtest` | Google Test (C++) suite tests | Windows + Linux |
| `smoke` | Quick verification tests | Both |
| `regression` | Full regression suite | Both |
| `needs_build` | Tests requiring compilation | Both |

```bash
# Run by marker
pytest -m java -v                     # Java tests only
pytest -m "pkcs11 and not gtest" -v   # PKCS#11 but exclude GTest
pytest -m smoke -v                    # Quick smoke tests
```

---

## Platform Support

| Component | Windows | Linux |
|-----------|---------|-------|
| UI tests (pywinauto) | Runs | Auto-skipped |
| Console tests (PKCS#11) | Runs | Runs |
| Log collection | Runs | Runs |
| Evidence / screenshots | Runs | Runs (if display available) |
| Allure reporting | Runs | Runs |
| Kiwi TCMS | Runs | Runs |
| Grafana metrics | Runs | Runs |
| Jenkins pipeline | `bat` commands | `sh` commands |
| Build scripts | `build.bat` | `build.sh` |

---

## Quick Start

### Framework Development

```bash
# 1. Clone
git clone <gitlab-url>/hsm-test-framework.git
cd hsm-test-framework

# 2. Setup (auto-detects Python, creates venv, installs deps)
scripts/setup.bat        # Windows
./scripts/setup.sh       # Linux/macOS

# 3. Configure — edit config/settings.yaml with your app/tool paths

# 4. Run
scripts/run_tests.bat smoke     # Windows
./scripts/run_tests.sh smoke    # Linux
```

### New Consumer Repo (UI / General)

```bash
cp -r examples/consumer-repo-template/ /path/to/my-tests/
cd /path/to/my-tests/
pip install -r requirements.txt
# Edit config/settings.yaml, then write your tests
```

### New Consumer Repo (PKCS#11)

```bash
cp -r examples/pkcs11-consumer-template/ /path/to/pkcs11-tests/
cd /path/to/pkcs11-tests/
pip install -r requirements.txt
# Place binaries in bin/, source in src/
# Edit config/settings.yaml with paths + log locations
./scripts/build.sh              # Build source code
./scripts/run_tests.sh smoke    # Run tests
```

### Using in Test Files

```python
from hsm_test_framework import (
    UIDriver, ConsoleRunner, Evidence, StepTracker,
    LogCollector, LogMonitor, resolve_platform_config,
)

# All fixtures auto-available: config, evidence, console, log_collector, ui_app
```

---

## PKCS#11 Consumer Repo Structure

```
pkcs11-tests/
├── bin/                              # Pre-compiled binaries
│   ├── pkcs11-keygen.jar             # Java (ready)
│   ├── pkcs11_encrypt                # C++ (ready)
│   └── ...
├── src/                              # Source code (if needs build)
│   ├── java/signing/pom.xml          # Java Maven
│   ├── go/slot/main.go              # Go source
│   └── cpp/gtest_crypto/Makefile     # GTest + Makefile
├── config/settings.yaml              # Paths, log locations, build flags
├── tests/console/
│   ├── test_pkcs11_java.py           # Java wrappers (5 tests)
│   ├── test_pkcs11_cpp.py            # C++ wrappers (6 tests)
│   ├── test_pkcs11_go.py             # Go wrappers (4 tests)
│   └── test_pkcs11_gtest.py          # GTest wrappers (4 tests)
├── scripts/
│   ├── build.sh / build.bat          # Compile Java/Go/GTest
│   └── run_tests.sh / run_tests.bat  # Run tests by marker
├── logs/                             # Tool log files (auto-collected)
├── evidence/                         # Test evidence (auto-generated)
├── conftest.py                       # Auto-build + tool_config fixture
├── Jenkinsfile                       # Build → Test → Report pipeline
└── requirements.txt                  # One line: hsm-test-framework
```

---

## Evidence Flow

Every test run produces a complete evidence trail:

```
Test Execution
    │
    ├─► stdout / stderr capture         → Allure report (text attachment)
    ├─► External log files              → Allure report (auto-collected via LogCollector)
    ├─► GTest XML reports               → Allure report (parsed summary + raw XML)
    ├─► Screenshots (per step)          → Allure report (embedded PNG)
    ├─► Screenshots (on failure)        → Allure report (auto-captured)
    ├─► Test execution logs             → evidence/ folder (timestamped)
    │
    ├─► JUnit XML                       → Jenkins test results
    ├─► Kiwi TCMS sync                  → Test case management (auto-reported)
    └─► Prometheus metrics              → Grafana dashboard (pass rate, trends)
```

---

## Documentation

| Document | Contents |
|----------|----------|
| **[SETUP_GUIDE.md](SETUP_GUIDE.md)** | Full setup instructions, prerequisites, Jenkins/Grafana/TCMS configuration, PKCS#11 consumer repo setup, per-part execution, UI element discovery, troubleshooting |
| **[PRESENTATION.md](PRESENTATION.md)** | Executive summary for managers — problem, solution, architecture, integration flow, effort estimate, demo path |
| **[TODO.md](TODO.md)** | Roadmap and future improvement ideas (5 phases) |
| **[config/settings.yaml](config/settings.yaml)** | Configuration reference with inline comments |
| **[examples/consumer-repo-template/](examples/consumer-repo-template/)** | Boilerplate for UI + general console test repos |
| **[examples/pkcs11-consumer-template/](examples/pkcs11-consumer-template/)** | Boilerplate for PKCS#11 test repos (Java, C++, Go, GTest) with build scripts |


https://claude.ai/magic-link?client=desktop_app#553e1e0d6961cd18c11489ac2f85741a:YWltYW50YXAyMDIzZmJAZ21haWwuY29t