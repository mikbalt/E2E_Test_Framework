# Ankole Framework - Setup Guide

## Prerequisites

| Software | Version | Purpose |
|----------|---------|---------|
| Python | >= 3.10 | Framework runtime |
| Docker & Docker Compose | Latest | Sample apps + observability |
| Git | Any | Version control |

## Quick Setup (Docker)

```bash
# 1. Clone and enter project
git clone <repo-url>
cd ankole

# 2. Start all services
docker-compose up -d

# 3. Verify services are healthy
docker-compose ps

# 4. Install framework in development mode
pip install -e ".[all]"

# 5. Install Playwright browsers (for web tests)
playwright install chromium

# 6. Run tests
pytest tests/unit/ -v       # Unit tests (no Docker needed)
pytest tests/api/ -v        # API tests
pytest tests/web/ -v        # Web UI tests
```

## Environment Variables

Copy `.env.example` to `.env` and adjust:

```bash
cp .env.example .env
```

| Variable | Default | Description |
|----------|---------|-------------|
| `WORKSPACE_WEB_URL` | `http://localhost:5000` | Flask web app URL |
| `WORKSPACE_API_URL` | `http://localhost:8000` | FastAPI API URL |
| `DATABASE_URL` | `postgresql://ankole:ankole@localhost:5432/ankole` | PostgreSQL connection |
| `PUSHGATEWAY_URL` | `http://localhost:9091` | Prometheus Pushgateway |
| `LOKI_URL` | `http://localhost:3100` | Loki log aggregator |
| `ADMIN_USERNAME` | `admin` | Test admin username |
| `ADMIN_PASSWORD` | `admin123` | Test admin password |

## Running Tests

### By Category

```bash
pytest tests/unit/ -v           # Framework unit tests
pytest tests/api/ -v            # API integration tests
pytest tests/web/ -v            # Web UI tests (Playwright)
pytest tests/cli/ -v            # CLI tool tests
pytest tests/desktop/ -v        # Desktop tests (Windows only)
```

### By Marker

```bash
pytest -m smoke -v              # Smoke tests only
pytest -m critical -v           # Critical path tests
pytest -m flow -v               # Flow-based tests
pytest -m "not slow" -v         # Skip slow tests
```

### With Observability

```bash
# Push metrics to Grafana
pytest tests/ -v --alluredir=evidence/allure-results

# Enable smoke gate (fail-fast)
pytest tests/ --smoke-gate

# Skip health checks
pytest tests/ --skip-health-check
```

## Accessing Services

| Service | URL | Credentials |
|---------|-----|-------------|
| Web App | http://localhost:5000 | admin / admin123 |
| REST API | http://localhost:8000/docs | JWT auth |
| Grafana | http://localhost:3000 | admin / admin (or anonymous) |
| Prometheus | http://localhost:9090 | None |
| Allure | http://localhost:5050 | None (use `--profile reporting`) |

## Development

### Adding a New Page Object

```python
# ankole/pages/web/my_page.py
from ankole.pages.web.base_web_page import BaseWebPage

class MyPage(BaseWebPage):
    MY_BUTTON = "#my-button"

    def click_my_button(self):
        with self._web_step("Click my button"):
            self.driver.click(self.MY_BUTTON)
```

### Adding a New API Test

```python
# tests/api/test_my_endpoint.py
import pytest

@pytest.mark.api
class TestMyEndpoint:
    def test_get_data(self, authed_api):
        resp = authed_api.get("/api/my-endpoint")
        resp.assert_status(200)
        resp.assert_json_key("data")
```

### Adding a New Flow

```python
# ankole/flows/workspace/my_flow.py
from ankole.flows.base import Flow, Step

def my_flow(username, password):
    return Flow("My Flow", [
        Step("Login", lambda ctx: login(ctx, username, password)),
        Step("Do thing", lambda ctx: do_thing(ctx)),
    ])
```
