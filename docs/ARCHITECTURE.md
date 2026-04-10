# Ankole Framework - Architecture

## Overview

Ankole is a multi-driver E2E test framework designed for comprehensive testing across
web, API, CLI, and desktop interfaces. It follows a layered architecture with clear
separation of concerns.

## Layer Diagram

```
┌─────────────────────────────────────────────────────┐
│                    Tests Layer                       │
│  tests/web/  tests/api/  tests/cli/  tests/desktop/ │
├─────────────────────────────────────────────────────┤
│                    Flows Layer                       │
│  ankole/flows/workspace/  (composed Step sequences)  │
├─────────────────────────────────────────────────────┤
│                    Steps Layer                       │
│  ankole/steps/workspace/  (atomic test actions)      │
├─────────────────────────────────────────────────────┤
│                  Page Objects Layer                   │
│  ankole/pages/web/  ankole/pages/desktop/            │
├─────────────────────────────────────────────────────┤
│                   Drivers Layer                      │
│  WebDriver  │  UIDriver  │  APIDriver  │ ConsoleRunner│
│ (Playwright)│ (pywinauto)│   (httpx)   │ (subprocess) │
├─────────────────────────────────────────────────────┤
│                  Plugin Layer                        │
│  config  │  fixtures  │  hooks  │  metrics  │  kiwi  │
├─────────────────────────────────────────────────────┤
│               Infrastructure Layer                   │
│  Evidence  │  HealthCheck  │  SmokeGate  │  Logging  │
└─────────────────────────────────────────────────────┘
```

## Driver Abstraction

All drivers implement Protocol-based interfaces (structural typing):

- **DriverProtocol** — Desktop UI operations (click, type, wait)
- **WebDriverProtocol** — Web UI operations (goto, fill, click CSS selectors)
- **APIDriverProtocol** — HTTP operations (get, post, put, delete with auth)

This enables type checking without coupling to concrete implementations.

## Plugin System

The `ankole.plugin` package auto-registers with pytest via entry points:

```toml
[project.entry-points.pytest11]
ankole = "ankole.plugin"
```

Hooks provided:
- `pytest_configure` — Register markers, init smoke gate, connect TCMS
- `pytest_collection_modifyitems` — Auto-skip desktop on non-Windows, Kiwi filtering
- `pytest_sessionstart` — Health checks, metrics init
- `pytest_runtest_makereport` — Screenshot on failure, result tracking
- `pytest_sessionfinish` — Push to TCMS and Prometheus

## Flow/Step Engine

The flow engine (`ankole/flows/base.py`) provides:

- **FlowContext** — Shared state (driver, evidence, test data) between steps
- **Step** — Named action with retry support and conditional execution
- **Flow** — Ordered sequence of steps with cleanup and composition

Flows compose with the `+` operator:

```python
full_test = login_flow + create_flow + verify_flow
full_test.run(ctx)
```

## Evidence Collection

- Screenshots on test failure (automatic via hook)
- Step-level screenshots (via `tracked_step` decorator)
- App log collection (PRE + POST snapshots)
- Allure report integration
- Loki remote log aggregation

## Observability

```
Test Runner → Prometheus Pushgateway → Prometheus → Grafana
                                                      ↑
Application Logs → Promtail → Loki ───────────────────┘
```

All metrics use the `ankole_` prefix. Dashboard is pre-loaded in Grafana.
