"""CLI tests for authentication commands."""

import pytest


@pytest.mark.cli
class TestCLIAuth:
    """Test ankole-cli auth commands."""

    def test_cli_login(self, cli_runner, cli_command, api_url):
        """CLI login should succeed with valid credentials."""
        result = cli_runner.run(
            cli_command,
            ["--api-url", api_url, "auth", "login",
             "--username", "admin", "--password", "admin123"],
            timeout=30,
        )
        assert result.returncode == 0

    def test_cli_login_invalid(self, cli_runner, cli_command, api_url):
        """CLI login should fail with invalid credentials."""
        result = cli_runner.run(
            cli_command,
            ["--api-url", api_url, "auth", "login",
             "--username", "admin", "--password", "wrong"],
            timeout=30,
        )
        assert result.returncode != 0

    def test_cli_logout(self, cli_runner, cli_command, api_url):
        """CLI logout should succeed."""
        # Login first
        cli_runner.run(
            cli_command,
            ["--api-url", api_url, "auth", "login",
             "--username", "admin", "--password", "admin123"],
            timeout=30,
        )
        # Then logout
        result = cli_runner.run(
            cli_command,
            ["--api-url", api_url, "auth", "logout"],
            timeout=30,
        )
        assert result.returncode == 0
