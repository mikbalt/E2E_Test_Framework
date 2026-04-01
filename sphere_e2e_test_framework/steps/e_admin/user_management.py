"""
E-Admin user & profile CRUD step factories.

Each function returns a Step that internally uses page objects.
Steps communicate via ``ctx.state`` / ``ctx.page``.
"""

import logging
import time

from sphere_e2e_test_framework.flows.base import Step

logger = logging.getLogger(__name__)


def ensure_user_blocked(
    username_attr="user_username",
    password_attr="user_password",
    profile_attr="profile_name",
    acl_attr="select_all_acl",
    session_attr="user_session",
    wrong_password_attr="wrong_password",
    max_attempts_attr="max_attempts",
    admin_session_attr="admin_session",
    admin_username_attr="admin_username",
    admin_password_attr="admin_password",
):
    """Ensure user exists and is blocked — dynamic prerequisite.

    Reads the user table to decide what to do:
    - **BLOCKED** → no-op, ctx.page stays on UserManagementPage
    - **ACTIVE** → logout, exhaust wrong-password attempts, re-login as ADMIN
    - **Not found** → create profile + user + sync, then block cycle

    Expects ``ctx.page`` is DashboardPage (after full_login).
    Sets ``ctx.page`` to DashboardPage (logged in as ADMIN).
    """

    def _action(ctx):
        from sphere_e2e_test_framework.pages.e_admin import DashboardPage

        dashboard = ctx.page
        username = getattr(ctx.td, username_attr)

        # Navigate to User Management and check status
        user_page = dashboard.goto_user(
            step_name="When: Navigate to User Management",
        )
        user_page.refresh(step_name="And: Refresh user list")

        needs_creation = False
        needs_blocking = False

        if user_page.user_exists_in_table(username):
            status = user_page.get_user_status(username)
            if status and "block" in status.lower():
                logger.info(
                    f"User '{username}' is already BLOCKED — "
                    f"skipping to unblock"
                )
                ctx.page = user_page
                return
            else:
                logger.info(
                    f"User '{username}' status='{status}' — will block"
                )
                needs_blocking = True
        else:
            logger.info(
                f"User '{username}' not found — will create and block"
            )
            needs_creation = True
            needs_blocking = True

        # --- Create user if needed ---
        if needs_creation:
            profile_name = getattr(ctx.td, profile_attr)
            select_all = getattr(ctx.td, acl_attr, True)

            profile_page = dashboard.goto_profile(
                step_name="When: Navigate to Profile Management",
            )
            profile_page.create_profile(
                profile_name=profile_name,
                select_all_acl=select_all,
                step_name=f"When: Create profile '{profile_name}'",
            )

            password = getattr(ctx.td, password_attr)
            user_page = dashboard.goto_user(
                step_name="When: Navigate to User Management",
            )
            user_page.create_user(
                username=username,
                password=password,
                profile_name=profile_name,
                step_name=(
                    f"When: Create user '{username}' "
                    f"with profile '{profile_name}'"
                ),
            )
            user_page.refresh(
                step_name="And: Refresh user list after creation",
            )
            user_page.sync(step_name="And: Sync users to HSM")

        # --- Block user ---
        if needs_blocking:
            # Logout
            dashboard_ref = DashboardPage(ctx.driver, ctx.evidence)
            login_page = dashboard_ref.logout(
                step_name="When: ADMIN logs out to block user",
            )

            # Open form, select user session, exhaust wrong-password attempts
            session_hint = getattr(ctx.td, session_attr)
            wrong_password = getattr(ctx.td, wrong_password_attr)
            correct_password = getattr(ctx.td, password_attr)
            max_attempts = getattr(ctx.td, max_attempts_attr)

            login_page.open_login_form(
                step_name="And: Open login form for block attempt",
            )
            sessions = login_page.get_sessions()
            session = next(
                (s for s in sessions if session_hint in s), sessions[0],
            )
            login_page.select_session(
                session,
                step_name=f"And: Select session '{session}'",
            )

            for attempt in range(1, max_attempts + 1):
                login_page.login_expect_failure(
                    username, wrong_password,
                    step_name=(
                        f"And: Attempt {attempt}/{max_attempts} — "
                        f"login as '{username}' with wrong password"
                    ),
                )

            # Verify blocked with correct password
            error_msg = login_page.login_expect_failure(
                username, correct_password,
                step_name=(
                    f"Then: Verify '{username}' is blocked "
                    f"(correct password rejected)"
                ),
            )
            assert error_msg, (
                "Expected error for blocked user login, got empty string"
            )
            logger.info(f"User '{username}' is now blocked: '{error_msg}'")

            # Re-login as ADMIN
            admin_session_hint = getattr(ctx.td, admin_session_attr)
            admin_username = getattr(ctx.td, admin_username_attr)
            admin_password = getattr(ctx.td, admin_password_attr)

            sessions = login_page.get_sessions()
            admin_session = next(
                (s for s in sessions if admin_session_hint in s),
                sessions[0],
            )
            login_page.select_session(
                admin_session,
                step_name=f"And: Select session '{admin_session}'",
            )
            dashboard = login_page.login(
                admin_username, admin_password,
                step_name="And: ADMIN re-logs in",
            )

            # Poll for admin login
            logged_in_user = ""
            for _ in range(15):
                logged_in_user = dashboard.get_logged_in_user()
                if admin_username.lower() in logged_in_user.lower():
                    break
                time.sleep(2)
            assert admin_username.lower() in logged_in_user.lower(), (
                f"Expected '{admin_username}' in label, "
                f"got '{logged_in_user}'"
            )
            logger.info("ADMIN re-logged in successfully")

        ctx.page = dashboard

    return Step("Ensure user is blocked (dynamic)", _action)


