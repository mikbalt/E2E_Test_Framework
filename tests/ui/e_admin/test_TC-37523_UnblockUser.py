"""
[E2E][e-admin] Unblock User — Flow-based version

Unblock a previously blocked user via User Management,
then verify the unblocked user can successfully log in.

Standalone-capable: dynamically reads user status from the table to decide:
  - BLOCKED  → skip straight to unblock
  - ACTIVE   → block first (logout, wrong pw x5, re-login), then unblock
  - Not found → create profile + user + sync, block, then unblock

Can run independently or after the Block User test (TC-37522).

    Background:
        Given the eAdmin application is launched and visible
          And the key ceremony has already been completed
          And ADMIN is logged into the eAdmin application

    Scenario: ADMIN ensures the target user is in BLOCKED state (dynamic)

        When ADMIN navigates to User Management from the sidebar
          And ADMIN clicks the Refresh button
        Then ADMIN reads the status of user "<username>" from the user list table

        When the user "<username>" status is "Blocked"
        Then no further prerequisite action is needed

        When the user "<username>" status is "Active"
        Then ADMIN logs out from the eAdmin application
          And the user "<username>" exhausts <max_attempts> login attempts
              with the wrong password "<wrong_password>"
          And the user "<username>" enters the correct password (expect blocked)
          And ADMIN re-logs in to the eAdmin application

        When the user "<username>" does not exist in the user list table
        Then ADMIN creates the profile "<profile_name>" with all ACL permissions
          And ADMIN creates the user "<username>" with profile "<profile_name>"
          And ADMIN syncs users to the HSM
          And ADMIN logs out and blocks the user via failed login attempts
          And ADMIN re-logs in to the eAdmin application

    Scenario: ADMIN unblocks the user via User Management

        Given ADMIN is logged into the eAdmin application
        When ADMIN navigates to User Management from the sidebar
          And ADMIN clicks the Refresh button
          And ADMIN selects the blocked user "<username>" from the user list table
          And ADMIN clicks the Unblock button
        Then a confirmation dialog is displayed

        When ADMIN clicks the Yes button on the confirmation dialog
        Then a confirmation message is displayed indicating the user has been unblocked

    Scenario: Unblocked user successfully logs in

        Given ADMIN logs out from the eAdmin application
          And the eAdmin login page is displayed
        When the unblocked user "<username>" opens the login form
          And the unblocked user selects the session "<session>"
          And the unblocked user enters valid credentials
          And the unblocked user clicks the Login button
        Then the eAdmin dashboard is accessible
          And the logged-in user label displays "<username>"

Run:
    pytest tests/ui/e_admin/test_TC-37523_UnblockUser.py -v -s
"""

import logging

import allure
import pytest

from sphere_e2e_test_framework.flows.base import FlowContext
from sphere_e2e_test_framework.flows.e_admin import unblock_user_flow
from tests.test_data import UnblockUserData

logger = logging.getLogger(__name__)


@allure.epic("Sphere HSM Idemia - E2E Tests - E-Admin")
@allure.feature("User Management")
@allure.suite("eAdmin-Tier1 Journeys")
@allure.tag("e-admin", "windows", "ui", "user-management", "unblock-user", "flow")
@pytest.mark.e_admin
@pytest.mark.flow
@pytest.mark.tcms(case_id=37523)
class TestUnblockUserFlow:

    @pytest.fixture(autouse=True)
    def setup(self, e_admin_driver, evidence):
        self.driver = e_admin_driver
        self.evidence = evidence
        self.td = UnblockUserData.from_env()
        yield

    @allure.story("ADMIN ensures user blocked, unblocks via User Management, unblocked user logs in")
    @allure.title("[E2E][e-admin] Unblock User (Flow)")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.critical
    @pytest.mark.order(5)
    @pytest.mark.depends_on(37522)
    def test_unblock_user(self):
        """Unblock user: ensure blocked, unblock via User Management, verify login succeeds."""
        ctx = FlowContext(self.driver, self.evidence, self.td)
        unblock_user_flow.run(ctx)
