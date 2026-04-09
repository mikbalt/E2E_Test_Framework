"""
[E2E][e-admin][Key Ceremony] Key ceremony Non-FIPS mode — Flow-based version

Works in both scenarios:
- After HSM Reset (full flow): password change auto-skipped
- Standalone (fresh HSM): password change auto-detected and handled

Scenario:
    Given  eAdmin launched and connected to HSM
    When   user starts HSM Initialization
    And    T&C pages and password change handled (auto-detect)
    And    SUPER_USER authenticates and creates Admin
    And    Admin logs in and creates 3 Key Custodians + 1 Auditor
    And    each Key Custodian imports their CCMK component
    And    user selects Non-FIPS mode and finalizes
    Then   Key Ceremony completed successfully

Run:
    pytest tests/ui/e_admin/test_TC-37515_KeyCeremonyNonFIPS.py -v -s
"""

import logging

import allure
import pytest

from sphere_e2e_test_framework.flows.base import FlowContext
from sphere_e2e_test_framework.flows.e_admin import key_ceremony_nonfips_flow
from tests.test_data import KeyCeremonyData

logger = logging.getLogger(__name__)


@allure.epic("Sphere HSM Idemia - E2E Tests - E-Admin")
@allure.feature("Key Ceremony")
@allure.suite("eAdmin-Tier1 Journeys")
@allure.tag("e-admin", "windows", "ui", "key-ceremony", "non-fips", "flow")
@pytest.mark.e_admin
@pytest.mark.flow
@pytest.mark.tcms(case_id=37515)
class TestKeyCeremonyNonFIPSFlow:

    @pytest.fixture(autouse=True)
    def setup(self, e_admin_driver, evidence):
        self.driver = e_admin_driver
        self.evidence = evidence
        self.td = KeyCeremonyData.from_env()
        yield

    @allure.story("User performs full key ceremony (Non-FIPS) using password via E-Admin")
    @allure.title("[E2E][e-admin][Key Ceremony] Key ceremony Non-FIPS mode (Flow)")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.testcase("https://10.88.1.13/case/37515/")
    @pytest.mark.critical
    @pytest.mark.order(9)
    @pytest.mark.depends_on(37517)
    def test_non_fips_key_ceremony_password(self):
        """Key ceremony Non-FIPS: auto-detects password change need."""
        ctx = FlowContext(self.driver, self.evidence, self.td)
        ctx.set("fips_mode", False)
        key_ceremony_nonfips_flow.run(ctx)
