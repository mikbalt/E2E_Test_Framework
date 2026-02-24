"""
PKCS#11 Java Tests — Python wrappers for Java JAR executables.

These tests do NOT modify or replace the Java code. They:
1. Run the existing Java JARs via subprocess
2. Capture stdout, stderr, and external log files
3. Validate results (exit code, expected output)
4. Attach all evidence to Allure report

Test types:
- pkcs11_java_keygen  : Pre-built JAR (ready binary, no compilation needed)
- pkcs11_java_signing : Built from source (Maven) — build.sh handles compilation

Usage:
    pytest tests/console/test_pkcs11_java.py -v
    pytest -m java -v
"""

import os

import allure
import pytest

from hsm_test_framework import ConsoleRunner, LogCollector, resolve_platform_config


@allure.epic("PKCS#11")
@allure.feature("Java Tests")
@pytest.mark.console
@pytest.mark.pkcs11
@pytest.mark.java
class TestPKCS11JavaKeygen:
    """
    PKCS#11 Key Generation — Java (pre-built JAR).

    Wraps: bin/pkcs11-keygen.jar
    This JAR is committed as a binary — no build step needed.
    """

    def _tool(self, config):
        """Resolve platform config for this tool."""
        return resolve_platform_config(config["console_tools"]["pkcs11_java_keygen"])

    @allure.story("RSA Key Generation")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    def test_rsa_keygen(self, config, console, evidence, log_collector):
        """Test RSA-2048 key generation via Java PKCS#11 tool."""
        tool = self._tool(config)
        timeout = tool.get("timeout", 60)

        # Monitor the tool's own log file during execution
        with log_collector.monitor(tool.get("log_path", "")) as log_mon:
            evidence.step("Run Java PKCS#11 keygen: RSA-2048")
            result = console.run_java(
                jar_path=tool["command"],
                args=["--keygen", "--type", "RSA", "--size", "2048"],
                timeout=timeout,
            )

        # Attach evidence
        evidence.attach_text(result.output, "java_keygen_stdout")
        if log_mon.captured:
            log_collector.collect_text(log_mon.captured, "java_keygen_runtime_log")

        # Collect the tool's log file (full content)
        log_collector.collect_from_config(tool)

        # Validate
        evidence.step("Validate RSA key generation result")
        result.assert_success()
        result.assert_output_contains("key generated", case_sensitive=False)

    @allure.story("EC Key Generation")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_ec_keygen(self, config, console, evidence, log_collector):
        """Test EC P-256 key generation via Java PKCS#11 tool."""
        tool = self._tool(config)

        evidence.step("Run Java PKCS#11 keygen: EC P-256")
        result = console.run_java(
            jar_path=tool["command"],
            args=["--keygen", "--type", "EC", "--curve", "P-256"],
            timeout=tool.get("timeout", 60),
        )

        evidence.attach_text(result.output, "java_ec_keygen_stdout")
        log_collector.collect_from_config(tool)

        evidence.step("Validate EC key generation result")
        result.assert_success()
        result.assert_output_contains("key generated", case_sensitive=False)

    @allure.story("List Keys")
    @allure.severity(allure.severity_level.NORMAL)
    def test_list_keys(self, config, console, evidence, log_collector):
        """Test listing keys in the HSM via Java tool."""
        tool = self._tool(config)

        evidence.step("Run Java PKCS#11 list keys")
        result = console.run_java(
            jar_path=tool["command"],
            args=["--list-keys"],
            timeout=tool.get("timeout", 60),
        )

        evidence.attach_text(result.output, "java_list_keys_stdout")
        log_collector.collect_from_config(tool)

        evidence.step("Validate key listing")
        result.assert_success()


@allure.epic("PKCS#11")
@allure.feature("Java Tests")
@pytest.mark.console
@pytest.mark.pkcs11
@pytest.mark.java
@pytest.mark.needs_build
class TestPKCS11JavaSigning:
    """
    PKCS#11 Digital Signing — Java (built from source).

    Wraps: bin/pkcs11-signing.jar
    Source: src/java/signing/ (built via Maven by build.sh)

    The conftest.py 'build_artifacts' fixture ensures this is compiled
    before the test session starts.
    """

    def _tool(self, config):
        """Resolve platform config for this tool."""
        return resolve_platform_config(config["console_tools"]["pkcs11_java_signing"])

    @allure.story("RSA Signing")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    def test_rsa_sign(self, config, console, evidence, log_collector):
        """Test RSA signing operation via Java PKCS#11 tool."""
        tool = self._tool(config)

        # Verify binary exists (was built)
        if not os.path.exists(tool["command"]):
            pytest.skip(f"Binary not found: {tool['command']} (build may have been skipped)")

        evidence.step("Run Java PKCS#11 RSA signing")
        result = console.run_java(
            jar_path=tool["command"],
            args=["--sign", "--algorithm", "SHA256withRSA", "--key-label", "test-key"],
            timeout=tool.get("timeout", 60),
        )

        evidence.attach_text(result.output, "java_rsa_sign_stdout")
        log_collector.collect_from_config(tool)

        evidence.step("Validate RSA signing result")
        result.assert_success()
        result.assert_output_contains("signature", case_sensitive=False)

    @allure.story("RSA Verify")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_rsa_verify(self, config, console, evidence, log_collector):
        """Test RSA signature verification via Java PKCS#11 tool."""
        tool = self._tool(config)

        if not os.path.exists(tool["command"]):
            pytest.skip(f"Binary not found: {tool['command']}")

        evidence.step("Run Java PKCS#11 RSA verify")
        result = console.run_java(
            jar_path=tool["command"],
            args=["--verify", "--algorithm", "SHA256withRSA", "--key-label", "test-key"],
            timeout=tool.get("timeout", 60),
        )

        evidence.attach_text(result.output, "java_rsa_verify_stdout")
        log_collector.collect_from_config(tool)

        evidence.step("Validate RSA verification result")
        result.assert_success()
        result.assert_output_contains("verified", case_sensitive=False)
