"""
PKCS#11 C++ Tests — Python wrappers for pre-compiled C++ executables.

These tests wrap EXISTING C++ binaries that are already compiled.
The C++ source code and build process are NOT touched.

Test types:
- pkcs11_cpp_encrypt     : Encryption operations (pre-compiled executable)
- pkcs11_cpp_token_mgmt  : Token management (pre-compiled executable)

Each C++ tool has its own log path configured in settings.yaml.
The LogCollector automatically picks up those logs and attaches
them to the Allure report.

Usage:
    pytest tests/console/test_pkcs11_cpp.py -v
    pytest -m cpp -v
"""

import os

import allure
import pytest

from hsm_test_framework import ConsoleRunner, LogCollector, resolve_platform_config


@allure.epic("PKCS#11")
@allure.feature("C++ Native Tests")
@pytest.mark.console
@pytest.mark.pkcs11
@pytest.mark.cpp
class TestPKCS11CppEncrypt:
    """
    PKCS#11 Encryption — C++ native executable (pre-compiled).

    Wraps: bin/pkcs11_encrypt.exe (Windows) / bin/pkcs11_encrypt (Linux)
    Logs:  logs/cpp/*.log (directory-based, multiple log files)
    """

    def _tool(self, config):
        return resolve_platform_config(config["console_tools"]["pkcs11_cpp_encrypt"])

    @allure.story("AES Encryption")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    def test_aes_encrypt(self, config, console, evidence, log_collector):
        """Test AES-256-CBC encryption via C++ PKCS#11 tool."""
        tool = self._tool(config)

        if not os.path.exists(tool["command"]):
            pytest.skip(f"Binary not found: {tool['command']}")

        # Monitor log directory for new files during execution
        evidence.step("Run C++ PKCS#11 AES-256 encryption")
        result = console.run_executable(
            exe_path=tool["command"],
            args=["--encrypt", "--algorithm", "AES-256-CBC", "--input", "testdata.bin"],
            timeout=tool.get("timeout", 60),
        )

        # Capture evidence: stdout + tool's own log files
        evidence.attach_text(result.output, "cpp_aes_encrypt_stdout")
        log_collector.collect_from_config(tool)

        evidence.step("Validate AES encryption result")
        result.assert_success()
        result.assert_output_not_contains("error", case_sensitive=False)

    @allure.story("AES Decryption")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_aes_decrypt(self, config, console, evidence, log_collector):
        """Test AES-256-CBC decryption via C++ PKCS#11 tool."""
        tool = self._tool(config)

        if not os.path.exists(tool["command"]):
            pytest.skip(f"Binary not found: {tool['command']}")

        evidence.step("Run C++ PKCS#11 AES-256 decryption")
        result = console.run_executable(
            exe_path=tool["command"],
            args=["--decrypt", "--algorithm", "AES-256-CBC", "--input", "encrypted.bin"],
            timeout=tool.get("timeout", 60),
        )

        evidence.attach_text(result.output, "cpp_aes_decrypt_stdout")
        log_collector.collect_from_config(tool)

        evidence.step("Validate AES decryption result")
        result.assert_success()

    @allure.story("RSA Encryption")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_rsa_encrypt(self, config, console, evidence, log_collector):
        """Test RSA encryption via C++ PKCS#11 tool."""
        tool = self._tool(config)

        if not os.path.exists(tool["command"]):
            pytest.skip(f"Binary not found: {tool['command']}")

        evidence.step("Run C++ PKCS#11 RSA encryption")
        result = console.run_executable(
            exe_path=tool["command"],
            args=["--encrypt", "--algorithm", "RSA-OAEP", "--key-label", "rsa-key"],
            timeout=tool.get("timeout", 60),
        )

        evidence.attach_text(result.output, "cpp_rsa_encrypt_stdout")
        log_collector.collect_from_config(tool)

        evidence.step("Validate RSA encryption result")
        result.assert_success()


@allure.epic("PKCS#11")
@allure.feature("C++ Native Tests")
@pytest.mark.console
@pytest.mark.pkcs11
@pytest.mark.cpp
class TestPKCS11CppTokenMgmt:
    """
    PKCS#11 Token Management — C++ native executable (pre-compiled).

    Wraps: bin/pkcs11_token_mgmt.exe (Windows) / bin/pkcs11_token_mgmt (Linux)
    Logs:  logs/cpp_token.log (single log file)
    """

    def _tool(self, config):
        return resolve_platform_config(config["console_tools"]["pkcs11_cpp_token_mgmt"])

    @allure.story("List Slots")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.smoke
    def test_list_slots(self, config, console, evidence, log_collector):
        """Test listing PKCS#11 slots via C++ tool."""
        tool = self._tool(config)

        if not os.path.exists(tool["command"]):
            pytest.skip(f"Binary not found: {tool['command']}")

        # Monitor the tool's log file in real time
        log_path = tool.get("log_path", "")
        with log_collector.monitor(log_path) as log_mon:
            evidence.step("Run C++ PKCS#11 list slots")
            result = console.run_executable(
                exe_path=tool["command"],
                args=["--list-slots"],
                timeout=tool.get("timeout", 90),
            )

        evidence.attach_text(result.output, "cpp_list_slots_stdout")
        if log_mon.captured:
            log_collector.collect_text(log_mon.captured, "cpp_token_runtime_log")

        evidence.step("Validate slot listing")
        result.assert_success()
        result.assert_output_contains("slot", case_sensitive=False)

    @allure.story("Token Info")
    @allure.severity(allure.severity_level.NORMAL)
    def test_token_info(self, config, console, evidence, log_collector):
        """Test getting token information via C++ tool."""
        tool = self._tool(config)

        if not os.path.exists(tool["command"]):
            pytest.skip(f"Binary not found: {tool['command']}")

        evidence.step("Run C++ PKCS#11 token info")
        result = console.run_executable(
            exe_path=tool["command"],
            args=["--token-info", "--slot", "0"],
            timeout=tool.get("timeout", 90),
        )

        evidence.attach_text(result.output, "cpp_token_info_stdout")
        log_collector.collect_from_config(tool)

        evidence.step("Validate token info output")
        result.assert_success()

    @allure.story("Initialize Token")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.regression
    def test_init_token(self, config, console, evidence, log_collector):
        """Test token initialization via C++ tool."""
        tool = self._tool(config)

        if not os.path.exists(tool["command"]):
            pytest.skip(f"Binary not found: {tool['command']}")

        evidence.step("Run C++ PKCS#11 init token")
        result = console.run_executable(
            exe_path=tool["command"],
            args=["--init-token", "--slot", "0", "--label", "TestToken",
                   "--so-pin", "12345678"],
            timeout=tool.get("timeout", 90),
        )

        evidence.attach_text(result.output, "cpp_init_token_stdout")
        log_collector.collect_from_config(tool)

        evidence.step("Validate token initialization")
        result.assert_success()
