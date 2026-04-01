"""
Pre-composed E-Admin HSM reset flow.
"""

from sphere_e2e_test_framework.flows.base import Flow
from sphere_e2e_test_framework.steps.e_admin import (
    click_reset_and_decline,
    confirm_reset_with_admin_auth,
    dismiss_reset_completion,
    export_audit_log,
    full_login,
    relogin_super_user,
)

# ------------------------------------------------------------------
# HSM Reset by Super User (TC-37517)
# ------------------------------------------------------------------
hsm_reset_flow = Flow("HSM Reset by Super User", [
    full_login(
        session_attr="super_user_session",
        username_attr="super_user_username",
        password_attr="super_user_password",
        label="SUPER_USER",
    ),
    click_reset_and_decline(),
    export_audit_log(),
    relogin_super_user(),
    confirm_reset_with_admin_auth(),
    dismiss_reset_completion(),
])
