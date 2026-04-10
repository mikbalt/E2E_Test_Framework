# 04 — Page Objects

## Learning Objectives
- Understand the Page Object Model (POM) pattern
- Create a reusable page class
- Use page objects in tests for cleaner code

## Concepts
Page Objects encapsulate page-specific selectors and actions into classes. Ankole provides `BaseWebPage` as a foundation. Each page object receives a `WebDriver` and exposes domain-specific methods instead of raw selectors.

## Exercise
1. `exercise_01_create_page.py` — Create a LoginPage class and use it in a test

## Verification
```bash
pytest docs/playground/04_page_objects/ -v
```
