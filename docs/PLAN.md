# Workspace Test Framework — Maximize Effort Plan

> Generated from full codebase analysis on 2026-02-27.
> Goal: Identify the highest-ROI actions to get maximum value from the framework.

---

## Current State Assessment

### What's Built & Working (Phase 1 + 1.5)

| Module | Status |
|--------|--------|
| `ui_driver.py` — Windows UI automation (WPF, WinForms, Win32) | Done |
| `console_runner.py` — Subprocess wrapper with assertions | Done |
| `evidence.py` — Screenshots, logs, `tracked_step` | Done |
| `log_collector.py` — External log files, real-time monitor, GTest XML | Done |
| `health_check.py` — Pre-execution ping/tcp/http checks | Done |
| `smoke_gate.py` — Fail-fast for smoke tests | Done |
| `kiwi_tcms.py` — Bidirectional TCMS integration | Done |
| `grafana_push.py` — Prometheus Pushgateway metrics | Done |
| `plugin.py` — Auto-registered pytest plugin with fixtures & hooks | Done |
| Jenkinsfile — Multi-platform parallel pipeline | Done |
| Consumer repo templates (UI + CLI) | Done |
| Setup scripts, UI Inspector, SETUP_GUIDE, README | Done |

### What's Disabled / Unused

| Feature | Config Location | Current State |
|---------|----------------|---------------|
| Health Check | `settings.yaml → health_check.enabled` | `false` |
| Kiwi TCMS | `settings.yaml → kiwi_tcms.enabled` | `false` |
| Grafana Metrics | `settings.yaml → metrics.enabled` | `false` |
| Smoke Gate | Jenkinsfile `--smoke-gate` flag | Not used |
| TCMS in Jenkins | `Jenkinsfile` env block | Commented out |
| Video Recording | `settings.yaml → evidence.video_recording` | `false` (not implemented) |

### Test Coverage Gap

| File | Tests | Status |
|------|-------|--------|
| `tests/ui/test_workspace.py` | 1 test (`test_connect_and_load_dashboard`) | Active — only real test |
| `tests/ui/test_sample_app.py` | 2 tests (Calculator demo) + 1 skipped template | Demo only |
| `tests/console/test_pkcs11_sample.py` | 7 tests (CLI samples) | Sample — tools not configured |
| Framework unit tests | 0 | None exist |

**Bottom line:** The framework has 10 modules with rich capabilities. The actual test suite has **1 real test**.

---

## Known Bugs

| Bug | Location | Severity | Fix |
|-----|----------|----------|-----|
| `STATUS_BLOCKED` undefined variable | `kiwi_tcms.py:203` | Medium | Change to `self.status_ids["BLOCKED"]` |
| `resolve_platform_config` only resolves `command` and `working_dir` | `console_runner.py:39` | Low | Should also resolve `log_path`, `log_dir`, `gtest_xml` |


---

## Prioritized Action Plan

### Tier 1: Immediate (DONE)

Pure configuration changes with immediate impact. All resolved.

- [x] **Enable Health Check** — flip `health_check.enabled: true` in `settings.yaml`
  - Prevents wasted CI runs when Workspace at `10.66.1.10:52000` is unreachable
  - Already configured with ping + TCP checks
- [x] **Add `--smoke-gate` to Jenkinsfile** — add flag to pytest command in both Win + Linux stages
  - Fail-fast: if smoke tests fail, skip remaining tests
  - Saves CI time on broken environments
- [x] **Fix `STATUS_BLOCKED` bug** in `kiwi_tcms.py:203`
  - Changed `STATUS_BLOCKED` → `self.status_ids["BLOCKED"]`
  - Was causing NameError if any test reported BLOCKED status

---

### Tier 2: This Sprint (Days)

#### Write More Workspace Web Tests

The app is configured (`AdminApp.exe`, WinForms, Workspace simulator). Only connection is tested. Add:

