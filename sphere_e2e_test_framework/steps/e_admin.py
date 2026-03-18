"""
E-Admin step factories for flow orchestration.

Each function returns a Step that internally uses page objects.
Steps communicate via ``ctx.state`` / ``ctx.page``.

Attribute-name parameters (e.g. ``session_attr="admin_session"``) are
resolved at runtime via ``getattr(ctx.td, attr_name)`` so the same step
works with any test-data dataclass (AddOperationUserData,
DeleteOperationUserData, HSMResetData, etc.).

Usage::

    from sphere_e2e_test_framework.steps.e_admin import connect, full_login

    flow = Flow("Login", [
        connect(),
        full_login(label="ADMIN"),
    ])
"""

import logging
import time

from sphere_e2e_test_framework.flows.base import Step

logger = logging.getLogger(__name__)


# ======================================================================
# Connection & Login steps
# ======================================================================

def connect(retries=0, retry_delay=1.0):
    """Connect eAdmin to HSM. Sets ``ctx.page`` to DashboardPage."""

    def _action(ctx):
        from sphere_e2e_test_framework.pages.e_admin import LoginPage

        login = LoginPage(ctx.driver, ctx.evidence)
        dashboard = login.connect_to_hsm(
            step_name="Given: eAdmin is connected to HSM",
        )
        assert dashboard.is_visible(), "Dashboard not visible after connection"
        ctx.page = dashboard

    return Step("Connect", _action, retries=retries, retry_delay=retry_delay)


def open_login_form():
    """Open login form from dashboard. Sets ``ctx.page`` to LoginPage."""

    def _action(ctx):
        dashboard = ctx.page
        login_page = dashboard.open_login()
        login_page.open_login_form(
            step_name="And: Open login form",
        )
        ctx.page = login_page

    return Step("Open login form", _action)


def select_session(session_attr="admin_session", label=None):
    """Select session from combobox. Expects ``ctx.page`` is LoginPage.

    Args:
        session_attr: Attribute name on ctx.td for the session name.
        label: Display label for step name (defaults to session_attr).
    """

    def _action(ctx):
        login_page = ctx.page
        session_hint = getattr(ctx.td, session_attr)
        sessions = login_page.get_sessions()
        session = next(
            (s for s in sessions if session_hint in s), sessions[0],
        )
        login_page.select_session(
            session,
            step_name=f"And: Select session '{session}'",
        )
        ctx.set("selected_session", session)

    _label = label or session_attr
    return Step(f"Select session ({_label})", _action)


def login_with_credentials(
    username_attr="admin_username",
    password_attr="admin_password",
    label="ADMIN",
    poll=True,
    poll_timeout=30,
):
    """Login with credentials. Sets ``ctx.page`` to DashboardPage.

    Args:
        username_attr: Attribute name on ctx.td for username.
        password_attr: Attribute name on ctx.td for password.
        label: Human-readable label for the step.
        poll: If True, poll ``get_logged_in_user`` to verify login.
        poll_timeout: Max seconds to poll (default 30).
    """

    def _action(ctx):
        login_page = ctx.page
        username = getattr(ctx.td, username_attr)
        password = getattr(ctx.td, password_attr)

        dashboard = login_page.login(
            username, password,
            step_name=f"And: {label} logs in to eAdmin",
        )

        if poll:
            logged_in_user = ""
            attempts = poll_timeout // 2
            for _ in range(attempts):
                logged_in_user = dashboard.get_logged_in_user()
                if username.lower() in logged_in_user.lower():
                    break
                time.sleep(2)
            assert username.lower() in logged_in_user.lower(), (
                f"Expected '{username}' in label, got '{logged_in_user}'"
            )
            logger.info(f"Logged in as '{logged_in_user}'")

        ctx.page = dashboard

    return Step(f"Login as {label}", _action)


