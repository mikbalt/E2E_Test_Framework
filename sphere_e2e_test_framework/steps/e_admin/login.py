"""
E-Admin login & session step factories.

Each function returns a Step that internally uses page objects.
Steps communicate via ``ctx.state`` / ``ctx.page``.
"""

import logging
import time

from sphere_e2e_test_framework.flows.base import Step

logger = logging.getLogger(__name__)


def _find_session(sessions, hint):
    """Find a session matching hint, raise if no match found."""
    match = next((s for s in sessions if hint in s), None)
    if match is None:
        raise ValueError(
            f"No session matching '{hint}' found. "
            f"Available sessions: {sessions}"
        )
    return match


def _poll_for_dashboard(dashboard, username, poll_timeout=30):
    """Poll dashboard label until username appears. Returns logged-in user string."""
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
    return logged_in_user


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
        session = _find_session(sessions, session_hint)
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
            logged_in_user = _poll_for_dashboard(dashboard, username, poll_timeout)
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
        session = _find_session(sessions, session_hint)
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
            _poll_for_dashboard(dashboard, username, poll_timeout)

        logger.info(f"Background complete — logged in as {label}")
        ctx.page = dashboard

    return Step(f"Background: Connect and login as {label}", _action,
                retries=retries, retry_delay=retry_delay)


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
        session = _find_session(sessions, session_hint)
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
        session = _find_session(sessions, session_hint)
        login_page.select_session(
            session,
            step_name=f"And: Select session '{session}'",
        )

        dashboard = login_page.login(
            username, password,
            step_name=f"And: '{username}' logs in",
        )

        _poll_for_dashboard(dashboard, username, poll_timeout)
        logger.info(f"{label} '{username}' logged in successfully")
        ctx.page = dashboard

    return Step(f"Login as {label}", _action)


def block_user_by_failed_logins(
    session_attr="user_session",
    username_attr="user_username",
    password_attr="user_password",
    wrong_password_attr="wrong_password",
    max_attempts_attr="max_attempts",
):
    """Block user by exhausting login attempts with wrong password,
    then verify account is locked with correct password.

    Expects ``ctx.page`` is LoginPage (post-logout).
    """

    def _action(ctx):
        login_page = ctx.page
        session_hint = getattr(ctx.td, session_attr)
        username = getattr(ctx.td, username_attr)
        correct_password = getattr(ctx.td, password_attr)
        wrong_password = getattr(ctx.td, wrong_password_attr)
        max_attempts = getattr(ctx.td, max_attempts_attr)

        # Open form and select session once
        login_page.open_login_form(
            step_name="And: Open login form for block attempt",
        )
        sessions = login_page.get_sessions()
        session = _find_session(sessions, session_hint)
        login_page.select_session(
            session,
            step_name=f"And: Select session '{session}'",
        )

        # Exhaust login attempts with wrong password
        for attempt in range(1, max_attempts + 1):
            error_msg = login_page.login_expect_failure(
                username, wrong_password,
                step_name=(
                    f"And: Attempt {attempt}/{max_attempts} — "
                    f"login as '{username}' with wrong password"
                ),
            )
            logger.info(
                f"Wrong password attempt {attempt}/{max_attempts}: '{error_msg}'"
            )

        # Now try with correct password — should fail (account locked)
        error_msg = login_page.login_expect_failure(
            username, correct_password,
            step_name=f"Then: Login as '{username}' with correct password (expect blocked)",
        )
        assert error_msg, (
            "Expected error message for blocked user login, got empty string"
        )
        logger.info(f"User '{username}' is blocked: '{error_msg}'")
        ctx.set("block_msg", error_msg)

    return Step("Block user by failed logins", _action)
