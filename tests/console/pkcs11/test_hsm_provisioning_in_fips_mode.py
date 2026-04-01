"""
[E2E][PKCS11][FIPS] HSM provisioning good case via PKCS11 C++ gtest

Scenario:
    Given PKCS11 C++ test binary is available on Windows
    When user runs the FIPS provisioning gtest filter
    Then command exits with code 0

Run:
    python -m pytest tests/console/pkcs11/test_hsm_provisioning_in_fips_mode.py -v
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
PKCS11_GTEST_FILTER = "hsmProvisioning.testGoodCase_fips"
PKCS11_TIMEOUT = 420
PKCS11_LOG_FILE = r"C:\logpkcs11\pkcs11_logfile.log"


@allure.epic("Sphere HSM Idemia - E2E Tests - Console")
@allure.feature("PKCS#11")
@allure.suite("PKCS11-C++ Journeys")
@pytest.mark.console
@pytest.mark.pkcs11
# @pytest.mark.cpp
@pytest.mark.tcms(case_id=37512)
@pytest.mark.order(1)
class TestHSMProvisioningInFIPSMode:
    """Run PKCS11.exe FIPS provisioning test from pytest."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.runner = ConsoleRunner()

    @allure.story("Execute PKCS11 C++ gtest for FIPS provisioning")
    @allure.title("[E2E][PKCS11][FIPS] HSM provisioning via C++ gtest")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.description(
        """
        Notes:
        Description: This test case is to verify the FIPS-enabled HSM Provisioning and Key Ceremony process in PKCS#11 Tier-1 Journey.

        Pre-requisites:
        1. HSM Rooky Board/Simulator and Proxy are in place and configured correctly.
        2. PKCS#11 library and PKCS#11 test runner are installed on client side.
        3. Default SUPER_USER password and provisioning input data are available.
        4. CCMK import data set (3 parts, KCV, final KCV check) is prepared.

        Notes: This journey is executed through PKCS#11 provisioning API (single provisioning transaction)

        Scenario: Perform FIPS HSM provisioning via PKCS#11 with CCMK import

        Given PKCS#11 library is loaded successfully
        And PKCS#11 function list is available
        And PKCS#11 environment is initialized
        When user starts HSM provisioning in FIPS mode
        And user provides SUPER_USER password rotation data
        And user provides Admin, Auditor, Key Custodian 1, Key Custodian 2, Key Custodian 3, and PKCS#11 User data
        And user provides CCMK import secrets, per-part KCVs, and final CCMK KCV check
        And user executes provisioning on target cluster
        Then HSM provisioning is completed successfully
        And key ceremony data is accepted successfully
        And required user accounts are created successfully
        And PKCS#11 environment is finalized successfully
        And user successfully login with test_c_login_logout
        """
    )
    @allure.tag("pkcs11", "windows", "console", "cpp", "fips")
    def test_hsm_provisioning_in_fips_mode(self, evidence, log_collector):
        if platform.system() != "Windows":
            pytest.skip("PKCS11 C++ executable path is Windows-only")

        if not os.path.exists(PKCS11_EXE):
            pytest.fail(f"PKCS11 executable not found: {PKCS11_EXE}")

        args = [PKCS11_DLL, f"--gtest_filter={PKCS11_GTEST_FILTER}"]

        # Future extension point (e.g., Kiwi run args) without changing core behavior now.
        extra_args = []
        if extra_args:
            args.extend(extra_args)

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
            name="hsm_provisioning_fips_output",
        )
        log_collector.collect(PKCS11_LOG_FILE, name="pkcs11_logfile")

        result.assert_success(
            "PKCS11.exe gtest filter should succeed for hsmProvisioning.testGoodCase_fips"
        )