def full_login(
    session_attr="admin_session",
    username_attr="admin_username",
    password_attr="admin_password",
    label="ADMIN",
    poll=True,
    poll_timeout=30,
    retries=0,
    retry_delay=1.0,
):
    """All-in-one: connect → open form → select session → login.

    Sets ``ctx.page`` to DashboardPage.
    """

    def _action(ctx):
        from sphere_e2e_test_framework.pages.e_admin import LoginPage

        login = LoginPage(ctx.driver, ctx.evidence)
        dashboard = login.connect_to_hsm(
            step_name="Given: eAdmin is connected to HSM",
        )
        assert dashboard.is_visible(), "Dashboard not visible after connection"

        login_page = dashboard.open_login()
        login_page.open_login_form(
            step_name="And: Open login form",
        )

        session_hint = getattr(ctx.td, session_attr)
        sessions = login_page.get_sessions()
        session = next(
            (s for s in sessions if session_hint in s), sessions[0],
        )
        login_page.select_session(
            session,
            step_name=f"And: Select session '{session}'",
        )

        username = getattr(ctx.td, username_attr)
        password = getattr(ctx.td, password_attr)
        dashboard = login_page.login(
            username, password,
            step_name=f"And: {label} logs in to eAdmin",
        )

        if poll:
            logged_in_user = ""
            attempts = poll_timeout // 2
            for _ in range(attempts):
                logged_in_user = dashboard.get_logged_in_user()
                if username.lower() in logged_in_user.lower():
                    break
                time.sleep(2)
            assert username.lower() in logged_in_user.lower(), (
                f"Expected '{username}' in label, got '{logged_in_user}'"
            )

        logger.info(f"Background complete — logged in as {label}")
        ctx.page = dashboard

    return Step(f"Background: Connect and login as {label}", _action,
                retries=retries, retry_delay=retry_delay)


# ======================================================================
# Navigation steps
# ======================================================================

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


# ======================================================================
# Profile & User CRUD steps
# ======================================================================

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


# ======================================================================
# Logout & verification steps
# ======================================================================

def logout():
    """Logout current user. Sets ctx.page to LoginPage (via DashboardPage).

    Expects ``ctx.page`` is DashboardPage or has a reference to dashboard.
    """

    def _action(ctx):
        from sphere_e2e_test_framework.pages.e_admin import DashboardPage

        dashboard = ctx.page
        if not isinstance(dashboard, DashboardPage):
            dashboard = DashboardPage(ctx.driver, ctx.evidence)

        login_page = dashboard.logout(
            step_name="When: Current user logs out",
        )
        ctx.page = login_page

    return Step("Logout", _action)


def login_expect_failure(
    session_attr="user_session",
    username_attr="user_username",
    password_attr="user_password",
    label="deleted user",
):
    """Attempt login expecting failure. Verifies error message and login form still visible.

    Expects ``ctx.page`` is LoginPage (post-logout).
    """

    def _action(ctx):
        login_page = ctx.page
        session_hint = getattr(ctx.td, session_attr)
        username = getattr(ctx.td, username_attr)
        password = getattr(ctx.td, password_attr)

        login_page.open_login_form(
            step_name=f"And: Open login form for {label}",
        )

        sessions = login_page.get_sessions()
        session = next(
            (s for s in sessions if session_hint in s), sessions[0],
        )
        login_page.select_session(
            session,
            step_name=f"And: Select session '{session}'",
        )

        error_msg = login_page.login_expect_failure(
            username, password,
            step_name=f"And: Attempt login as {label} '{username}'",
        )
        assert error_msg, (
            "Expected error message for login, got empty string"
        )
        logger.info(f"Login error message: '{error_msg}'")

        assert ctx.driver.element_exists(
            auto_id="btnLogin", control_type="Button",
        ), "Login form should still be visible after failed login attempt"
        logger.info(f"Login correctly rejected for {label} '{username}'")

    return Step(f"Verify {label} login fails", _action)


