"""
[E2E][e-admin] Add Operation User — Flow-based version

Same test as test_TC-37516_OperationalUserCreation.py but using the
flow orchestration layer.

Background:
    Given the eAdmin application is launched and visible
    And the key ceremony has already been completed
    And ADMIN is logged into the eAdmin application

Scenario 1: ADMIN creates a new user profile
Scenario 2: ADMIN creates a new user with the profile
Scenario 3: Newly created user logs in successfully

Run:
    pytest tests/ui/e_admin/test_TC-37516_Flow_AddOperationUser.py -v -s
"""

import logging

import allure
import pytest

from sphere_e2e_test_framework.flows.base import FlowContext
from sphere_e2e_test_framework.flows.e_admin import add_user_flow
from tests.test_data import AddOperationUserData

logger = logging.getLogger(__name__)


@allure.epic("Sphere HSM Idemia - E2E Tests - E-Admin")
@allure.feature("User Management")
@allure.suite("eAdmin-Tier1 Journeys")
@allure.tag("e-admin", "windows", "ui", "user-management", "add-user", "flow")
@pytest.mark.e_admin
@pytest.mark.flow
@pytest.mark.tcms(case_id=37516)
class TestAddOperationUserFlow:

    @pytest.fixture(autouse=True)
    def setup(self, e_admin_driver, evidence):
        self.driver = e_admin_driver
        self.evidence = evidence
        self.td = AddOperationUserData.from_env()
        yield

    @allure.story("ADMIN creates profile, creates user, user logs in")
    @allure.title("[E2E][e-admin] Add Operation User (Flow)")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.critical
    @pytest.mark.order(2)
    @pytest.mark.depends_on(37509)
    def test_add_operation_user(self):
        """Full flow: login admin → create profile → create user → sync → verify login."""
        ctx = FlowContext(self.driver, self.evidence, self.td)
        add_user_flow.run(ctx)