def navigate_to_user_management():
    """Navigate sidebar → User Management, refresh. Sets ctx.page to UserManagementPage."""

    def _action(ctx):
        dashboard = ctx.page
        user_page = dashboard.goto_user(
            step_name="When: Navigate to User Management",
        )
        user_page.refresh(
            step_name="And: Refresh user list",
        )
        ctx.page = user_page

    return Step("Navigate to User Management", _action)


def navigate_to_profile_management():
    """Navigate sidebar → Profile Management. Sets ctx.page to ProfileManagementPage."""

    def _action(ctx):
        dashboard = ctx.page
        profile_page = dashboard.goto_profile(
            step_name="When: Navigate to Profile Management",
        )
        ctx.page = profile_page

    return Step("Navigate to Profile Management", _action)


def verify_user_table_populated():
    """Verify user table is displayed and has at least one user entry.

    Expects ``ctx.page`` is UserManagementPage.
    """

    def _action(ctx):
        user_page = ctx.page
        data = user_page.get_user_table()
        row_count = len(data["rows"])
        assert row_count >= 1, (
            f"Expected at least 1 user in table, got {row_count}"
        )
        logger.info(f"User table populated: {row_count} entries")

    return Step("Verify user table is populated", _action)


def create_user_on_page(
    username_attr="user_username",
    password_attr="user_password",
    profile_attr="profile_name",
):
    """Create user while already on UserManagementPage.

    Unlike ``create_user()``, this does NOT navigate from dashboard.
    Expects ``ctx.page`` is UserManagementPage.
    Stores confirmation message in ``ctx.state['create_msg']``.
    """

    def _action(ctx):
        user_page = ctx.page
        username = getattr(ctx.td, username_attr)
        password = getattr(ctx.td, password_attr)
        profile_name = getattr(ctx.td, profile_attr)

        create_msg = user_page.create_user(
            username=username,
            password=password,
            profile_name=profile_name,
            step_name=(
                f"When: Create user '{username}' "
                f"with profile '{profile_name}'"
            ),
        )
        assert create_msg, "Expected confirmation message after user creation"
        logger.info(f"User creation message: '{create_msg}'")
        ctx.set("create_msg", create_msg)

    return Step("Create user on page", _action)