def login_as_new_user(
    session_attr="user_session",
    username_attr="user_username",
    password_attr="user_password",
    label="new user",
    poll_timeout=30,
):
    """Logout then login as newly created user, verify success.

    Expects ``ctx.page`` is LoginPage (post-logout).
    Sets ``ctx.page`` to DashboardPage.
    """

    def _action(ctx):
        login_page = ctx.page
        session_hint = getattr(ctx.td, session_attr)
        username = getattr(ctx.td, username_attr)
        password = getattr(ctx.td, password_attr)

        login_page.open_login_form(
            step_name=f"And: Open login form for {label}",
        )

        sessions = login_page.get_sessions()
        session = next(
            (s for s in sessions if session_hint in s), sessions[0],
        )
        login_page.select_session(
            session,
            step_name=f"And: Select session '{session}'",
        )

        dashboard = login_page.login(
            username, password,
            step_name=f"And: '{username}' logs in",
        )

        # Poll for label update
        logged_in_user = ""
        attempts = poll_timeout // 2
        for _ in range(attempts):
            logged_in_user = dashboard.get_logged_in_user()
            if username in logged_in_user.lower():
                break
            time.sleep(2)

        assert username in logged_in_user.lower(), (
            f"Expected '{username}' in label, got '{logged_in_user}'"
        )
        logger.info(f"{label} '{username}' logged in successfully")
        ctx.page = dashboard

    return Step(f"Login as {label}", _action)


# ======================================================================
# Key Ceremony steps
# ======================================================================

def start_hsm_init():
    """Dashboard → click HSM Init → sets ``ctx.page`` to TermsPage."""

    def _action(ctx):
        dashboard = ctx.page
        terms = dashboard.start_hsm_init(
            step_name="When: User starts HSM Initialization",
        )
        ctx.page = terms

    return Step("Start HSM Initialization", _action)


def accept_terms(label="Terms & Conditions"):
    """Accept Terms & Conditions page. Expects ``ctx.page`` is TermsPage."""

    def _action(ctx):
        from sphere_e2e_test_framework.pages.e_admin import TermsPage

        page = ctx.page
        if not isinstance(page, TermsPage):
            page = TermsPage(ctx.driver, ctx.evidence)
        page.accept(
            step_name=f"And: User accepts {label}",
        )
        ctx.page = page

    return Step(f"Accept {label}", _action)


def change_super_user_password(
    old_attr="default_super_user_pass",
    new_attr="new_super_user_pass",
):
    """Change SUPER_USER default password during ceremony."""

    def _action(ctx):
        from sphere_e2e_test_framework.pages.e_admin import PasswordChangePage

        old_pass = getattr(ctx.td, old_attr)
        new_pass = getattr(ctx.td, new_attr)
        pwd = PasswordChangePage(ctx.driver, ctx.evidence)
        pwd.change_password(
            old_pass, new_pass,
            step_name="And: SUPER_USER changes the default password",
        )

    return Step("Change SUPER_USER password", _action)


def auto_setup_pre_auth(
    old_attr="default_super_user_pass",
    new_attr="new_super_user_pass",
):
    """Auto-detect and handle all T&C pages + password change before authenticate.

    After ``start_hsm_init()``, loops through the UI screens:
    - If ``rbAgree`` is visible → accept the T&C page
    - If ``txtOldPass`` is visible → change the SUPER_USER password

    Stops when neither is found (authenticate screen reached).

    Handles both scenarios automatically:
    - **Fresh HSM**: Sphere HSM T&C → Password Change T&C → change password → Admin Creation T&C
    - **Post-reset**: Admin Creation T&C only (password already changed)
    """

    def _action(ctx):
        from sphere_e2e_test_framework.pages.e_admin import PasswordChangePage, TermsPage

        terms = TermsPage(ctx.driver, ctx.evidence)
        tc_count = 0
        password_changed = False

        for _ in range(10):  # safety limit
            if ctx.driver.element_exists(auto_id="txtOldPass"):
                old_pass = getattr(ctx.td, old_attr)
                new_pass = getattr(ctx.td, new_attr)
                pwd = PasswordChangePage(ctx.driver, ctx.evidence)
                pwd.change_password(
                    old_pass, new_pass,
                    step_name="And: SUPER_USER changes the default password",
                )
                password_changed = True
            elif ctx.driver.element_exists(auto_id="rbAgree", found_index=0):
                tc_count += 1
                terms.accept(step_name=f"And: Accept Terms & Conditions ({tc_count})")
            else:
                break

        mode = "fresh HSM" if password_changed else "post-reset"
        logger.info(
            f"Pre-auth setup complete ({mode}): "
            f"{tc_count} T&C pages, password_changed={password_changed}"
        )

    return Step("Handle T&C and password setup (auto-detect)", _action)


