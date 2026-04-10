# 03 — API Driver

## Learning Objectives
- Use APIDriver for REST API testing
- Perform CRUD operations
- Validate responses with schema assertions

## Concepts
`APIDriver` wraps httpx with JWT token management. It provides `get()`, `post()`, `put()`, `delete()` methods that return `APIResponse` objects with chainable assertion helpers like `assert_status()`, `assert_json_key()`, `assert_schema()`, and `assert_json_schema()`.

## Exercises
1. `exercise_01_crud.py` — CRUD operations on members API
2. `exercise_02_schema_validation.py` — Validate API responses against schemas

## Verification
```bash
pytest docs/playground/03_api_driver/ -v
```
