# 10 — Security Testing

## Learning Objectives
- Test APIs for SQL injection resilience
- Verify authentication requirements on endpoints
- Check security-related HTTP headers

## Concepts
Ankole's security module provides:
- `SQLInjectionPayloads` / `XSSPayloads` — Common attack payloads
- `test_injection_resilience()` — Automated injection testing
- `test_auth_endpoints_require_token()` — Auth enforcement verification
- `SecurityHeadersReport` — Security header analysis

## Exercise
1. `exercise_01_injection.py` — Test the sample API for injection vulnerabilities

## Verification
```bash
pytest docs/playground/10_security/ -v
```