def authenticate_super_user(password_attr="new_super_user_pass"):
    """Authenticate SUPER_USER for admin creation during ceremony."""

    def _action(ctx):
        from sphere_e2e_test_framework.pages.e_admin import UserCreationPage

        password = getattr(ctx.td, password_attr)
        user_page = UserCreationPage(ctx.driver, ctx.evidence)
        user_page.authenticate_super_user(
            password,
            step_name="And: SUPER_USER authenticates with new credentials",
        )
        ctx.set("_ceremony_user_page", user_page)

    return Step("Authenticate SUPER_USER", _action)


def create_ceremony_user(
    username_attr="admin_username",
    password_attr="admin_password",
    add_button_id=None,
    label="Admin",
):
    """Create a user during key ceremony (Admin, KC, or Auditor)."""

    def _action(ctx):
        from sphere_e2e_test_framework.pages.e_admin import UserCreationPage

        user_page = ctx.get("_ceremony_user_page") or UserCreationPage(ctx.driver, ctx.evidence)
        username = getattr(ctx.td, username_attr)
        password = getattr(ctx.td, password_attr)
        user_page.create_user(
            username, password,
            add_button_id=add_button_id,
            step_name=f"And: Creates {label} account",
        )
        ctx.set("_ceremony_user_page", user_page)

    return Step(f"Create {label} account", _action)


def confirm_admin_and_transition():
    """Post-admin-creation: dismiss_ok → sleep(10) → refresh → wait → accept T&C."""

    def _action(ctx):
        from sphere_e2e_test_framework.pages.base_page import BasePage, TIMEOUT
        from sphere_e2e_test_framework.pages.e_admin import TermsPage

        base = BasePage(ctx.driver, ctx.evidence)
        base.dismiss_ok(
            step_name="Then: Admin account created successfully",
        )
        time.sleep(10)
        ctx.driver.refresh_window()
        ctx.driver.wait_for_element(timeout=TIMEOUT, auto_id="rbAgree", found_index=0)
        terms = TermsPage(ctx.driver, ctx.evidence)
        terms.accept(
            step_name="And: Accept post-admin-creation Terms & Conditions",
        )
        ctx.page = terms

    return Step("Confirm admin and transition", _action)


def wait_and_accept_terms(sleep_seconds=10, label="Terms & Conditions"):
    """Sleep → refresh → wait for rbAgree → accept T&C."""

    def _action(ctx):
        from sphere_e2e_test_framework.pages.base_page import TIMEOUT
        from sphere_e2e_test_framework.pages.e_admin import TermsPage

        time.sleep(sleep_seconds)
        ctx.driver.refresh_window()
        ctx.driver.wait_for_element(timeout=TIMEOUT, auto_id="rbAgree", found_index=0)
        terms = TermsPage(ctx.driver, ctx.evidence)
        terms.accept(
            step_name=f"When: User accepts {label}",
        )
        ctx.page = terms

    return Step(f"Wait and accept {label}", _action)


def kc_admin_login(
    username_attr="admin_username",
    password_attr="admin_password",
):
    """Admin login during ceremony via KCLoginPage + refresh + wait."""

    def _action(ctx):
        from sphere_e2e_test_framework.pages.base_page import TIMEOUT
        from sphere_e2e_test_framework.pages.e_admin import KCLoginPage

        username = getattr(ctx.td, username_attr)
        password = getattr(ctx.td, password_attr)
        kc_login = KCLoginPage(ctx.driver, ctx.evidence)
        kc_login.login(
            username, password,
            step_name="And: Admin logs in with credentials",
        )
        ctx.driver.refresh_window()
        ctx.driver.wait_for_element(timeout=TIMEOUT, auto_id="rbAgree", found_index=0)
        ctx.set("_kc_login_page", kc_login)

    return Step("Admin login during ceremony", _action)