def verify_user_in_table(
    username_attr="user_username",
    profile_attr="profile_name",
):
    """Verify user exists in table and check profile assignment.

    Expects ``ctx.page`` is UserManagementPage.
    """

    def _action(ctx):
        user_page = ctx.page
        username = getattr(ctx.td, username_attr)
        profile_name = getattr(ctx.td, profile_attr)

        user_page.refresh(
            step_name=f"And: Refresh user list to verify '{username}'",
        )
        assert user_page.user_exists_in_table(username), (
            f"User '{username}' not found in table after creation"
        )

        headers, row = user_page.get_user_row(username)
        assert row is not None, f"User '{username}' row data not found"
        row_text = " ".join(row)
        assert profile_name in row_text, (
            f"Profile '{profile_name}' not found in user row: {row}"
        )
        logger.info(
            f"User '{username}' verified in table with profile '{profile_name}'"
        )

    return Step("Verify user in table with profile", _action)


def create_profile(profile_attr="profile_name", acl_attr="select_all_acl"):
    """Create profile via Profile Management. Navigates from dashboard.

    Expects ``ctx.page`` is DashboardPage.
    Sets ``ctx.page`` back to DashboardPage (navigates to profile, creates, done).
    """

    def _action(ctx):
        dashboard = ctx.page
        profile_name = getattr(ctx.td, profile_attr)
        select_all = getattr(ctx.td, acl_attr, True)

        profile_page = dashboard.goto_profile(
            step_name=f"When: Navigate to Profile Management",
        )
        profile_msg = profile_page.create_profile(
            profile_name=profile_name,
            select_all_acl=select_all,
            step_name=f"When: Create profile '{profile_name}'",
        )
        logger.info(f"Profile creation message: '{profile_msg}'")
        ctx.set("profile_msg", profile_msg)
        # page stays as dashboard (sidebar is still available)
        ctx.page = dashboard

    return Step("Create profile", _action)


def create_user(
    username_attr="user_username",
    password_attr="user_password",
    profile_attr="profile_name",
):
    """Create user via User Management. Navigates from dashboard.

    Expects ``ctx.page`` is DashboardPage.
    Sets ``ctx.page`` to UserManagementPage.
    """

    def _action(ctx):
        dashboard = ctx.page
        username = getattr(ctx.td, username_attr)
        password = getattr(ctx.td, password_attr)
        profile_name = getattr(ctx.td, profile_attr)

        user_page = dashboard.goto_user(
            step_name="When: Navigate to User Management",
        )
        create_msg = user_page.create_user(
            username=username,
            password=password,
            profile_name=profile_name,
            step_name=(
                f"When: Create user '{username}' "
                f"with profile '{profile_name}'"
            ),
        )
        logger.info(f"User creation message: '{create_msg}'")
        ctx.set("create_msg", create_msg)
        ctx.page = user_page

    return Step("Create user", _action)


def refresh_and_sync(retries=0, retry_delay=1.0):
    """Refresh user list and sync to HSM. Expects ctx.page is UserManagementPage."""

    def _action(ctx):
        user_page = ctx.page
        user_page.refresh(
            step_name="And: Refresh user list",
        )
        sync_msg = user_page.sync(
            step_name="And: Sync users to HSM",
        )
        logger.info(f"Sync message: '{sync_msg}'")
        ctx.set("sync_msg", sync_msg)

    return Step("Refresh and sync to HSM", _action,
                retries=retries, retry_delay=retry_delay)