- [ ] **Workspace Web — Settings Navigation**: Open settings panel, verify fields visible
- [ ] **Workspace Web — Workspace Slot Listing**: Connect → list available slots → verify output
- [ ] **Workspace Web — Key Generation**: Connect → generate key → verify key appears in list
- [ ] **Workspace Web — Certificate Operations**: Import/export certificate workflows
- [ ] **Workspace Web — Disconnect and Reconnect**: Connect → disconnect → reconnect → verify state
- [ ] **Workspace Web — Connection Error Handling**: Wrong IP/port → verify error message shown
- [ ] **Workspace Web — Multi-step Workflow**: Connect → operate → verify → disconnect (full lifecycle)

> Use `scripts/inspect_app.py --title "AdminApp" --depth 5` to discover all available UI elements first.

#### Code Quality Fixes

- [x] **Migrate `test_sample_app.py`** to use fixtures (`ui_app`, `evidence`) instead of direct instantiation
- [x] **Replace `StepTracker` with `tracked_step`** in `test_sample_app.py`
- [x] **Enable Kiwi TCMS** — configure credentials if infrastructure is available (user: intentionally disabled for now)
- [ ] **Add unit tests** for `resolve_platform_config()` and `smoke_gate.py` (pure logic, easy to test)

#### TCMS Bidirectional Flow Improvements (DONE)

- [x] **Rewrite `_filter_by_kiwi_run`** — only use `@pytest.mark.tcms(case_id=X)` for matching (removed unreliable name-based matching)
- [x] **Detect unmatched TCMS cases** — log WARNING with case IDs and summaries
- [x] **Mark unmatched TCMS cases as BLOCKED** — with comment explaining how to link automation
- [x] **Bidirectional session summary** — log matched vs unmatched counts at session end
- [x] **Add `mark_unmatched_as_blocked`** method to `KiwiReporter`
- [x] **Document full bidirectional flow** in README.md with ASCII diagram

---

### Tier 3: Next Sprint (1–2 Weeks)

#### Framework Unit Tests (Phase 2 from TODO.md)

- [ ] Unit tests for `console_runner.py` — mock subprocess, verify `CommandResult` assertions
- [ ] Unit tests for `evidence.py` — mock file I/O, verify Allure attachment
- [ ] Unit tests for `kiwi_tcms.py` — mock XML-RPC calls, test bidirectional flow
- [ ] Unit tests for `health_check.py` — mock socket/ping, test report generation
- [ ] Unit tests for `log_collector.py` — mock file reads, test monitor context manager

#### Enhance `resolve_platform_config`

- [ ] Extend to resolve `log_path_windows`/`log_path_linux` → `log_path`
- [ ] Extend to resolve `log_dir_windows`/`log_dir_linux` → `log_dir`
- [ ] Extend to resolve `gtest_xml_windows`/`gtest_xml_linux` → `gtest_xml`

#### Error Resilience

- [ ] Retry logic for flaky UI interactions (configurable count + delay in `settings.yaml`)
- [ ] Graceful cleanup if app crashes mid-test (process kill fallback)
- [ ] Per-step timeout (not just per-test)

#### Page Object Model for Workspace Web

- [ ] Create `pages/workspace_main.py` — main window actions
- [ ] Create `pages/workspace_settings.py` — settings panel actions
- [ ] Create `pages/workspace_connection.py` — connection dialog actions
- [ ] Refactor `test_workspace.py` to use POM classes

---

### Tier 4: Future (Phase 3–5 from TODO.md)

- [ ] Enable Grafana metrics (deploy Pushgateway first)
- [ ] Video recording via ffmpeg
- [ ] Slack/Teams webhook notifications on failure
- [ ] Parallel test execution with pytest-xdist
- [ ] Private PyPI publishing for framework distribution
- [ ] Config validation on startup (warn on missing required fields)
- [ ] CI pipeline for the framework repo itself (test on push)

---

## Jenkins Pipeline Quick Wins

Current `Jenkinsfile` doesn't use framework features. Recommended changes:

```groovy
// Add to Win/Linux test stages:
python -m pytest --smoke-gate -m ${suite} \
    --alluredir=evidence/allure-results \
    --junitxml=evidence/junit-results.xml

// Uncomment TCMS credentials in environment block:
TCMS_API_URL  = credentials('tcms-api-url')
TCMS_USERNAME = credentials('tcms-username')
TCMS_PASSWORD = credentials('tcms-password')

// Add --kiwi-create-run for auto TCMS reporting:
python -m pytest --smoke-gate --kiwi-create-run -m ${suite} ...
```