def accept_post_login_terms():
    """Click rbAgree + dismiss_ok (non-standard T&C, no btnNext)."""

    def _action(ctx):
        from sphere_e2e_test_framework.pages.base_page import BasePage

        ctx.driver.click_radio(auto_id="rbAgree")
        base = BasePage(ctx.driver, ctx.evidence)
        base.dismiss_ok(
            step_name="And: Admin accepts post-login Terms & Conditions",
        )

    return Step("Accept post-login terms", _action)


def create_key_custodians():
    """Loop key custodians + create auditor. Data-driven from ctx.td."""

    def _action(ctx):
        from sphere_e2e_test_framework.pages.e_admin import UserCreationPage

        user_page = ctx.get("_ceremony_user_page") or UserCreationPage(ctx.driver, ctx.evidence)

        for i, kc in enumerate(ctx.td.key_custodians, start=1):
            user_page.create_user(
                username=kc.username,
                password=kc.password,
                add_button_id=kc.add_button,
                step_name=f"And: Admin creates Key Custodian {i} ({kc.username}) account",
            )

        user_page.create_user(
            username=ctx.td.auditor_username,
            password=ctx.td.auditor_password,
            add_button_id="btnAuditorCreate",
            step_name=f"And: Admin creates Auditor ({ctx.td.auditor_username}) account",
        )

    return Step("Create key custodians and auditor", _action)


def accept_ccmk_terms():
    """Accept 3-page CCMK T&C sequence with inter-page sleeps."""

    def _action(ctx):
        from sphere_e2e_test_framework.pages.e_admin import TermsPage

        terms = TermsPage(ctx.driver, ctx.evidence)

        terms.accept(
            step_name="When: User accepts CCMK Import Terms & Conditions (page 1/3)",
        )
        time.sleep(30)

        terms.accept(
            step_name="And: User accepts CCMK Import Terms & Conditions (page 2/3)",
        )
        time.sleep(5)

        terms.accept(
            step_name="And: User accepts CCMK Import Terms & Conditions (page 3/3)",
        )

    return Step("Accept CCMK terms (3 pages)", _action)


def import_all_ccmk_components():
    """Loop KCs: KCLoginPage.login() → CCMKImportPage.import_component() → next()."""

    def _action(ctx):
        from sphere_e2e_test_framework.pages.e_admin import KCLoginPage

        kc_login = ctx.get("_kc_login_page") or KCLoginPage(ctx.driver, ctx.evidence)

        for i, kc in enumerate(ctx.td.key_custodians, start=1):
            is_last = (i == len(ctx.td.key_custodians))

            ccmk_page = kc_login.login(
                kc.username, kc.password,
                step_name=f"And: Key Custodian {i} ({kc.username}) logs in",
            )
            ccmk_page.import_component(
                kc.ccmk_secret,
                kc.ccmk_kcv,
                kc.ccmk_combined_kcv if is_last else None,
                step_name=f"And: Key Custodian {i} ({kc.username}) imports CCMK component",
            )
            if not is_last:
                ccmk_page.next()

    return Step("Import all CCMK components", _action)


def finalize_ceremony():
    """Select FIPS or non-FIPS and finalize. Reads ``ctx.get('fips_mode', True)``."""

    def _action(ctx):
        from sphere_e2e_test_framework.pages.e_admin import KeyCeremonyFlow

        fips_mode = ctx.get("fips_mode", True)
        ceremony = KeyCeremonyFlow(ctx.driver, ctx.evidence)

        if fips_mode:
            ceremony.select_fips_and_finalize(
                step_name="When: User selects FIPS mode of operation and finalizes",
            )
        else:
            ceremony.select_non_fips_and_finalize(
                step_name="When: User selects Non-FIPS mode of operation and finalizes",
            )

        logger.info("Key Ceremony completed successfully")

    return Step("Finalize ceremony", _action)


# ======================================================================
# HSM Reset steps
# ======================================================================

