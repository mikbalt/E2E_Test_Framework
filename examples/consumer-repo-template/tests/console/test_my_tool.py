"""
Example: Console test for a consumer repo.
Shows how to use the shared framework for CLI tool testing.
Works on both Windows and Linux.
"""

import allure
import pytest

from hsm_test_framework import ConsoleRunner, resolve_platform_config


@allure.suite("My Tool - Console Tests")
@pytest.mark.console
@pytest.mark.smoke
class TestMyTool:

    @pytest.fixture(autouse=True)
    def setup(self, config):
        self.runner = ConsoleRunner()
        self.config = config

    def _tool(self):
        raw = self.config.get("console_tools", {}).get("my_tool", {})
        return resolve_platform_config(raw)

    @allure.title("My Tool - Version Check")
    def test_version(self, evidence):
        tool = self._tool()
        result = self.runner.run(
            tool.get("command", "my-tool"),
            ["--version"],
            working_dir=tool.get("working_dir"),
            timeout=tool.get("timeout", 30),
        )
        evidence.attach_text(result.output, name="version_output")
        result.assert_success("Version check should succeed")

    @allure.title("My Tool - Health Check")
    def test_health(self, evidence):
        tool = self._tool()
        result = self.runner.run(
            tool.get("command", "my-tool"),
            ["health"],
            working_dir=tool.get("working_dir"),
            timeout=tool.get("timeout", 30),
        )
        evidence.attach_text(result.output, name="health_output")
        result.assert_success("Health check should pass")
        result.assert_output_contains("ok", case_sensitive=False)
