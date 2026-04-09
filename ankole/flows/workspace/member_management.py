"""Member management flows for workspace application.

Pre-composed flows for common member operations:
    add_member_flow      — login as admin, create member, verify
    delete_member_flow   — login as admin, delete member, verify
    suspend_member_flow  — login as admin, suspend member, verify status
    reactivate_member_flow — login as admin, reactivate member, verify status
"""

from ankole.flows.base import Flow
from ankole.steps.workspace.login import full_login, logout
from ankole.steps.workspace.member_management import (
    create_member,
    delete_member,
    suspend_member,
    reactivate_member,
    verify_member_exists,
    verify_member_status,
)


def add_member_flow(
    admin_user: str,
    admin_pass: str,
    member_username: str,
    member_email: str,
    member_password: str,
    member_role: str = "member",
    base_url: str = "",
) -> Flow:
    """Flow: login as admin, create a member, verify they appear in table."""
    return Flow(
        f"Add Member: {member_username}",
        steps=[
            full_login(admin_user, admin_pass, base_url),
            create_member(
                member_username, member_email, member_password,
                member_role, base_url,
            ),
            verify_member_exists(member_username, base_url),
        ],
        cleanup_steps=[logout(base_url)],
    )


def delete_member_flow(
    admin_user: str,
    admin_pass: str,
    member_username: str,
    base_url: str = "",
) -> Flow:
    """Flow: login as admin, delete a member."""
    return Flow(
        f"Delete Member: {member_username}",
        steps=[
            full_login(admin_user, admin_pass, base_url),
            delete_member(member_username, base_url),
        ],
        cleanup_steps=[logout(base_url)],
    )


def suspend_member_flow(
    admin_user: str,
    admin_pass: str,
    member_username: str,
    base_url: str = "",
) -> Flow:
    """Flow: login as admin, suspend a member, verify suspended status."""
    return Flow(
        f"Suspend Member: {member_username}",
        steps=[
            full_login(admin_user, admin_pass, base_url),
            suspend_member(member_username, base_url),
            verify_member_status(member_username, "suspended", base_url),
        ],
        cleanup_steps=[logout(base_url)],
    )


def reactivate_member_flow(
    admin_user: str,
    admin_pass: str,
    member_username: str,
    base_url: str = "",
) -> Flow:
    """Flow: login as admin, reactivate a member, verify active status."""
    return Flow(
        f"Reactivate Member: {member_username}",
        steps=[
            full_login(admin_user, admin_pass, base_url),
            reactivate_member(member_username, base_url),
            verify_member_status(member_username, "active", base_url),
        ],
        cleanup_steps=[logout(base_url)],
    )
