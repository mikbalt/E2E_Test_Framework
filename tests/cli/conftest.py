"""Fixtures for CLI tests."""

import pytest

from ankole.driver.console_runner import ConsoleRunner
from ankole.plugin.config import load_config


@pytest.fixture(scope="session")
def cli_config():
    """Load CLI-specific configuration."""
    cfg = load_config()
    return cfg.get("workspace", {}).get("cli", {})


@pytest.fixture
def cli_runner():
    """Provide a ConsoleRunner for CLI tests."""
    return ConsoleRunner()


@pytest.fixture
def cli_command(cli_config):
    """Get the CLI command name."""
    return cli_config.get("command", "ankole-cli")


@pytest.fixture
def api_url(cli_config):
    """Get the API URL for CLI commands."""
    return cli_config.get("api_url", "http://localhost:8000")
