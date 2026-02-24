# HSM Test Framework — Roadmap & TODO

## Status Legend
- [ ] Not started
- [x] Done
- [~] In progress

---

## Phase 1: Foundation (DONE)

- [x] Core framework: UIDriver, ConsoleRunner, Evidence
- [x] pytest plugin with auto-registered fixtures and hooks
- [x] Cross-platform support (Windows + Linux)
- [x] Platform-aware config resolution (`command_windows` / `command_linux`)
- [x] Auto-skip UI tests on non-Windows
- [x] Screenshot on failure
- [x] Allure reporting integration
- [x] Kiwi TCMS integration
- [x] Grafana/Prometheus metrics push
- [x] Jenkinsfile (multi-agent, parallel Windows + Linux)
- [x] Consumer repo template (UI + general)
- [x] Setup scripts with auto Python version detection
- [x] SETUP_GUIDE.md
- [x] PRESENTATION.md (executive summary for managers)
- [x] UI Inspector tool (`scripts/inspect_app.py`) — discover element IDs
- [x] Per-part test execution (markers: ui, console, pkcs11, smoke, regression)

## Phase 1.5: PKCS#11 Integration & Log Collection (DONE)

- [x] `LogCollector` module — collect external log files as evidence
- [x] `LogMonitor` — real-time log capture during test execution (only new lines)
- [x] GTest XML parser — parse Google Test reports, create readable summaries
- [x] Auto-collect from config (`collect_from_config` reads log_path, log_dir, gtest_xml)
- [x] Large file handling — auto-tail files >10MB (last 500 lines)
- [x] `log_collector` fixture — auto-available in all consumer repos
- [x] `ConsoleRunner` enhancements: `run_make()`, `run_cmake_build()`, `run_executable()`
- [x] PKCS#11 consumer repo template with 4 test types:
  - [x] Java wrapper tests (pre-built JAR + Maven-built JAR)
  - [x] C++ wrapper tests (pre-compiled executables)
  - [x] Go wrapper tests (source built via `go build`)
  - [x] Google Test wrapper tests (built via Makefile, XML parsed)
- [x] Build scripts (`build.sh`/`build.bat`) — Java Maven, Go build, Makefile
- [x] Auto-build session fixture (compiles before test session, skippable via `BUILD_SKIP=1`)
- [x] New markers: `java`, `cpp`, `go_test`, `gtest`, `needs_build`
- [x] Jenkinsfile for PKCS#11 (Build → Test → Report pipeline)
- [x] Updated SETUP_GUIDE.md with PKCS#11 setup instructions
- [x] Updated README.md with full feature documentation

---

## Phase 2: Harden for Production

### Testing the Framework Itself
- [ ] Add unit tests for `console_runner.py` (mock subprocess, test assertions)
- [ ] Add unit tests for `evidence.py` (mock file I/O, test Allure attach)
- [ ] Add unit tests for `resolve_platform_config()`
- [ ] Add unit tests for `kiwi_tcms.py` (mock XML-RPC calls)
- [ ] Add integration test: full pipeline dry run on both platforms
- [ ] CI pipeline for the framework repo itself (test on push)

### Error Handling & Resilience
- [ ] Retry logic for flaky UI interactions (configurable retry count + delay)
- [ ] Graceful cleanup if app crashes mid-test (process kill fallback)
- [ ] Timeout per-step (not just per-test) for long-running operations
- [ ] Better error messages when app window not found (suggest `print_control_tree`)

### Configuration
- [ ] Environment variable overrides for all settings (e.g., `HSM_APP_PATH`)
- [ ] `.env` file auto-loading (python-dotenv)
- [ ] Config validation on startup (warn on missing required fields)
- [ ] Per-test config overrides via pytest markers or fixtures

---

## Phase 3: Enhanced Evidence & Reporting

### Video Recording
- [ ] Screen recording via ffmpeg (start on test begin, stop on test end)
- [ ] Attach video to Allure report on failure
- [ ] Configurable: record always vs. record on failure only
- [ ] Video compression settings in settings.yaml

