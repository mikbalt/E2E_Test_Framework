# 02 — Web Driver

## Learning Objectives
- Use WebDriver to navigate and interact with web pages
- Fill forms, click buttons, read text
- Extract table data from the DOM

## Concepts
`WebDriver` wraps Playwright's sync API. It provides methods like `goto()`, `fill()`, `click()`, `get_text()`, and `get_table_data()`. The `web_driver` fixture handles browser lifecycle.

## Exercises
1. `exercise_01_login.py` — Navigate to login page, fill credentials, submit, verify redirect
2. `exercise_02_table_data.py` — Navigate to members page, extract table data, assert contents

## Verification
```bash
pytest docs/playground/02_web_driver/ -v
```
