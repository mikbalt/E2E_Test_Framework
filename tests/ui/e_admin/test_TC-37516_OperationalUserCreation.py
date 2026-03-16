"""
[E2E][e-admin] Add Operation User — Create profile, create user, verify login

Background:
    Given the eAdmin application is launched and visible
    And the key ceremony has already been completed
    And ADMIN is logged into the eAdmin application

Scenario 1: ADMIN creates a new user profile
Scenario 2: ADMIN creates a new user with the profile
Scenario 3: Newly created user logs in successfully

Run:
    pytest tests/ui/e_admin/test_add_operation_user.py -v -s
"""

import logging

import allure
import pytest

from hsm_test_framework.pages import DashboardPage, LoginPage
from tests.test_data import AddOperationUserData

logger = logging.getLogger(__name__)


@allure.epic("Sphere HSM Idemia - E2E Tests - E-Admin")
@allure.feature("User Management")
@allure.suite("eAdmin-Tier1 Journeys")
@allure.tag("e-admin", "windows", "ui", "user-management")
@pytest.mark.e_admin
@pytest.mark.tcms(case_id=37516)
class TestAddOperationUser:

    @pytest.fixture(autouse=True)
    def setup(self, e_admin_driver, evidence):
        self.driver = e_admin_driver
        self.evidence = evidence
        self.td = AddOperationUserData.from_env()
        yield

    @allure.story("ADMIN creates profile, creates user, user logs in")
    @allure.title("[E2E][e-admin] Add Operation User")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.critical
    @pytest.mark.order(2)
    @pytest.mark.depends_on(37509)
    def test_add_operation_user(self):
        """Full flow: login admin → create user → verify login."""
        driver = self.driver
        evidence = self.evidence
        td = self.td

        # ==================================================================
        # Background: Connect and login as ADMIN
        # ==================================================================
        login = LoginPage(driver, evidence)

        dashboard = login.connect_to_hsm(
            step_name="Given: eAdmin is connected to HSM",
        )
        assert dashboard.is_visible(), "Dashboard not visible after connection"

        login_page = dashboard.open_login()
        login_page.open_login_form(
            step_name="And: Open login form",
        )

        sessions = login_page.get_sessions()
        admin_session = next(
            (s for s in sessions if td.admin_session in s), sessions[0],
        )
        login_page.select_session(
            admin_session,
            step_name=f"And: Select session '{admin_session}'",
        )
        dashboard = login_page.login(
            td.admin_username, td.admin_password,
            step_name="And: ADMIN logs in to eAdmin",
        )

        logged_in_user = dashboard.get_logged_in_user()
        assert td.admin_username in logged_in_user.lower(), (
            f"Expected '{td.admin_username}' in label, got '{logged_in_user}'"
        )
        logger.info(f"Background complete — logged in as '{logged_in_user}'")

        # ==================================================================
        # Scenario 1: Create Profile
        # ==================================================================
        profile_page = dashboard.goto_profile(
            step_name="When: ADMIN navigates to Profile Management",
        )

        profile_msg = profile_page.create_profile(
            profile_name=td.profile_name,
            select_all_acl=td.select_all_acl,
            step_name=(
                f"When: ADMIN creates profile '{td.profile_name}'"
            ),
        )
        logger.info(f"Then: Profile creation message: '{profile_msg}'")

        # ==================================================================
        # Scenario 2: Create User
        # ==================================================================
        user_page = dashboard.goto_user(
            step_name="When: ADMIN navigates to User Management",
        )

        # Create new user
        create_msg = user_page.create_user(
            username=td.user_username,
            password=td.user_password,
            profile_name=td.profile_name,
            step_name=(
                f"When: ADMIN creates user '{td.user_username}' "
                f"with profile '{td.profile_name}'"
            ),
        )

        # Assert: confirmation message
        logger.info(f"Then: Confirmation message: '{create_msg}'")

        # Refresh and verify user appears in table
        user_page.refresh(
            step_name="And: Refresh user list",
        )

        # Sync to HSM
        sync_msg = user_page.sync(
            step_name="Then: ADMIN syncs users to HSM",
        )
        logger.info(f"Sync message: '{sync_msg}'")

        # ==================================================================
        # Scenario 3: Logout ADMIN → Login as new user
        # ==================================================================
        dashboard = DashboardPage(driver, evidence)
        login_page = dashboard.logout(
            step_name="When: ADMIN logs out",
        )

        login_page.open_login_form(
            step_name="And: Open login form for new user",
        )

        sessions = login_page.get_sessions()
        user_session = next(
            (s for s in sessions if td.user_session in s), sessions[0],
        )
        login_page.select_session(
            user_session,
            step_name=f"And: Select session '{user_session}'",
        )
        dashboard = login_page.login(
            td.user_username, td.user_password,
            step_name=f"And: '{td.user_username}' logs in",
        )

        # User_Session takes longer to load — poll label for up to 30s
        import time as _time
        logged_in_user = ""
        for _ in range(15):
            logged_in_user = dashboard.get_logged_in_user()
            if td.user_username in logged_in_user.lower():
                break
            _time.sleep(2)

        assert td.user_username in logged_in_user.lower(), (
            f"Expected '{td.user_username}' in label, got '{logged_in_user}'"
        )
        logger.info(
            f"Scenario 3 PASSED — '{td.user_username}' logged in successfully"
        )
