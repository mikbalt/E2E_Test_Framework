# HSM Test Framework — Executive Summary

---

## The Problem

1. **No standardized way** to automate testing for Windows desktop apps (C#/.NET)
2. **Console-based tests** (PKCS#11 via Go/Java/C++) are scattered across repos with no unified reporting
3. **No evidence trail** — when tests pass or fail, there's no recorded proof (screenshots, logs)
4. **Manual effort** — tests run manually, results reported manually to Kiwi TCMS, no monitoring
5. **Multiple repos** need testing, but each would have to build its own framework from scratch

---

## What We Built

A **single, reusable test framework** that any team or repo can install with one command.

```
pip install git+https://gitlab.yourcompany.com/qa/hsm-test-framework.git
```

### Core Capabilities

| Capability | How |
|-----------|-----|
| **Windows UI Automation** | Opens apps, clicks buttons, reads text, verifies results (pywinauto) |
| **Console/CLI Testing** | Runs Go/Java/C++ binaries, captures output, validates results (subprocess) |
| **Automatic Evidence** | Screenshots per step, screenshots on failure, full logs — all attached to report |
| **Cross-Platform** | Windows for UI tests, Linux for console tests. UI tests auto-skip on Linux. |
| **Reusable Base** | Install once as a pip package. Any test repo gets all features automatically. |

---

## How It Works With Our Existing Environment

```
  Developer writes tests          Tests stored in
  using the framework     ──►     GitLab repos
                                      │
                                      ▼
                                  Jenkins picks up
                                  changes automatically
                                      │
                          ┌───────────┼───────────┐
                          ▼                       ▼
                   Windows Agent             Linux Agent
                   (UI + Console)            (Console only)
                          │                       │
                          └───────────┬───────────┘
                                      │
                      ┌───────────────┼───────────────┐
                      ▼               ▼               ▼
                 Allure Report   Kiwi TCMS        Grafana
                 (evidence +     (test cases +    (pass rate,
                  screenshots)    run results)     trends)
```

### Integration Details

| Your System | Integration | What Happens |
|-------------|-------------|-------------|
| **GitLab** | Source repo | Framework code + test code stored here. Consumer repos reference framework via git URL. |
| **Jenkins** | CI/CD pipeline | `Jenkinsfile` included. Runs tests on Windows + Linux agents in parallel. Publishes Allure report as build artifact. |
| **Kiwi TCMS** | Auto-reporting | After each test run, results are **automatically pushed** — test cases created, pass/fail recorded, run history tracked. Zero manual entry. |
| **Grafana** | Monitoring dashboard | Test pass rate, duration trends, last run timestamp — all pushed to Prometheus and visualized in Grafana. Dashboard JSON included, ready to import. |

---

## Architecture: One Framework, Many Repos

```
         hsm-test-framework          ◄── This repo (the shared base)
          (pip-installable)
                 │
     ┌───────────┼───────────┬──────────────┐
     ▼           ▼           ▼              ▼
 HSM Admin    PKCS#11     Key Mgmt     Future App
  Tests        Tests       Tests         Tests
 (repo A)    (repo B)    (repo C)      (repo D)
```

Each consumer repo only needs:
- `requirements.txt` (one line pointing to framework)
- `config/settings.yaml` (app-specific paths)
- `tests/` (their actual test files)
- `Jenkinsfile` (copy from template)

**Everything else is inherited**: fixtures, evidence capture, TCMS reporting, Grafana metrics, platform guards.

---

## What Gets Recorded (Evidence)

Every test run produces:

| Evidence Type | Format | Where |
|--------------|--------|-------|
| Step-by-step screenshots | PNG | Allure report (embedded) + `evidence/` folder |
| Failure screenshots | PNG | Auto-captured on any test failure |
| Desktop screenshots | PNG | Full screen capture on demand |
| Console command output | TXT | stdout + stderr + duration logged |
| Test execution logs | TXT | Timestamped log per test |
| Summary report | HTML | Allure interactive report |
| Test case results | — | Kiwi TCMS (synced automatically) |
| Metrics over time | — | Grafana dashboard |

---

## Key Decisions & Why

| Decision | Why |
|----------|-----|
| **Python** (not C#) | Faster to write, cross-platform, works for both UI and console tests |
| **pywinauto** (not Appium/WinAppDriver) | Lightweight, no server needed, native Windows support, active community |
| **pytest** (not unittest) | Industry standard, rich plugin ecosystem, markers, fixtures, parallel support |
| **Allure** (not just JUnit XML) | Visual reports with embedded screenshots, step-by-step evidence, shareable HTML |
| **pip package** (not copy-paste) | One upgrade command updates all repos. Version controlled. No code duplication. |
| **pytest plugin** (auto-registered) | Consumer repos get everything with zero configuration. Just `pip install`. |

---

## Effort Estimate

| Phase | Scope | Status |
|-------|-------|--------|
| **Phase 1 — Foundation** | Framework, CI/CD, integrations, templates | **Done** |
| **Phase 2 — Harden** | Unit tests for framework, retry logic, config validation | ~1-2 weeks |
| **Phase 3 — Enhanced Evidence** | Video recording, Slack notifications, annotated screenshots | ~2-3 weeks |
| **Phase 4 — Advanced** | Page Object Model, PKCS#11 helpers, SSH remote exec | ~3-4 weeks |
| **Phase 5 — Scale** | Private PyPI, CLI scaffolding, Docker runners, matrix builds | ~4-6 weeks |

Phase 1 is complete and **ready to use today**.
Phases 2-5 are in `TODO.md`, can be tackled incrementally.

---

## Demo Path (5 minutes)

1. Run `scripts\setup.bat` — shows one-command setup
2. Run `scripts\run_tests.bat smoke` — opens Calculator, clicks 7+3=10, captures screenshots
3. Open `evidence/allure-report/index.html` — show screenshots embedded in report
4. Show `Jenkinsfile` — automated pipeline with Windows + Linux parallel execution
5. Show `examples/consumer-repo-template/` — how fast a new team can start

---

## Summary

| Before | After |
|--------|-------|
| No automation for Windows apps | One-click test execution with evidence |
| Console tests scattered, no reporting | Unified framework, auto-reported to Kiwi TCMS |
| No evidence when tests fail | Screenshots per step + on failure, attached to Allure |
| Each repo builds its own tooling | `pip install` one shared framework, write only tests |
| Manual TCMS updates | Automatic — every run syncs to Kiwi TCMS |
| No test health visibility | Grafana dashboard with trends, pass rate, duration |
| Windows-only | Cross-platform: Windows + Linux |
