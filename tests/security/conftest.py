"""Fixtures for OWASP security tests."""

import os

import pytest

from ankole.driver.api_driver import APIDriver
from ankole.plugin.config import load_config


@pytest.fixture(scope="session")
def security_config():
    """Load security-specific configuration."""
    cfg = load_config()
    return cfg.get("security", {})


@pytest.fixture(scope="session")
def api_config():
    """Load API configuration."""
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


@pytest.fixture
def member_api(api_config):
    """Provide a separate API client for member-level operations."""
    client = APIDriver(
        base_url=api_config.get("base_url", "http://localhost:8000"),
        timeout=api_config.get("timeout", 30),
    )
    client.start()
    yield client
    client.close()


@pytest.fixture
def zap_scanner(security_config):
    """Provide a ZAP scanner instance. Skips if ZAP is not configured."""
    zap_url = os.environ.get(
        "ZAP_API_URL",
        security_config.get("zap", {}).get("api_url", ""),
    )
    if not zap_url:
        pytest.skip("ZAP_API_URL not set — skipping ZAP tests")

    zap_key = os.environ.get(
        "ZAP_API_KEY",
        security_config.get("zap", {}).get("api_key", ""),
    )

    from ankole.driver.zap_scanner import ZAPScanner

    scanner = ZAPScanner(api_url=zap_url, api_key=zap_key)
    scanner.start()
    yield scanner
    scanner.close()


@pytest.fixture
def auth_token(api_config):
    """Return a raw JWT token for manual header testing."""
    client = APIDriver(
        base_url=api_config.get("base_url", "http://localhost:8000"),
        timeout=api_config.get("timeout", 30),
    )
    client.start()
    resp = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    token = resp.json().get("access_token", "") if resp.status_code == 200 else ""
    client.close()
    return token
