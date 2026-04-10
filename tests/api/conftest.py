"""Fixtures for API tests (httpx)."""

import pytest

from ankole.driver.api_driver import APIDriver
from ankole.plugin.config import load_config


@pytest.fixture(scope="session")
def api_config():
    """Load API-specific configuration."""
    cfg = load_config()
    return cfg.get("workspace", {}).get("api", {})


@pytest.fixture
def api_client(api_config):
    """Provide an unauthenticated API client."""
    client = APIDriver(
        base_url=api_config.get("base_url", "http://localhost:8000"),
        timeout=api_config.get("timeout", 30),
    )
    client.start()
    yield client
    client.close()


@pytest.fixture
def authed_api(api_client):
    """Provide an authenticated API client (logged in as admin)."""
    api_client.login("admin", "admin123")
    return api_client
