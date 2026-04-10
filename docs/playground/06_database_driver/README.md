# 06 — Database Driver

## Learning Objectives
- Connect to PostgreSQL directly in tests
- Use assertion helpers to verify database state
- Understand autorollback for test isolation

## Concepts
`DBDriver` wraps psycopg2 and provides assertion methods: `assert_row_exists()`, `assert_row_count()`, `assert_column_value()`. With `autorollback=True`, all changes are rolled back when the driver closes, ensuring test isolation.

## Exercise
1. `exercise_01_assertions.py` — Query the database and make assertions

## Verification
```bash
pytest docs/playground/06_database_driver/ -v
```
