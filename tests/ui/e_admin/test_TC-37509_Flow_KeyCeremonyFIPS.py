"""
[E2E][e-admin][Key Ceremony] Key ceremony FIPS mode — Flow-based version

Same test as test_TC-37509_KeyCeremonyFIPS.py but using the flow
orchestration layer.

Scenario:
    Given  eAdmin launched and connected to HSM
    When   user starts HSM Initialization
    And    accepts T&C, changes SUPER_USER password
    And    SUPER_USER authenticates and creates Admin
    And    Admin logs in and creates 3 Key Custodians + 1 Auditor
    And    each Key Custodian imports their CCMK component
    And    user selects FIPS mode and finalizes
    Then   Key Ceremony completed successfully

Run:
    pytest tests/ui/e_admin/test_TC-37509_Flow_KeyCeremonyFIPS.py -v -s
"""

import logging

import allure
import pytest

from sphere_e2e_test_framework.flows.base import FlowContext
from sphere_e2e_test_framework.flows.e_admin import key_ceremony_flow
from tests.test_data import KeyCeremonyData

logger = logging.getLogger(__name__)


@allure.epic("Sphere HSM Idemia - E2E Tests - E-Admin")
@allure.feature("Key Ceremony")
@allure.suite("eAdmin-Tier1 Journeys")
@allure.tag("e-admin", "windows", "ui", "key-ceremony", "fips", "flow")
@pytest.mark.e_admin
@pytest.mark.flow
@pytest.mark.tcms(case_id=37509)
class TestKeyCeremonyFIPSFlow:

    @pytest.fixture(autouse=True)
    def setup(self, e_admin_driver, evidence):
        self.driver = e_admin_driver
        self.evidence = evidence
        self.td = KeyCeremonyData.from_env()
        yield

    @allure.story("User performs full key ceremony (FIPS) using password via E-Admin")
    @allure.title("[E2E][e-admin][Key Ceremony] Key ceremony FIPS mode (Flow)")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.testcase("https://10.88.1.13/case/37509/")
    @pytest.mark.critical
    @pytest.mark.order(1)
    def test_fips_key_ceremony_password(self):
        """Full key ceremony: connect, init HSM, create users, import CCMK, finalize FIPS."""
        ctx = FlowContext(self.driver, self.evidence, self.td)
        ctx.set("fips_mode", True)
        key_ceremony_flow.run(ctx)
