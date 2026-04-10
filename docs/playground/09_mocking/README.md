# 09 — Mocking

## Learning Objectives
- Mock HTTP responses for API tests with respx
- Intercept browser network requests with Playwright routes
- Simulate network errors and slow responses

## Concepts
Ankole provides two mocking approaches:
- `APIMocker` — Uses respx to intercept httpx calls at the transport level
- `BrowserMocker` — Uses Playwright's `page.route()` to intercept browser requests

Both support response mocking, error simulation, and delay injection.

## Exercise
1. `exercise_01_mock_api.py` — Mock API responses in API and browser tests

## Verification
```bash
pytest docs/playground/09_mocking/ -v
```
