"""
[E2E][e-admin] Delete Operation User — Create user, delete user, verify deleted user fails login

Background:
    Given the eAdmin application is launched and visible
    And the key ceremony has already been completed
    And ADMIN is logged into the eAdmin application

Scenario 1: ADMIN creates a new user (prerequisite)
Scenario 2: ADMIN deletes the user
Scenario 3: Deleted user fails to login

Run:
    pytest tests/ui/e_admin/test_TC-37520_DeleteOperationUser.py -v -s
"""

import logging

import allure
import pytest

from hsm_test_framework.pages import DashboardPage, LoginPage
from tests.test_data import DeleteOperationUserData

logger = logging.getLogger(__name__)


@allure.epic("Sphere HSM Idemia - E2E Tests - E-Admin")
@allure.feature("User Management")
@allure.suite("eAdmin-Tier1 Journeys")
@allure.tag("e-admin", "windows", "ui", "user-management", "delete-user")
@pytest.mark.e_admin
@pytest.mark.tcms(case_id=37520)
class TestDeleteOperationUser:

    @pytest.fixture(autouse=True)
    def setup(self, e_admin_driver, evidence):
        self.driver = e_admin_driver
        self.evidence = evidence
        self.td = DeleteOperationUserData.from_env()
        yield

    @allure.story("ADMIN creates user, deletes user, deleted user fails to login")
    @allure.title("[E2E][e-admin] Delete Operation User")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.critical
    @pytest.mark.order(2)
    @pytest.mark.depends_on(37509)
    def test_delete_operation_user(self):
        """Full flow: login admin → create user → delete user → verify login fails."""
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

        # Label updates asynchronously after login — poll until it shows username
        import time as _time
        logged_in_user = ""
        for _ in range(15):
            logged_in_user = dashboard.get_logged_in_user()
            if td.admin_username in logged_in_user.lower():
                break
            _time.sleep(2)

        assert td.admin_username in logged_in_user.lower(), (
            f"Expected '{td.admin_username}' in label, got '{logged_in_user}'"
        )
        logger.info(f"Background complete — logged in as '{logged_in_user}'")

        # ==================================================================
        # Scenario 1: Create user (prerequisite for deletion)
        # ==================================================================
        user_page = dashboard.goto_user(
            step_name="When: ADMIN navigates to User Management",
        )
        user_page.refresh(
            step_name="And: Refresh user list",
        )

        if user_page.user_exists_in_table(td.user_username):
            logger.info(
                f"User '{td.user_username}' already exists — skipping creation"
            )
        else:
            # Create profile first
            profile_page = dashboard.goto_profile(
                step_name="When: ADMIN navigates to Profile Management",
            )
            profile_page.create_profile(
                profile_name=td.profile_name,
                select_all_acl=td.select_all_acl,
                step_name=f"When: ADMIN creates profile '{td.profile_name}'",
            )

            # Create user
            user_page = dashboard.goto_user(
                step_name="When: ADMIN navigates to User Management",
            )
            create_msg = user_page.create_user(
                username=td.user_username,
                password=td.user_password,
                profile_name=td.profile_name,
                step_name=(
                    f"When: ADMIN creates user '{td.user_username}' "
                    f"with profile '{td.profile_name}'"
                ),
            )
            logger.info(f"Then: User creation message: '{create_msg}'")

            # Refresh and sync
            user_page.refresh(
                step_name="And: Refresh user list after creation",
            )
            sync_msg = user_page.sync(
                step_name="And: ADMIN syncs users to HSM",
            )
            logger.info(f"Sync message: '{sync_msg}'")

        # Verify user exists before proceeding to delete
        assert user_page.user_exists_in_table(td.user_username), (
            f"User '{td.user_username}' not found in table — cannot proceed"
        )
        logger.info(
            f"Scenario 1 PASSED — user '{td.user_username}' ready for deletion"
        )

        # ==================================================================
        # Scenario 2: Delete user
        # ==================================================================
        user_page = dashboard.goto_user(
            step_name="When: ADMIN navigates to User Management",
        )
        user_page.refresh(
            step_name="And: Refresh user list before deletion",
        )

        delete_msg = user_page.delete_user(
            username=td.user_username,
            step_name=f"When: ADMIN deletes user '{td.user_username}'",
        )
        logger.info(f"Then: Delete confirmation message: '{delete_msg}'")

        # Refresh and verify user is gone
        user_page.refresh(
            step_name="And: Refresh user list after deletion",
        )
        assert not user_page.user_exists_in_table(td.user_username), (
            f"User '{td.user_username}' still found in table after deletion"
        )

        # Sync deletion to HSM
        sync_msg = user_page.sync(
            step_name="And: ADMIN syncs deletion to HSM",
        )
        logger.info(f"Sync message: '{sync_msg}'")
        logger.info(
            f"Scenario 2 PASSED — user '{td.user_username}' deleted successfully"
        )

        # ==================================================================
        # Scenario 3: Deleted user fails to login
        # ==================================================================
        dashboard = DashboardPage(driver, evidence)
        login_page = dashboard.logout(
            step_name="When: ADMIN logs out",
        )

        login_page.open_login_form(
            step_name="And: Open login form for deleted user",
        )

        sessions = login_page.get_sessions()
        user_session = next(
            (s for s in sessions if td.user_session in s), sessions[0],
        )
        login_page.select_session(
            user_session,
            step_name=f"And: Select session '{user_session}'",
        )

        error_msg = login_page.login_expect_failure(
            td.user_username, td.user_password,
            step_name=f"And: Attempt login as deleted user '{td.user_username}'",
        )
        assert error_msg, (
            "Expected error message for deleted user login, got empty string"
        )
        logger.info(f"Then: Login error message: '{error_msg}'")

        # Verify login form is still visible (login button present = not logged in)
        assert driver.element_exists(
            auto_id="btnLogin", control_type="Button",
        ), "Login form should still be visible after deleted user login attempt"
        logger.info(
            f"Scenario 3 PASSED — deleted user '{td.user_username}' "
            f"correctly rejected with: '{error_msg}'"
        )
