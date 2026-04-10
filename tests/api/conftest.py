"""Fixtures for API tests (httpx)."""

import logging

import pytest

from ankole.driver.api_driver import APIDriver
from ankole.plugin.config import load_config
from ankole.testing.data_factory import DataFactory

logger = logging.getLogger(__name__)


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


@pytest.fixture
def data_factory(authed_api):
    """Provide a DataFactory with shared cleanup tracker."""
    factory = DataFactory()
    yield factory
    errors = factory.cleanup_all()
    if errors:
        logger.warning(f"Cleanup errors: {errors}")


@pytest.fixture
def member_factory(data_factory, authed_api):
    """Factory that creates members via API and auto-deletes on teardown."""
    return lambda **kwargs: data_factory.members.create_via_api(authed_api, **kwargs)


@pytest.fixture
def role_factory(data_factory, authed_api):
    """Factory that creates roles via API and auto-deletes on teardown."""
    return lambda **kwargs: data_factory.roles.create_via_api(authed_api, **kwargs)


@pytest.fixture
def project_factory(data_factory, authed_api):
    """Factory that creates projects via API and auto-deletes on teardown."""
    return lambda **kwargs: data_factory.projects.create_via_api(authed_api, **kwargs)
