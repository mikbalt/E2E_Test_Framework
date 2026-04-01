"""
[E2E][e-admin] HSM Reset by Super User — Flow-based version

Same test as test_TC-37517_HSMResetBySuperUser.py but using the flow
orchestration layer.

Background:
    Given the eAdmin application is launched and visible
    And the key ceremony has already been completed

Scenario: SUPER_USER initiates HSM Reset, ADMIN authorizes
    Phase 1 — Export Audit Log
    Phase 2 — Perform HSM Reset

Run:
    pytest tests/ui/e_admin/test_TC-37517_Flow_HSMResetBySuperUser.py -v -s
"""

import logging

import allure
import pytest

from sphere_e2e_test_framework.flows.base import FlowContext
from sphere_e2e_test_framework.flows.e_admin import hsm_reset_flow
from tests.test_data import HSMResetData

logger = logging.getLogger(__name__)


@allure.epic("Sphere HSM Idemia - E2E Tests - E-Admin")
@allure.feature("HSM Reset")
@allure.suite("eAdmin-Tier1 Journeys")
@allure.tag("e-admin", "windows", "ui", "hsm-reset", "flow")
@pytest.mark.e_admin
@pytest.mark.flow
@pytest.mark.tcms(case_id=37517)
class TestHSMResetBySuperUserFlow:

    @pytest.fixture(autouse=True)
    def setup(self, e_admin_driver, evidence):
        self.driver = e_admin_driver
        self.evidence = evidence
        self.td = HSMResetData.from_env()
        yield

    @allure.story("SUPER_USER initiates HSM reset, ADMIN authorizes")
    @allure.title("[E2E][e-admin] HSM Reset by Super User (Flow)")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.critical
    @pytest.mark.order(3)
    @pytest.mark.depends_on(37509)
    def test_hsm_reset_by_super_user(self):
        """Full flow: login → export audit log → re-login → reset → verify."""
        ctx = FlowContext(self.driver, self.evidence, self.td)
        hsm_reset_flow.run(ctx)
