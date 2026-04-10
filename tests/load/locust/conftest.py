"""Fixtures for Locust load tests."""

import os

import pytest

from ankole.plugin.config import load_config


@pytest.fixture(scope="session")
def load_config_data():
    """Load the load_testing configuration section."""
    cfg = load_config()
    return cfg.get("load_testing", {}).get("locust", {})


@pytest.fixture(scope="session")
def locust_config(load_config_data):
    """Provide Locust run parameters from config or env vars."""
    return {
        "users": int(os.environ.get("LOCUST_USERS", load_config_data.get("users", 10))),
        "spawn_rate": int(
            os.environ.get("LOCUST_SPAWN_RATE", load_config_data.get("spawn_rate", 2))
        ),
        "run_time": os.environ.get(
            "LOCUST_RUN_TIME", load_config_data.get("run_time", "30s")
        ),
    }


@pytest.fixture(scope="session")
def target_url(load_config_data):
    """Target host URL for Locust."""
    return os.environ.get(
        "WORKSPACE_API_URL",
        load_config_data.get("target_host", "http://localhost:8000"),
    )
