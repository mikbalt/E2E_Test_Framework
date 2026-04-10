# 08 — Accessibility

## Learning Objectives
- Run WCAG compliance scans with axe-core
- Understand violation impacts (critical, serious, moderate, minor)
- Scope scans to specific page sections

## Concepts
`A11yScanner` injects the axe-core library into Playwright pages via CDN and runs accessibility audits. Results come back as `A11yReport` with violations categorized by impact level. Use `assert_no_violations(impact=["critical", "serious"])` to enforce standards.

## Exercise
1. `exercise_01_scan.py` — Scan the login page for accessibility violations

## Verification
```bash
pytest docs/playground/08_accessibility/ -v
```
