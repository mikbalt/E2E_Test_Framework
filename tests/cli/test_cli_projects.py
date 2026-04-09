"""CLI tests for project management commands."""

import pytest


@pytest.mark.cli
class TestCLIProjects:
    """Test ankole-cli project commands."""

    def test_list_projects(self, cli_runner, cli_command, api_url):
        """CLI should list projects."""
        cli_runner.run(
            cli_command,
            ["--api-url", api_url, "auth", "login",
             "--username", "admin", "--password", "admin123"],
            timeout=30,
        )
        result = cli_runner.run(
            cli_command,
            ["--api-url", api_url, "projects", "list"],
            timeout=30,
        )
        assert result.returncode == 0

    def test_create_project(self, cli_runner, cli_command, api_url):
        """CLI should create a project."""
        cli_runner.run(
            cli_command,
            ["--api-url", api_url, "auth", "login",
             "--username", "admin", "--password", "admin123"],
            timeout=30,
        )
        result = cli_runner.run(
            cli_command,
            ["--api-url", api_url, "projects", "create",
             "--name", "CLI Test Project",
             "--description", "Created by CLI test"],
            timeout=30,
        )
        assert result.returncode == 0

    def test_system_health(self, cli_runner, cli_command, api_url):
        """CLI health check should work without auth."""
        result = cli_runner.run(
            cli_command,
            ["--api-url", api_url, "system", "health"],
            timeout=30,
        )
        assert result.returncode == 0