---

## Effort vs Impact Matrix

```
                        HIGH IMPACT
                            |
    Enable health check  *  |  * Write more Workspace Web tests
    Enable smoke gate    *  |  * Fix STATUS_BLOCKED bug
                            |  * Enable Kiwi TCMS
    ────────────────────────┼────────────────────────────
    Grafana metrics      *  |  * Framework unit tests
    Video recording      *  |  * Page Object Model
    PyPI publishing      *  |  * Retry logic for UI
                            |
                        LOW IMPACT

          LOW EFFORT ───────┼─────── HIGH EFFORT
```

**Start top-right, then top-left.** The biggest ROI is writing actual tests that use the framework you already built.

---

## TCMS & Test Documentation Convention

> Decision: **No BDD/Gherkin in Python code.** Gherkin is used as a documentation
> template inside Kiwi TCMS Test Case Text field only. Python tests stay native
> pytest with `tracked_step`. The two layers are linked via `@pytest.mark.tcms(case_id=X)`.

### Why Not pytest-bdd

1. **Step count** — Key ceremony and complex UI workflows have 20-30 granular steps.
   Gherkin forces a 1:1 step-definition-per-line, creating double maintenance
   (`.feature` file + step definitions) with no added value.
2. **Mixed test types** — Framework handles UI (pywinauto), console (subprocess),
   CLI (Java/Go/C++/GTest). BDD patterns fit UI awkwardly and console tests
   even worse (`When I run pkcs11-tool with args "--list-slots"` is not readable).
3. **Audience** — Test engineers, not PMs/BAs. Python is more readable for this team
   than Gherkin + step definitions.
4. **Existing tooling** — `tracked_step` + Allure decorators already provide
   structured, documented, evidence-rich test steps without a BDD layer.

### Two-Level Documentation Model

```
┌───────────────────────────────────────────────────────────┐
│  KIWI TCMS — Test Case (Source of Truth for Procedure)    │
│                                                           │
│  Summary: [E2E][eAdmin][Connect] Connect to Workspace           │
│  Text:                                                    │
│    Given eAdmin is launched on Windows client              │
│    When operator clicks Connect and confirms popup         │
│    Then dashboard loads and Workspace status shows Connected     │
│                                                           │
│  → High-level, business readable, 3-5 lines               │
│  → Follows oracle rules: objective, deterministic,        │
│    verifiable by evidence                                  │
└────────────────────────┬──────────────────────────────────┘
                         │  @pytest.mark.tcms(case_id=42)
                         │
┌────────────────────────▼──────────────────────────────────┐
│  Python Test — Implementation (Automation Code)           │
│                                                           │
│  with tracked_step("Given: eAdmin launched"):             │
│      assert driver.main_window.is_visible()               │
│                                                           │
│  with tracked_step("When: Connect and confirm popup"):    │
│      driver.click_button(auto_id="btnConnect")            │
│      driver.wait_for_element(auto_id="btnOK")             │
│      driver.click_button(auto_id="btnOK")                 │
│                                                           │
│  with tracked_step("Then: Dashboard loaded"):             │
│      assert driver.element_exists(name="Dashboard")       │
│                                                           │
│  → Granular, 20-30 steps, auto-screenshots per step       │
└───────────────────────────────────────────────────────────┘
                         │
                         ▼
┌───────────────────────────────────────────────────────────┐
│  Allure Report — Auto-Generated Evidence                  │
│                                                           │
│  Step 1: Given: eAdmin launched .............. PASS [img] │
│  Step 2: When: Connect and confirm popup ..... PASS [img] │
│  Step 3: Then: Dashboard loaded .............. PASS [img] │
│                                                           │
│  → Screenshots at every step, logs, timing                │
│  → Cross-referenceable with TCMS procedure                │
└───────────────────────────────────────────────────────────┘
```