def click_reset_and_decline():
    """Click btnReset → decline first prompt (No) → dismiss 2x info popups (OK)."""

    def _action(ctx):
        from sphere_e2e_test_framework.driver.evidence import tracked_step
        from sphere_e2e_test_framework.pages.base_page import TIMEOUT

        with tracked_step(ctx.evidence, ctx.driver, "When: SUPER_USER clicks Reset"):
            ctx.driver.click_button(auto_id="btnReset")

        with tracked_step(ctx.evidence, ctx.driver, "And: Decline first reset prompt (No)"):
            ctx.driver.wait_for_element(
                timeout=TIMEOUT, auto_id="7", control_type="Button",
            )
            ctx.driver.click_button(auto_id="7")

        for label in ("And: Dismiss info popup (OK)", "And: Dismiss second info popup (OK)"):
            with tracked_step(ctx.evidence, ctx.driver, label):
                ctx.driver.wait_for_element(
                    timeout=TIMEOUT, auto_id="2", control_type="Button",
                )
                ctx.driver.click_button(auto_id="2")

    return Step("Click Reset and decline", _action)


def export_audit_log(
    auditor_user_attr="auditor_username",
    auditor_pass_attr="auditor_password",
):
    """Export audit log: click Export → Yes → auditor auth → read notification → dismiss."""

    def _action(ctx):
        import allure
        from sphere_e2e_test_framework.driver.evidence import tracked_step
        from sphere_e2e_test_framework.pages.base_page import TIMEOUT

        auditor_user = getattr(ctx.td, auditor_user_attr)
        auditor_pass = getattr(ctx.td, auditor_pass_attr)

        with tracked_step(ctx.evidence, ctx.driver, "When: Click Export Log button"):
            ctx.driver.wait_for_element(
                timeout=TIMEOUT, auto_id="btnExportLog", control_type="Button",
            )
            ctx.driver.click_button(auto_id="btnExportLog")

        with tracked_step(ctx.evidence, ctx.driver, "And: Confirm export log (Yes)"):
            ctx.driver.wait_for_element(
                timeout=TIMEOUT, auto_id="6", control_type="Button",
            )
            ctx.driver.click_button(auto_id="6")

        with tracked_step(ctx.evidence, ctx.driver, "And: Auditor authenticates for log export"):
            ctx.driver.wait_for_element(
                timeout=TIMEOUT, auto_id="1001", control_type="Edit",
            )
            ctx.driver.type_text(auditor_user, auto_id="1001")
            ctx.driver.type_text(
                auditor_pass, auto_id="txtPassword", sensitive=True,
            )
            ctx.driver.click_button(auto_id="btnAuth")

        with tracked_step(ctx.evidence, ctx.driver, "Then: Log file saved notification displayed"):
            log_label = ctx.driver.wait_for_element(
                timeout=TIMEOUT, auto_id="65535", control_type="Text",
            )
            log_notification = log_label.window_text()
            logger.info(f"Audit log notification: {log_notification}")
            allure.attach(
                log_notification,
                name="Audit Log Export — Path & Filename",
                attachment_type=allure.attachment_type.TEXT,
            )

        with tracked_step(ctx.evidence, ctx.driver, "And: Dismiss log saved notification (OK)"):
            ctx.driver.wait_for_element(
                timeout=TIMEOUT, auto_id="2", control_type="Button",
            )
            ctx.driver.click_button(auto_id="2")

        logger.info("Audit log exported via auditor")

    return Step("Export audit log", _action)


def relogin_super_user(
    username_attr="super_user_username",
    password_attr="super_user_password",
):
    """Re-login as SUPER_USER via raw driver (post-export UI state)."""

    def _action(ctx):
        from sphere_e2e_test_framework.driver.evidence import tracked_step
        from sphere_e2e_test_framework.pages.base_page import TIMEOUT

        username = getattr(ctx.td, username_attr)
        password = getattr(ctx.td, password_attr)

        with tracked_step(ctx.evidence, ctx.driver, "When: Re-open login form"):
            ctx.driver.wait_for_element(
                timeout=TIMEOUT, auto_id="lbl_clickLogin", control_type="Text",
            )
            ctx.driver.click_element(auto_id="lbl_clickLogin", control_type="Text")

        with tracked_step(ctx.evidence, ctx.driver, "And: SUPER_USER re-logs in"):
            ctx.driver.wait_for_element(
                timeout=TIMEOUT, auto_id="rbPassword",
            )
            ctx.driver.click_radio(auto_id="rbPassword")
            ctx.driver.type_text(username, auto_id="1001")
            ctx.driver.type_text(
                password, auto_id="txtPassword", sensitive=True,
            )
            ctx.driver.click_button(auto_id="btnLogin")
            ctx.driver.wait_for_element(
                timeout=TIMEOUT, auto_id="btnLogOut", control_type="Button",
            )
            logger.info("SUPER_USER re-logged in successfully")

    return Step("Re-login as SUPER_USER", _action)


