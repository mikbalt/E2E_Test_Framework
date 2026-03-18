"""
[E2E][e-admin] Delete Operation User — Flow-based version

Same test as test_TC-37520_DeleteOperationUser.py but using the
flow orchestration layer. Kept alongside the original for validation.

Background:
    Given the eAdmin application is launched and visible
    And the key ceremony has already been completed
    And ADMIN is logged into the eAdmin application

Scenario 1: ADMIN creates a new user (prerequisite)
Scenario 2: ADMIN deletes the user
Scenario 3: Deleted user fails to login

Run:
    pytest tests/ui/e_admin/test_TC-37520_flow.py -v -s
"""

import logging

import allure
import pytest

from sphere_e2e_test_framework.flows.base import FlowContext
from sphere_e2e_test_framework.flows.e_admin import delete_user_flow
from tests.test_data import DeleteOperationUserData

logger = logging.getLogger(__name__)


@allure.epic("Sphere HSM Idemia - E2E Tests - E-Admin")
@allure.feature("User Management")
@allure.suite("eAdmin-Tier1 Journeys")
@allure.tag("e-admin", "windows", "ui", "user-management", "delete-user", "flow")
@pytest.mark.e_admin
@pytest.mark.flow
@pytest.mark.tcms(case_id=37520)
class TestDeleteOperationUserFlow:

    @pytest.fixture(autouse=True)
    def setup(self, e_admin_driver, evidence):
        self.driver = e_admin_driver
        self.evidence = evidence
        self.td = DeleteOperationUserData.from_env()
        yield

    @allure.story("ADMIN creates user, deletes user, deleted user fails to login")
    @allure.title("[E2E][e-admin] Delete Operation User (Flow)")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.critical
    @pytest.mark.order(3)
    @pytest.mark.depends_on(37509)
    def test_delete_operation_user(self):
        """Full flow: login admin -> create user -> delete user -> verify login fails."""
        ctx = FlowContext(self.driver, self.evidence, self.td)
        delete_user_flow.run(ctx)
