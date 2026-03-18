# Sphere E2E Test Framework — Decoupling & Modularity Brief

**Presenter**: QA Automation Engineer
**Date**: March 2026
**Audience**: Senior Engineers, Tech Leads

---

## 1. Problem Statement

Framework v1.0 was tightly coupled to the E-Admin application:

| Problem | Impact |
|---------|--------|
| `BasePage` contained E-Admin-specific methods (sidebar nav, T&C, logout) | New apps (CPS, Proxy) inherited 10+ irrelevant methods |
| `plugin.py` was a single 400+ line file | Hard to navigate, test, or extend |
| Each new app required ~120 lines of boilerplate conftest fixtures | Slow onboarding, copy-paste bugs |
| No driver interface contract | Impossible to swap pywinauto for Playwright or mock drivers |
| Hardcoded `time.sleep()` throughout UIDriver | Flaky tests, no way to tune per-environment |
| Dependency-tracking hooks were silently broken | `@pytest.mark.depends_on` was a no-op in UI tests |
| Evidence logger polluted root logger | Log cross-contamination across parallel test runs |

**Bottom line**: Adding a new application (CPS/Proxy) required touching 6+ files and deep framework knowledge.

---

## 2. What We Did

### Phase 1: Page Object Hierarchy Split

```
BEFORE                          AFTER
──────                          ─────
BasePage                        BasePage (generic WinForms only)
├── LoginPage                   ├── EAdminBasePage (E-Admin nav)
├── DashboardPage               │   ├── LoginPage
├── KeyCeremonyPage             │   ├── DashboardPage
└── ... (all apps)              │   └── ... (10 E-Admin pages)
                                ├── CPS pages (clean base)
                                └── Proxy pages (clean base)
```

- `BasePage`: `_step()`, `dismiss_ok()`, `dismiss_ok_with_message()` — nothing app-specific
- `EAdminBasePage`: `agree_and_next()`, `goto_user_management()`, `logout()` — E-Admin only
- New apps inherit `BasePage` directly — zero unwanted methods

### Phase 2: Plugin Decomposition

```
BEFORE                          AFTER
──────                          ─────
plugin.py (1 file, 400+ LOC)   plugin/
                                ├── __init__.py   (backward compat re-exports)
                                ├── config.py     (config loading + env overrides)
                                ├── hooks.py      (pytest hooks + screenshots)
                                ├── fixtures.py   (config, evidence, console)
                                ├── kiwi_hooks.py (TCMS sync helpers)
                                └── metrics.py    (Prometheus push)
```

Each module < 100 LOC. Single responsibility. Independently testable.

### Phase 3: DriverProtocol

```python
from sphere_e2e_test_framework.driver.base import DriverProtocol

@runtime_checkable
class DriverProtocol(Protocol):
    def click_button(self, ...) -> None: ...
    def type_text(self, ...) -> None: ...
    def wait_for_element(self, ...) -> Any: ...
    # ... 23 methods + 2 properties total
```

- Any driver satisfying this interface works with all page objects
- Enables: Playwright for web apps, mock drivers for unit testing, remote drivers
- Zero modification to existing page objects or tests required

### Phase 4: Conftest Factory Pattern

```python
# BEFORE: 120+ lines of manual fixtures per app
@pytest.fixture(scope="session")
def cps_config(config): ...
@pytest.fixture
def cps_driver(cps_config): ...
@pytest.fixture(autouse=True)
def window_monitor(...): ...
@pytest.fixture(autouse=True)
def collect_app_logs(...): ...

# AFTER: 4 lines
cps_config = make_app_config_fixture("cps")
cps_driver = make_driver_fixture("cps")
window_monitor = make_window_monitor_fixture("cps")
collect_app_logs = make_app_logs_fixture("cps")
```

Adding a new application: **4 lines of conftest + page objects + tests**. That's it.

### Phase 5: Configurable Timing (Zero Hardcoded Sleeps)

```python
# BEFORE: 12+ hardcoded values scattered across UIDriver
time.sleep(0.3)  # after click
time.sleep(0.5)  # after popup dismiss
time.sleep(1.0)  # after close

# AFTER: Class-level constants, overridable per-instance
class UIDriver:
    TIMING_AFTER_CLICK = 0.3
    TIMING_AFTER_POPUP_DISMISS = 0.5
    TIMING_AFTER_CLOSE = 1.0
    TIMING_AFTER_COMBO_EXPAND = 0.5
    TIMING_POLL_INTERVAL = 0.5

# Override via config or API
driver.set_timing({"after_click": 0.2, "after_close": 2.0})
```

Fast environments → lower values. Slow VMs → higher values. No code changes.

### Phase 6: Bug Fixes & Hardening

| Fix | Before | After |
|-----|--------|-------|
| Hook shadowing | `depends_on` marker silently broken | `track_passed_case()` helper, explicit imports |
| Flow headless crash | `Step.execute` crashes if `evidence=None` | Guard: logs step name, skips screenshots |
| Screenshot scope | Only captures E-Admin failures | Auto-detects any `*_driver` fixture |
| Evidence logger | Root logger pollution | Scoped to `sphere_e2e_test_framework` namespace |
| Missing markers | Consumer repos fail `--strict-markers` | All 13 markers registered in plugin |

