"""
Pre-composed E-Admin user management flows.
"""

from sphere_e2e_test_framework.flows.base import Flow
from sphere_e2e_test_framework.steps.e_admin import (
    block_user_by_failed_logins,
    create_profile,
    create_user,
    delete_user,
    ensure_user_blocked,
    ensure_user_exists,
    full_login,
    login_as_new_user,
    login_expect_failure,
    logout,
    refresh_and_sync,
    unblock_user,
)

# ------------------------------------------------------------------
# Delete Operation User (TC-37520)
# ------------------------------------------------------------------
delete_user_flow = Flow("Delete Operation User", [
    full_login(label="ADMIN"),
    ensure_user_exists(),
    delete_user(),
    logout(),
    login_expect_failure(label="deleted user"),
], cleanup_steps=[logout()])

# ------------------------------------------------------------------
# Block User (TC-37522)
#
# Login as ADMIN → ensure user exists → sync → logout →
# exhaust login attempts with wrong password → verify account locked.
# ------------------------------------------------------------------
block_user_flow = Flow("Block User", [
    full_login(label="ADMIN"),
    ensure_user_exists(),
    logout(),
    block_user_by_failed_logins(),
], cleanup_steps=[logout()])

# ------------------------------------------------------------------
# Unblock User
#
# Dynamic prerequisite: reads table status to decide what to do:
#   BLOCKED  → skip straight to unblock
#   ACTIVE   → block first, then unblock
#   Not found → create user, block, then unblock
# ------------------------------------------------------------------
unblock_user_flow = Flow("Unblock User", [
    full_login(label="ADMIN"),
    ensure_user_blocked(),
    unblock_user(),
    logout(),
    login_as_new_user(label="unblocked user"),
], cleanup_steps=[logout()])

# ------------------------------------------------------------------
# Add Operation User (TC-37516)
# ------------------------------------------------------------------
add_user_flow = Flow("Add Operation User", [
    full_login(label="ADMIN"),
    create_profile(),
    create_user(),
    refresh_and_sync(),
    logout(),
    login_as_new_user(label="new user"),
], cleanup_steps=[logout()])