def ensure_user_exists(
    username_attr="user_username",
    password_attr="user_password",
    profile_attr="profile_name",
    acl_attr="select_all_acl",
):
    """Ensure user exists — create (with profile) if not found.

    Navigates to User Management, checks table, conditionally creates
    profile + user + sync. Verifies user exists before returning.
    Expects ``ctx.page`` is DashboardPage.
    Sets ``ctx.page`` to UserManagementPage.
    """

    def _action(ctx):
        dashboard = ctx.page
        username = getattr(ctx.td, username_attr)

        user_page = dashboard.goto_user(
            step_name="When: Navigate to User Management",
        )
        user_page.refresh(
            step_name="And: Refresh user list",
        )

        if user_page.user_exists_in_table(username):
            logger.info(f"User '{username}' already exists — skipping creation")
        else:
            # Create profile first
            profile_name = getattr(ctx.td, profile_attr)
            select_all = getattr(ctx.td, acl_attr, True)

            profile_page = dashboard.goto_profile(
                step_name="When: Navigate to Profile Management",
            )
            profile_page.create_profile(
                profile_name=profile_name,
                select_all_acl=select_all,
                step_name=f"When: Create profile '{profile_name}'",
            )

            # Create user
            password = getattr(ctx.td, password_attr)
            user_page = dashboard.goto_user(
                step_name="When: Navigate to User Management",
            )
            create_msg = user_page.create_user(
                username=username,
                password=password,
                profile_name=profile_name,
                step_name=(
                    f"When: Create user '{username}' "
                    f"with profile '{profile_name}'"
                ),
            )
            logger.info(f"User creation message: '{create_msg}'")

            # Refresh and sync
            user_page.refresh(
                step_name="And: Refresh user list after creation",
            )
            sync_msg = user_page.sync(
                step_name="And: Sync users to HSM",
            )
            logger.info(f"Sync message: '{sync_msg}'")

        # Verify user exists before proceeding
        assert user_page.user_exists_in_table(username), (
            f"User '{username}' not found in table — cannot proceed"
        )
        logger.info(f"User '{username}' ready")
        ctx.page = user_page

    return Step("Ensure user exists (create if needed)", _action)


def unblock_user(username_attr="user_username"):
    """Unblock a blocked user, confirm, sync.

    Expects ``ctx.page`` is DashboardPage or UserManagementPage.
    If already on UserManagementPage, skips navigation.
    Sets ``ctx.page`` to UserManagementPage.
    """

    def _action(ctx):
        from sphere_e2e_test_framework.pages.e_admin.user_management_page import (
            UserManagementPage,
        )
        from sphere_e2e_test_framework.pages.e_admin import DashboardPage

        username = getattr(ctx.td, username_attr)

        page = ctx.page
        if isinstance(page, UserManagementPage):
            user_page = page
        elif hasattr(page, "goto_user"):
            user_page = page.goto_user(
                step_name="When: Navigate to User Management",
            )
        else:
            dashboard = DashboardPage(ctx.driver, ctx.evidence)
            user_page = dashboard.goto_user(
                step_name="When: Navigate to User Management",
            )

        user_page.refresh(
            step_name="And: Refresh user list",
        )

        unblock_msg = user_page.unblock_user(
            username=username,
            step_name=f"When: Unblock user '{username}'",
        )
        logger.info(f"Unblock confirmation: '{unblock_msg}'")
        ctx.set("unblock_msg", unblock_msg)
        ctx.page = user_page

    return Step("Unblock user", _action)


def delete_user(username_attr="user_username"):
    """Delete user, verify removed, sync.

    Expects ``ctx.page`` is DashboardPage or UserManagementPage.
    If already on UserManagementPage, skips navigation.
    Sets ``ctx.page`` to UserManagementPage.
    """

    def _action(ctx):
        from sphere_e2e_test_framework.pages.e_admin.user_management_page import (
            UserManagementPage,
        )
        from sphere_e2e_test_framework.pages.e_admin import DashboardPage

        username = getattr(ctx.td, username_attr)

        page = ctx.page
        if isinstance(page, UserManagementPage):
            user_page = page
        elif hasattr(page, "goto_user"):
            user_page = page.goto_user(
                step_name="When: Navigate to User Management",
            )
        else:
            # Fallback: wrap current driver as DashboardPage (sidebar is available)
            dashboard = DashboardPage(ctx.driver, ctx.evidence)
            user_page = dashboard.goto_user(
                step_name="When: Navigate to User Management",
            )

        user_page.refresh(
            step_name="And: Refresh user list before deletion",
        )

        delete_msg = user_page.delete_user(
            username=username,
            step_name=f"When: Delete user '{username}'",
        )
        logger.info(f"Delete confirmation: '{delete_msg}'")

        user_page.refresh(
            step_name="And: Refresh user list after deletion",
        )
        assert not user_page.user_exists_in_table(username), (
            f"User '{username}' still found in table after deletion"
        )

        sync_msg = user_page.sync(
            step_name="And: Sync deletion to HSM",
        )
        logger.info(f"Sync message: '{sync_msg}'")
        logger.info(f"User '{username}' deleted successfully")
        ctx.page = user_page

    return Step("Delete user", _action)
