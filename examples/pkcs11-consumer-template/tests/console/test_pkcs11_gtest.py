"""
PKCS#11 Google Test (C++) — Python wrapper for GTest executables.

Google Test binaries produce their own XML report (--gtest_output).
This wrapper:
1. Runs the GTest binary with XML output enabled
2. Parses the GTest XML to extract individual test results
3. Maps each GTest case to a pytest test (so Allure shows them all)
4. Collects the XML report + log files as evidence

The key difference from regular C++ tests:
- GTest binaries have built-in test logic and assertions
- We trust the GTest exit code AND parse the XML for detailed results
- Each GTest suite/case becomes visible in the Allure report

Test types:
- pkcs11_gtest_crypto : Crypto operations test suite (built via Makefile)

Usage:
    pytest tests/console/test_pkcs11_gtest.py -v
    pytest -m gtest -v
"""

import os

import allure
import pytest

from hsm_test_framework import ConsoleRunner, LogCollector, resolve_platform_config


@allure.epic("PKCS#11")
@allure.feature("Google Test Suite")
@pytest.mark.console
@pytest.mark.pkcs11
@pytest.mark.gtest
@pytest.mark.needs_build
class TestPKCS11GTestCrypto:
    """
    PKCS#11 Crypto Operations — Google Test (C++, built via Makefile).

    Wraps: bin/pkcs11_gtest_crypto.exe (Windows) / bin/pkcs11_gtest_crypto (Linux)
    Source: src/cpp/gtest_crypto/ (built via Makefile by build.sh)
    Output: evidence/gtest_crypto_results.xml (GTest XML report)
    Logs: logs/gtest/*.log

    The Makefile handles compilation and linking with Google Test.
    """

    def _tool(self, config):
        return resolve_platform_config(config["console_tools"]["pkcs11_gtest_crypto"])

    @allure.story("Run Full GTest Suite")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    def test_run_full_suite(self, config, console, evidence, log_collector):
        """
        Run the full Google Test crypto suite and validate results.

        This executes the GTest binary with XML output, then:
        - Parses the XML to show individual test results in evidence
        - Attaches the full XML report to Allure
        - Collects any log files produced during execution
        """
        tool = self._tool(config)

        if not os.path.exists(tool["command"]):
            pytest.skip(f"Binary not found: {tool['command']} (run build.sh gtest first)")

        # Determine GTest XML output path
        gtest_xml = tool.get("gtest_xml", "evidence/gtest_crypto_results.xml")
        os.makedirs(os.path.dirname(gtest_xml) or ".", exist_ok=True)

        evidence.step("Run Google Test PKCS#11 crypto suite")
        result = console.run_executable(
            exe_path=tool["command"],
            args=[
                f"--gtest_output=xml:{gtest_xml}",
                "--gtest_color=no",
            ],
            timeout=tool.get("timeout", 120),
        )

        # Attach stdout/stderr
        evidence.attach_text(result.output, "gtest_crypto_stdout")

        # Parse and attach GTest XML report
        evidence.step("Collect GTest XML report")
        gtest_results = log_collector.collect_gtest_xml(gtest_xml, name="gtest_crypto_report")

        # Collect log files from the tool
        log_collector.collect_from_config(tool)

        # Validate overall result
        evidence.step("Validate Google Test results")
        result.assert_success()

        # Additional validation from parsed XML
        if gtest_results:
            total = gtest_results["total"]
            failures = gtest_results["failures"]
            errors = gtest_results["errors"]
            evidence.log(f"GTest: {total} total, {failures} failures, {errors} errors")

            assert failures == 0, (
                f"GTest reported {failures} failures out of {total} tests. "
                f"See gtest_crypto_report in Allure for details."
            )
            assert errors == 0, (
                f"GTest reported {errors} errors out of {total} tests."
            )

    @allure.story("Run Specific GTest Filter")
    @allure.severity(allure.severity_level.NORMAL)
    def test_aes_operations_only(self, config, console, evidence, log_collector):
        """
        Run only AES-related tests from the GTest suite.

        Uses --gtest_filter to select specific test cases.
        """
        tool = self._tool(config)

        if not os.path.exists(tool["command"]):
            pytest.skip(f"Binary not found: {tool['command']}")

        gtest_xml = "evidence/gtest_aes_results.xml"
        os.makedirs("evidence", exist_ok=True)

        evidence.step("Run GTest: AES operations filter")
        result = console.run_executable(
            exe_path=tool["command"],
            args=[
                "--gtest_filter=*AES*:*aes*",
                f"--gtest_output=xml:{gtest_xml}",
                "--gtest_color=no",
            ],
            timeout=tool.get("timeout", 120),
        )

        evidence.attach_text(result.output, "gtest_aes_stdout")

        if os.path.exists(gtest_xml):
            gtest_results = log_collector.collect_gtest_xml(gtest_xml, name="gtest_aes_report")
            if gtest_results:
                evidence.log(f"AES tests: {gtest_results['total']} total, "
                            f"{gtest_results['failures']} failures")

        log_collector.collect_from_config(tool)

        evidence.step("Validate AES test results")
        result.assert_success()

    @allure.story("Run Specific GTest Filter")
    @allure.severity(allure.severity_level.NORMAL)
    def test_rsa_operations_only(self, config, console, evidence, log_collector):
        """
        Run only RSA-related tests from the GTest suite.
        """
        tool = self._tool(config)

        if not os.path.exists(tool["command"]):
            pytest.skip(f"Binary not found: {tool['command']}")

        gtest_xml = "evidence/gtest_rsa_results.xml"
        os.makedirs("evidence", exist_ok=True)

        evidence.step("Run GTest: RSA operations filter")
        result = console.run_executable(
            exe_path=tool["command"],
            args=[
                "--gtest_filter=*RSA*:*rsa*",
                f"--gtest_output=xml:{gtest_xml}",
                "--gtest_color=no",
            ],
            timeout=tool.get("timeout", 120),
        )

        evidence.attach_text(result.output, "gtest_rsa_stdout")

        if os.path.exists(gtest_xml):
            log_collector.collect_gtest_xml(gtest_xml, name="gtest_rsa_report")

        log_collector.collect_from_config(tool)

        evidence.step("Validate RSA test results")
        result.assert_success()

    @allure.story("GTest List Tests")
    @allure.severity(allure.severity_level.TRIVIAL)
    def test_list_tests(self, config, console, evidence, log_collector):
        """
        List all available tests in the GTest binary.

        Useful for discovery: see what the GTest binary contains
        without actually running any tests.
        """
        tool = self._tool(config)

        if not os.path.exists(tool["command"]):
            pytest.skip(f"Binary not found: {tool['command']}")

        evidence.step("List all available GTest cases")
        result = console.run_executable(
            exe_path=tool["command"],
            args=["--gtest_list_tests"],
            timeout=30,
        )

        evidence.attach_text(result.output, "gtest_available_tests")

        evidence.step("Validate test listing")
        result.assert_success()
        evidence.log(f"Available test cases:\n{result.stdout}")
