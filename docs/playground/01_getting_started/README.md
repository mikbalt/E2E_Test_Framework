# 01 — Getting Started

## Learning Objectives
- Understand the Ankole Framework structure
- Write and run your first test
- Use pytest markers and fixtures

## Concepts
Ankole is a multi-driver E2E test framework. Tests use **fixtures** (provided by the plugin) and **markers** (to categorize tests). The framework auto-registers its pytest plugin, so fixtures like `config` and `evidence` are available everywhere.

## Exercise
Open `exercise_01_first_test.py` and complete the TODOs:
1. Write a test that loads config and asserts it is a dict
2. Write a test that creates an Evidence instance and verifies the directory exists

## Verification
```bash
pytest docs/playground/01_getting_started/ -v
```

## Going Further
- Explore `config/settings.yaml` to see all configuration options
- Try adding a custom marker to your test
