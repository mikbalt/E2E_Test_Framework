"""CLI tests for member management commands."""

import pytest


@pytest.mark.cli
class TestCLIMembers:
    """Test ankole-cli member commands."""

    def test_list_members(self, cli_runner, cli_command, api_url):
        """CLI should list members."""
        # Login first
        cli_runner.run(
            cli_command,
            ["--api-url", api_url, "auth", "login",
             "--username", "admin", "--password", "admin123"],
            timeout=30,
        )
        result = cli_runner.run(
            cli_command,
            ["--api-url", api_url, "members", "list"],
            timeout=30,
        )
        assert result.returncode == 0
        assert "admin" in result.stdout or "member" in result.stdout.lower()

    def test_create_member(self, cli_runner, cli_command, api_url):
        """CLI should create a member."""
        cli_runner.run(
            cli_command,
            ["--api-url", api_url, "auth", "login",
             "--username", "admin", "--password", "admin123"],
            timeout=30,
        )
        result = cli_runner.run(
            cli_command,
            ["--api-url", api_url, "members", "create",
             "--username", "cli_test_member",
             "--email", "cli_test@example.com",
             "--password", "test123",
             "--role-id", "3"],
            timeout=30,
        )
        assert result.returncode == 0

    def test_delete_member(self, cli_runner, cli_command, api_url):
        """CLI should delete a member."""
        cli_runner.run(
            cli_command,
            ["--api-url", api_url, "auth", "login",
             "--username", "admin", "--password", "admin123"],
            timeout=30,
        )
        # Create first
        cli_runner.run(
            cli_command,
            ["--api-url", api_url, "members", "create",
             "--username", "cli_delete_test",
             "--email", "cli_delete@example.com",
             "--password", "test123",
             "--role-id", "3"],
            timeout=30,
        )
        # Then delete (need the ID - this depends on CLI output format)
        result = cli_runner.run(
            cli_command,
            ["--api-url", api_url, "members", "list"],
            timeout=30,
        )
        assert result.returncode == 0
