"""
[E2E][PKCS11][Deprovisioning] HSM deprovisioning good case via PKCS11 C++ gtest

Scenario:
    Given PKCS11 C++ test binary is available on Windows
    When user runs the deprovisioning gtest filter
    Then command exits with code 0

Run:
    python -m pytest tests/console/pkcs11/test_hsm_deprovisioning.py -v
"""

import logging
import os
import platform

import allure
import pytest

from sphere_e2e_test_framework import ConsoleRunner

logger = logging.getLogger(__name__)

PKCS11_EXE = (
    r"C:\Users\admin\Documents\HSM_Test\Test_PKCS#11\Test_v0050\GTest_Internal"
    r"\x64\Release\PKCS11.exe"
)
PKCS11_WORKING_DIR = (
    r"C:\Users\admin\Documents\HSM_Test\Test_PKCS#11\Test_v0050\GTest_Internal"
    r"\x64\Release"
)
PKCS11_DLL = "libIdemiaPKCS11.dll"
PKCS11_GTEST_FILTER = "hsmDeprovisioning.testGoodCase_01"
PKCS11_TIMEOUT = 420
PKCS11_LOG_FILE = r"C:\logpkcs11\pkcs11_logfile.log"


@allure.epic("Sphere HSM Idemia - E2E Tests - Console")
@allure.feature("PKCS#11")
@allure.suite("PKCS11-C++ Journeys")
@pytest.mark.console
@pytest.mark.pkcs11
# @pytest.mark.cpp
@pytest.mark.tcms(case_id=37519)
@pytest.mark.order(3)
class TestHSMDeprovisioning:
    """Run PKCS11.exe deprovisioning test from pytest."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.runner = ConsoleRunner()

    @allure.story("Execute PKCS11 C++ gtest for deprovisioning")
    @allure.title("[E2E][PKCS11][Deprovisioning] HSM deprovisioning via C++ gtest")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.description(
        """
        Notes:
        Description: This test case is to verify the HSM Deprovisioning and Key Material Cleanup process in PKCS#11 Tier-1 Journey.

        Pre-requisites:
        1. HSM Rooky Board/Simulator and Proxy are in place and configured correctly.
        2. PKCS#11 library and PKCS#11 test runner are installed on client side.
        3. Provisioned environment exists (Admin, Auditor, and key ceremony data already present).
        4. SUPER_USER, Admin, and Auditor credentials for deprovisioning are available.

        Notes: This journey is executed through PKCS#11 deprovisioning API (single deprovisioning transaction)

        Scenario: Perform HSM deprovisioning via PKCS#11 and remove provisioned users and CCMK

        Given PKCS#11 library is loaded successfully
        And PKCS#11 function list is available
        And PKCS#11 environment is initialized
        And target cluster is identified from the available domain/cluster list
        When user starts HSM deprovisioning
        And user provides SUPER_USER, Admin, and Auditor credentials
        And user executes deprovisioning on target cluster
        Then HSM deprovisioning is completed successfully
        And provisioned user accounts and CCMK-related data are removed successfully
        And PKCS#11 environment is finalized successfully
        """
    )
    @allure.tag("pkcs11", "windows", "console", "cpp", "deprovisioning")
    def test_hsm_deprovisioning_good_case(self, evidence, log_collector):
        if platform.system() != "Windows":
            pytest.skip("PKCS11 C++ executable path is Windows-only")

        if not os.path.exists(PKCS11_EXE):
            pytest.fail(f"PKCS11 executable not found: {PKCS11_EXE}")

        args = [PKCS11_DLL, f"--gtest_filter={PKCS11_GTEST_FILTER}"]

        result = self.runner.run(
            PKCS11_EXE,
            args,
            working_dir=PKCS11_WORKING_DIR,
            timeout=PKCS11_TIMEOUT,
            stream_output=True,
        )

        logger.info("Command: %s", result.command)
        logger.info("Exit code: %s", result.returncode)
        logger.info("Duration: %.2fs", result.duration)

        evidence.attach_text(
            f"Command: {result.command}\n"
            f"Return Code: {result.returncode}\n"
            f"Duration: {result.duration:.2f}s\n\n"
            f"--- STDOUT ---\n{result.stdout}\n\n"
            f"--- STDERR ---\n{result.stderr}",
            name="hsm_deprovisioning_output",
        )
        log_collector.collect(PKCS11_LOG_FILE, name="pkcs11_logfile")

        result.assert_success(
            "PKCS11.exe gtest filter should succeed for hsmDeprovisioning.testGoodCase_01"
        )