### TCMS Naming Convention → Allure/pytest Mapping

TCMS Summary format: `[Test Level][Component][Feature] Test Name`

```python
# TCMS: [E2E][PKCS11][Sign] RSA sign + verify using Workspace key via Proxy

@allure.suite("E2E")                                    # [Test Level]
@allure.feature("PKCS11")                               # [Component]
@allure.story("Sign")                                   # [Feature]
@allure.title("RSA sign + verify using Workspace key via Proxy")
@allure.description(
    "Given Workspace is connected and key 'TestRSA' exists\n"
    "When client sends CLI C_Sign with RSA-PSS mechanism\n"
    "Then signature is returned (non-empty, correct length)\n"
    "And C_Verify with same key returns CKR_OK"
)
@pytest.mark.tcms(case_id=42)
@pytest.mark.pkcs11
```

| TCMS Field | Maps To | Example |
|------------|---------|---------|
| Summary `[E2E]` | `@allure.suite("E2E")` | Top-level grouping |
| Summary `[eAdmin]` | `@allure.feature("eAdmin")` | Component |
| Summary `[Connect]` | `@allure.story("Connect")` | Feature/journey |
| Summary test name | `@allure.title(...)` | Display name |
| Text (Given/When/Then) | `@allure.description(...)` + `tracked_step` labels | Procedure |
| Case ID | `@pytest.mark.tcms(case_id=X)` | Bidirectional link |
| Tags | `@allure.tag(...)` + `@pytest.mark.<marker>` | Filtering |

### `tracked_step` Labeling Convention

Use Given/When/Then prefixes in `tracked_step` labels to match TCMS procedure:

```python
# Given
with tracked_step(evidence, driver, "Given: Workspace connected, operator logged in"):
    ...

# When
with tracked_step(evidence, driver, "When: Generate RSA-2048 key 'MasterKey'"):
    ...

# Then
with tracked_step(evidence, driver, "Then: Key 'MasterKey' appears in key list"):
    ...
```

For multi-step procedures, group sub-steps under a single Given/When/Then:

```python
# When (complex: multiple sub-actions)
with tracked_step(evidence, driver, "When: Execute key ceremony"):
    driver.click_button(auto_id="btnKeyMgmt")
    driver.select_combobox(auto_id="cmbKeyType", value="RSA-2048")
    driver.type_text("MasterKey", auto_id="txtLabel")
    driver.click_button(auto_id="btnGenerate")
    driver.wait_for_element(auto_id="lblSuccess", timeout=30)
    driver.click_button(auto_id="btnConfirm")
```

### Oracle Rules (from TCMS doc)

Every `Then` / assertion must be:
- **Objective** — no subjective judgment
- **Deterministic** — same input → same result
- **Verifiable by evidence** — screenshot or log proves it
- **Not visual/subjective** — no "looks correct"

```python
# BAD oracle
assert driver.main_window.is_visible()  # "looks correct"

# GOOD oracle
assert driver.element_exists(auto_id="lblStatus"), (
    "Status label not found after connection"
)
status = driver.get_text(auto_id="lblStatus")
assert "Connected" in status, (
    f"Expected 'Connected' in status, got: '{status}'"
)
```

---

## Notes

- The framework is production-ready — it's the test suite that needs work
- Phase 2 (hardening) should be prioritized before onboarding more consumer repos
- Every feature in Tier 1 is a config change — zero code required
- Use `inspect_app.py` to discover Workspace Web UI elements before writing new tests
- `tracked_step` is the recommended pattern — avoid raw `StepTracker`
- TCMS Gherkin is documentation, not executable — keep Python tests native pytest


python scripts/inspect_app.py "C:\SPHERE_Workspace\Admin Application\AdminApp.exe" --record -r check_flow


Action plan :
1. Gimana klo kita mulai dari beberapa button yg ada di e-admin ini kita buat semacam pages/properties, pada dasarnya kan button akan selalu disitu , agar tidak redundant jadi bisa kita panggil saja setiap buth pages itu.
2. Dicoba handle kalo butuh list down 
3. bisa ga ngetrigrer automation di server lain ? OK