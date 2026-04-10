# 11 — Parallel Execution & CI

## Learning Objectives
- Run tests in parallel with pytest-xdist
- Understand worker isolation for evidence directories
- Configure CI pipelines for the framework

## Concepts
`pytest-xdist` runs tests across multiple worker processes. Ankole provides:
- `get_worker_id()` / `worker_port_offset()` — Worker-aware helpers
- `worker_safe_evidence_dir()` — Isolated evidence per worker
- Thread-safe config loading with `_CONFIG_LOCK`

Run parallel: `pytest tests/ -n 2`

## Exercise
1. `exercise_01_xdist.py` — Verify parallel execution helpers work correctly

## Verification
```bash
pytest docs/playground/11_parallel_and_ci/ -v
```
