"""
Sample Console Test - PKCS#11 Tools (Cross-Platform)

Demonstrates how to test console/CLI based tools (Golang, Java, C++ binaries).
Works on both Windows and Linux using platform-aware config resolution.

Run:
    pytest tests/console/test_pkcs11_sample.py -v
"""

import logging

import allure
import pytest

from hsm_test_framework import ConsoleRunner, resolve_platform_config

logger = logging.getLogger(__name__)


@allure.suite("Console Tests")
@allure.feature("PKCS#11")
@pytest.mark.console
@pytest.mark.pkcs11
class TestPKCS11Operations:
    """
    PKCS#11 console test examples.
    Demonstrates testing CLI tools written in Go, Java, and C++.
    Uses resolve_platform_config() for cross-platform path resolution.
    """

    @pytest.fixture(autouse=True)
    def setup(self, config):
        """Setup console runner with platform-aware config."""
        self.runner = ConsoleRunner()
        self.config = config

    def _get_tool_config(self, tool_name):
        """Get platform-resolved config for a console tool."""
        raw_config = self.config.get("console_tools", {}).get(tool_name, {})
        return resolve_platform_config(raw_config)

    # ==================================================================
    # Generic PKCS#11 Tool Tests
    # ==================================================================

    @allure.title("PKCS11 - List Available Slots")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    def test_list_slots(self, evidence):
        """Test: List PKCS#11 slots and verify HSM is detected."""
        tool = self._get_tool_config("pkcs11_native")

        result = self.runner.run(
            tool.get("command", "pkcs11-tool"),
            ["--list-slots"],
            working_dir=tool.get("working_dir"),
            timeout=tool.get("timeout", 30),
        )

        evidence.attach_text(
            f"Command: {result.command}\n"
            f"Return Code: {result.returncode}\n"
            f"Duration: {result.duration:.2f}s\n\n"
            f"--- STDOUT ---\n{result.stdout}\n\n"
            f"--- STDERR ---\n{result.stderr}",
            name="list_slots_output",
        )

        result.assert_success("pkcs11-tool --list-slots should succeed")
        result.assert_output_contains("Slot", case_sensitive=False)
        logger.info(f"Slots found:\n{result.stdout}")

    @allure.title("PKCS11 - List Objects/Keys")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_list_objects(self, evidence):
        """Test: List objects/keys in PKCS#11 token."""
        tool = self._get_tool_config("pkcs11_native")

        result = self.runner.run(
            tool.get("command", "pkcs11-tool"),
            ["--list-objects", "--login", "--pin", "env:HSM_PIN"],
            working_dir=tool.get("working_dir"),
            timeout=tool.get("timeout", 30),
        )

        evidence.attach_text(result.output, name="list_objects_output")
        result.assert_success("Should be able to list PKCS#11 objects")

    @allure.title("PKCS11 - Token Info")
    @allure.severity(allure.severity_level.NORMAL)
    def test_token_info(self, evidence):
        """Test: Get PKCS#11 token information."""
        tool = self._get_tool_config("pkcs11_native")

        result = self.runner.run(
            tool.get("command", "pkcs11-tool"),
            ["--list-token-slots"],
            working_dir=tool.get("working_dir"),
            timeout=tool.get("timeout", 30),
        )

        evidence.attach_text(result.output, name="token_info_output")
        result.assert_success("Token info query should succeed")

    # ==================================================================
    # Go Binary Tests
    # ==================================================================

    @allure.title("PKCS11-Go - Health Check")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    def test_go_pkcs11_health(self, evidence):
        """Test: Run Go-based PKCS#11 tool health check."""
        tool = self._get_tool_config("pkcs11_go")

        result = self.runner.run(
            tool.get("command", "pkcs11-go-tool"),
            ["health", "--verbose"],
            working_dir=tool.get("working_dir"),
            timeout=tool.get("timeout", 30),
        )

        evidence.attach_text(result.output, name="go_health_output")
        result.assert_success("Go PKCS#11 health check should pass")

    # ==================================================================
    # Java Tests
    # ==================================================================

    @allure.title("PKCS11-Java - Provider Test")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_java_pkcs11_provider(self, evidence):
        """Test: Run Java PKCS#11 provider verification."""
        tool = self._get_tool_config("pkcs11_java")
        args = tool.get("args", [])
        jar_path = args[1] if len(args) > 1 and args[0] == "-jar" else None

        result = self.runner.run_java(
            jar_path=jar_path,
            args=["--test-provider"],
            working_dir=tool.get("working_dir"),
            timeout=tool.get("timeout", 60),
        )

        evidence.attach_text(result.output, name="java_provider_output")
        result.assert_success("Java PKCS#11 provider should load successfully")

    # ==================================================================
    # C++ Binary Tests
    # ==================================================================

    @allure.title("PKCS11-C++ - Initialization Test")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_cpp_pkcs11_init(self, evidence):
        """Test: Run C++ PKCS#11 initialization test."""
        tool = self._get_tool_config("pkcs11_cpp")

        result = self.runner.run(
            tool.get("command", "pkcs11_test"),
            ["--init", "--verbose"],
            working_dir=tool.get("working_dir"),
            timeout=tool.get("timeout", 30),
        )

        evidence.attach_text(result.output, name="cpp_init_output")
        result.assert_success("C++ PKCS#11 initialization should succeed")

    # ==================================================================
    # Cross-language Verification
    # ==================================================================

    @allure.title("PKCS11 - Cross-language Key Listing Consistency")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.regression
    def test_cross_language_key_listing(self, evidence):
        """Test: Verify all PKCS#11 implementations see the same keys."""
        native_tool = self._get_tool_config("pkcs11_native")

        evidence.step("Run key listing from pkcs11-tool")
        native_result = self.runner.run(
            native_tool.get("command", "pkcs11-tool"),
            ["--list-objects", "--type", "pubkey"],
            working_dir=native_tool.get("working_dir"),
            timeout=30,
        )

        evidence.attach_text(native_result.output, name="native_key_listing")
        evidence.log("Cross-language verification placeholder - extend as needed")