### Enhanced Screenshots
- [ ] Element-level screenshots (capture just the target control, not full window)
- [ ] Diff screenshots (compare before/after for visual regression)
- [ ] Annotated screenshots (highlight clicked element with red border)

### Reporting Enhancements
- [ ] Slack/Teams webhook notification on test failure
- [ ] Email notification via Jenkins (already scaffolded, needs activation)
- [ ] Custom Allure categories (map test markers to Allure categories)
- [ ] Test execution timeline in Allure (step durations visualized)
- [ ] Historical trend comparison (this run vs. last 5 runs)

---

## Phase 4: Advanced Test Capabilities

### UI Testing
- [ ] Page Object Model (POM) base class for structured UI test design
- [ ] UI element wait strategies (wait for text change, wait for element count)
- [ ] Keyboard shortcut support (send hotkeys like Ctrl+S, Alt+F4)
- [ ] Multi-window support (handle dialogs, popups, message boxes)
- [ ] Drag-and-drop support
- [ ] Table/Grid element helpers (read cell values, click row)

### Console Testing
- [ ] Interactive console support (expect-style: send input, wait for prompt)
- [ ] Output pattern matching with regex assertions
- [ ] Performance benchmarking (measure command duration, fail if too slow)
- [ ] Parallel console command execution (run multiple tools simultaneously)
- [ ] SSH remote execution (run console tests on remote machines)

### PKCS#11 Specific
- [ ] Dedicated PKCS11 helper class (wraps common pkcs11-tool commands)
- [ ] Key generation test helpers
- [ ] Sign/verify/encrypt/decrypt test helpers
- [ ] Token lifecycle tests (init, login, operation, logout)
- [ ] Multi-slot support
- [ ] HSM health monitoring integration

---

## Phase 5: Scale & Ecosystem

### Framework Distribution
- [ ] Publish to private PyPI registry (instead of git+url install)
- [ ] Semantic versioning with CHANGELOG.md
- [ ] Version pinning support in consumer repos
- [ ] Migration guide between framework versions

### Multi-Repo Orchestration
- [ ] Central dashboard aggregating results from all consumer repos
- [ ] Unified Grafana dashboard (all repos → one view)
- [ ] Cross-repo test dependency management
- [ ] Nightly regression run across all consumer repos (Jenkins multi-branch)

### Developer Experience
- [ ] CLI tool: `hsm-test init` to scaffold a new consumer repo
- [ ] CLI tool: `hsm-test discover` to scan app and generate test skeleton
- [ ] VS Code snippets / templates for common test patterns
- [ ] Cookiecutter template as alternative to examples/consumer-repo-template

### Advanced CI/CD
- [ ] Docker-based Linux runner (Dockerfile for consistent Linux env)
- [ ] Matrix builds (test against multiple HSM firmware versions)
- [ ] Canary testing (run subset before full regression)
- [ ] Test impact analysis (only run tests affected by code changes)
- [ ] Parallel test execution within a single agent (pytest-xdist)

---

## Ideas / Nice-to-Have

- [ ] AI-assisted test generation (scan UI control tree → suggest tests)
- [ ] Self-healing locators (auto-update element IDs if app UI changes)
- [ ] Performance profiling dashboard (track HSM operation latency over time)
- [ ] Accessibility testing integration (Windows UI Automation accessibility checks)
- [ ] API testing module (for HSM REST APIs, if applicable)
- [ ] Database verification helpers (check DB state after operations)
- [ ] Test data management (fixtures for generating test keys, certs, etc.)
- [ ] Custom Allure plugin for HSM-specific metadata (slot info, firmware version)

---

## Notes

- Phase 1 + 1.5 are complete and ready for production use
- Phase 2 should be prioritized before scaling to more consumer repos
- Phases 3-5 can be tackled incrementally based on team needs
- Each phase is independent — pick what matters most for your workflow
- LogCollector + PKCS#11 templates are fully documented in README.md and SETUP_GUIDE.md