---

## 3. Architecture (Current State)

```
sphere_e2e_test_framework/
├── plugin/               ← pytest plugin (auto-registered)
│   ├── config.py         ← YAML + env vars + data-driven overrides
│   ├── hooks.py          ← lifecycle hooks + screenshots
│   ├── fixtures.py       ← config, evidence, console, ui_app
│   ├── kiwi_hooks.py     ← bidirectional TCMS sync
│   └── metrics.py        ← Prometheus push
├── driver/
│   ├── base.py           ← DriverProtocol (23 methods, 2 properties)
│   ├── ui_driver.py      ← pywinauto impl (configurable timing)
│   ├── evidence.py       ← screenshots + scoped logging
│   └── ...               ← 9 more infrastructure modules
├── flows/                ← Step (retry+backoff), Flow (cleanup+composition)
├── steps/                ← Reusable step factories
├── testing/              ← Conftest factories + shared hooks
└── pages/
    ├── base_page.py      ← Generic WinForms (clean)
    └── e_admin/
        ├── e_admin_base_page.py  ← E-Admin nav (isolated)
        └── ...            ← 10 page classes
```

---

## 4. Key Metrics

| Metric | Value |
|--------|-------|
| Unit tests | **99/99 pass** (0.77s) |
| Total tests collected | **118** (0 errors) |
| Hardcoded sleep values | **0** (was 12+) |
| Lines to add new app | **4** (was 120+) |
| Plugin modules | **5** (was 1 monolith) |
| DriverProtocol coverage | **23 methods + 2 properties** (was 10 methods) |
| Stale references | **0** |
| Broken hooks | **0** (was 1 — depends_on silently broken) |

---

## 5. Scalability Path

### Ready Now
- **Playwright driver**: Implement `DriverProtocol` → all page objects work
- **New WinForms apps**: 4-line conftest + page objects inheriting clean `BasePage`
- **Kiwi TCMS**: Bidirectional sync, gap detection, auto-create runs
- **Grafana dashboards**: Configurable metric prefix + suite labels
- **CI/CD**: Jenkins pipeline, health checks, smoke gate

### Enabled By This Work
| Capability | How |
|-----------|-----|
| Web app testing | New driver implementing `DriverProtocol` (Playwright/Selenium) |
| Mobile testing | New driver implementing `DriverProtocol` (Appium) |
| Mock driver for unit tests | Satisfies protocol, no UI needed |
| Per-environment tuning | `set_timing()` / `timing_config` in settings.yaml |
| Parallel test runs | Scoped evidence logger, no cross-contamination |
| Consumer repo adoption | `pip install` + 4-line conftest + settings.yaml |

---

## 6. Design Decisions & Trade-offs

| Decision | Rationale | Trade-off |
|----------|-----------|-----------|
| `Protocol` over ABC | Duck typing — existing code works without modification | `issubclass()` limited in Python < 3.12 |
| `EAdminBasePage` split | Clean inheritance for new apps | One extra class in E-Admin hierarchy |
| Factory conftest | 4 lines vs 120 lines | Less visible — need to read factory source for customization |
| Class-level timing constants | Zero hardcoded sleeps, tunable | Instance mutation (not immutable config object) |
| Scoped logger | No cross-contamination | Only captures `sphere_e2e_test_framework.*` logs, not third-party |
| `track_passed_case()` helper | Solves hook shadowing cleanly | Consumers must call it explicitly if they override the hook |

---

## 7. Demo Flow (If Needed)

1. **Show `tests/ui/cps/conftest.py`** — 4 lines creates a full test suite
2. **Run `pytest tests/unit/ -v`** — 99 tests pass in < 1 second
3. **Run `pytest --co -q`** — 118 tests collected, 0 errors
4. **Show `DriverProtocol`** — explain how Playwright would plug in
5. **Show `set_timing()`** — demonstrate environment-specific tuning
6. **Show Allure report** — evidence trail with step screenshots

---

## 8. Q&A Prep

**Q: Why not use an Abstract Base Class instead of Protocol?**
A: Protocol is structural (duck-typed). `UIDriver` satisfies it without inheriting anything. This means existing code works without modification, and third-party drivers don't need to import our base class.

**Q: What happens if a new driver doesn't implement all 23 methods?**
A: `isinstance(driver, DriverProtocol)` returns False at runtime. Page objects will get `AttributeError` on first missing method call — fail-fast, clear error.

**Q: How do you prevent flaky tests?**
A: Three layers: (1) Configurable timing via `TIMING_*` constants — no hardcoded sleeps. (2) `_with_popup_retry` decorator auto-dismisses unexpected popups and retries. (3) `Step(retries=N)` with exponential backoff in the Flow layer.

**Q: Can this run in parallel?**
A: Evidence logger is now scoped (no cross-contamination). The `config` fixture is session-scoped and shared. For full xdist parallelism, `session.results` would need a thread lock — tracked as a known improvement.

**Q: How long to add a new application?**
A: ~30 minutes: add config to `settings.yaml`, create page objects inheriting `BasePage`, write 4-line conftest, write first test. See `COOKBOOK.md`.
