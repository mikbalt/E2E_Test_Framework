# 05 — Flows

## Learning Objectives
- Understand the Flow pattern for composable test scenarios
- Create a flow that chains multiple operations
- Reuse flows across tests

## Concepts
Flows are high-level test building blocks that compose multiple page actions or API calls into reusable scenarios. Ankole's flow engine in `ankole/flows/` provides a `BaseFlow` class. Flows receive drivers and orchestrate multi-step operations.

## Exercise
1. `exercise_01_compose_flow.py` — Create a flow that logs in and creates a member

## Verification
```bash
pytest docs/playground/05_flows/ -v
```
