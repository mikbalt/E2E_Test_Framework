"""
[E2E][e-admin] Block User

Block a user by exhausting login attempts with wrong password,
then verify the account is locked (correct password also rejected).

    Background:
        Given the eAdmin application is launched and visible
          And the key ceremony has already been completed
          And ADMIN is logged into the eAdmin application

    Scenario: ADMIN ensures the target user account exists

        Given the user "<username>" may or may not exist in the system
        When ADMIN navigates to User Management from the sidebar
          And ADMIN clicks the Refresh button
        Then ADMIN checks if the user "<username>" exists in the user list table

        When the user "<username>" does not exist
          And ADMIN navigates to Profile Management from the sidebar
          And ADMIN creates the profile "<profile_name>" with all ACL permissions
          And ADMIN navigates to User Management from the sidebar
          And ADMIN creates the user "<username>" with profile "<profile_name>"
          And ADMIN clicks the Refresh button
          And ADMIN clicks the Sync button to synchronize users to the HSM
        Then the user "<username>" appears in the user list table

    Scenario: User attempts login with wrong password multiple times

        Given ADMIN logs out from the eAdmin application
          And the eAdmin login page is displayed
        When the user "<username>" opens the login form
          And the user "<username>" selects the session "<session>"
          And the user "<username>" enters the wrong password "<wrong_password>"
          And the user clicks the Login button
        Then an error message is displayed indicating invalid credentials

        When the user "<username>" repeats the wrong password login
        Then the login attempt fails each time (repeated up to <max_attempts> attempts)

    Scenario: User account is blocked after exceeding maximum failed login attempts

        Given the user "<username>" has exhausted all <max_attempts> login attempts
              with the wrong password "<wrong_password>"
        When the user "<username>" enters the correct password "<password>"
          And the user clicks the Login button
        Then an error message is displayed indicating the account is blocked
          And the login page remains displayed

Run:
    pytest tests/ui/e_admin/test_TC-37522_BlockUser.py -v -s
"""

import logging

import allure
import pytest

from sphere_e2e_test_framework.flows.base import FlowContext
from sphere_e2e_test_framework.flows.e_admin import block_user_flow
from tests.test_data import BlockUserData

logger = logging.getLogger(__name__)


@allure.epic("Sphere HSM Idemia - E2E Tests - E-Admin")
@allure.feature("User Management")
@allure.suite("eAdmin-Tier1 Journeys")
@allure.tag("e-admin", "windows", "ui", "user-management", "block-user", "flow")
@pytest.mark.e_admin
@pytest.mark.flow
@pytest.mark.tcms(case_id=37522)
class TestBlockUserFlow:

    @pytest.fixture(autouse=True)
    def setup(self, e_admin_driver, evidence):
        self.driver = e_admin_driver
        self.evidence = evidence
        self.td = BlockUserData.from_env()
        yield

    @allure.story("ADMIN ensures user exists, wrong password 5x blocks user, correct password rejected")
    @allure.title("[E2E][e-admin] Block User (Flow)")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.critical
    @pytest.mark.order(4)
    @pytest.mark.depends_on(37509)
    def test_block_user(self):
        """Block user: ensure user exists, exhaust wrong-password attempts, verify account locked."""
        ctx = FlowContext(self.driver, self.evidence, self.td)
        block_user_flow.run(ctx)