def confirm_reset_with_admin_auth(
    admin_user_attr="admin_username",
    admin_pass_attr="admin_password",
):
    """Click Reset → Yes x2 → multi-window ADMIN auth via findwindows."""

    def _action(ctx):
        from sphere_e2e_test_framework.driver.evidence import tracked_step
        from sphere_e2e_test_framework.pages.base_page import TIMEOUT

        admin_user = getattr(ctx.td, admin_user_attr)
        admin_pass = getattr(ctx.td, admin_pass_attr)

        with tracked_step(ctx.evidence, ctx.driver, "When: SUPER_USER clicks Reset (2nd time)"):
            ctx.driver.click_button(auto_id="btnReset")

        with tracked_step(ctx.evidence, ctx.driver, "And: Confirm reset prompt (Yes)"):
            ctx.driver.wait_for_element(
                timeout=TIMEOUT, auto_id="6", control_type="Button",
            )
            ctx.driver.click_button(auto_id="6")

        with tracked_step(ctx.evidence, ctx.driver, "And: Confirm second reset prompt (Yes)"):
            ctx.driver.wait_for_element(
                timeout=TIMEOUT, auto_id="6", control_type="Button",
            )
            ctx.driver.click_button(auto_id="6")

        time.sleep(2)
        with tracked_step(ctx.evidence, ctx.driver, "And: ADMIN authenticates to authorize reset"):
            from pywinauto import findwindows

            handles = findwindows.find_windows(
                process=ctx.driver.app.process, backend="uia",
            )
            auth_win = None
            for h in handles:
                try:
                    w = ctx.driver.app.window(handle=h)
                    if w.child_window(auto_id="panel1").exists(timeout=1):
                        auth_win = w
                        break
                except Exception:
                    continue
            assert auth_win is not None, (
                f"Auth dialog (panel1) not found in {len(handles)} window(s)"
            )
            logger.info(f"Auth window found: handle={auth_win.handle}")

            auth_win.child_window(
                auto_id="1001", control_type="Edit",
            ).wait("visible", timeout=TIMEOUT)
            auth_win.child_window(
                auto_id="1001", control_type="Edit",
            ).set_edit_text(admin_user)
            auth_win.child_window(
                auto_id="txtPassword", control_type="Edit",
            ).set_edit_text(admin_pass)
            auth_win.child_window(auto_id="btnAuth").click_input()
            time.sleep(1)

    return Step("Confirm reset with ADMIN auth", _action)


def dismiss_reset_completion():
    """Dismiss sync confirmation (OK) + reset finished (No) via find_element_in_any_window."""

    def _action(ctx):
        from sphere_e2e_test_framework.driver.evidence import tracked_step
        from sphere_e2e_test_framework.pages.base_page import TIMEOUT

        with tracked_step(ctx.evidence, ctx.driver, "Then: Dismiss sync confirmation (OK)"):
            ok_btn = ctx.driver.find_element_in_any_window(
                auto_id="2", control_type="Button", timeout=TIMEOUT,
            )
            logger.info("Sync confirmation popup found")
            ok_btn.click_input()
            time.sleep(1)

        with tracked_step(ctx.evidence, ctx.driver, "Then: HSM Reset finished — click No to close eADMIN"):
            no_btn = ctx.driver.find_element_in_any_window(
                auto_id="7", control_type="Button", timeout=TIMEOUT,
            )
            logger.info(
                "HSM Reset Procedure has been finished successfully. "
                "HSM Initialization and Key Ceremony will be required."
            )
            no_btn.click_input()
            time.sleep(1)

        logger.info("HSM Reset completed successfully")

    return Step("Dismiss reset completion", _action)
