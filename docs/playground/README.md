# Ankole Framework Playground

Welcome to the Ankole Framework interactive playground! Learn the framework step-by-step through hands-on exercises.

## Prerequisites

- Python 3.10+
- Docker and Docker Compose
- Framework installed: `pip install -e ".[all]"`
- Playwright browsers: `playwright install chromium`

## Quick Start

1. Start the sample apps:
   ```bash
   docker-compose -f docs/playground/docker-compose.playground.yml up -d
   ```

2. Work through tutorials in order (01 through 11)

3. Each tutorial has:
   - **README.md** — Learning objectives, concepts, instructions
   - **exercise_*.py** — Skeleton tests with `TODO` markers for you to fill in
   - **solutions/** — Complete working solutions to check your work

4. Run exercises:
   ```bash
   pytest docs/playground/01_getting_started/ -v
   ```

5. Run all solutions to verify setup:
   ```bash
   pytest docs/playground/ -v
   ```

## Tutorial Map

| # | Topic | What You Learn |
|---|-------|---------------|
| 01 | Getting Started | Write your first Ankole test |
| 02 | Web Driver | Playwright-based UI automation |
| 03 | API Driver | REST API testing with httpx |
| 04 | Page Objects | Page Object Model pattern |
| 05 | Flows | Composable test flows |
| 06 | Database Driver | Direct DB assertions |
| 07 | Visual Regression | Screenshot comparison testing |
| 08 | Accessibility | WCAG compliance with axe-core |
| 09 | Mocking | API and browser request mocking |
| 10 | Security | Injection and auth testing |
| 11 | Parallel & CI | pytest-xdist and CI pipelines |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `WORKSPACE_WEB_URL` | `http://localhost:5000` | Web app URL |
| `WORKSPACE_API_URL` | `http://localhost:8000` | API URL |
| `DATABASE_URL` | `postgresql://ankole:ankole@localhost:5432/ankole` | PostgreSQL DSN |
