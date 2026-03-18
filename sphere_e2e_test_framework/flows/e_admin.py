"""
Pre-composed E-Admin flows built from reusable steps.

Each flow is a ready-to-use Flow instance. Pass a FlowContext with the
appropriate test-data dataclass and run::

    from sphere_e2e_test_framework.flows.e_admin import delete_user_flow
    from sphere_e2e_test_framework.flows.base import FlowContext

    ctx = FlowContext(driver, evidence, DeleteOperationUserData.from_env())
    delete_user_flow.run(ctx)
"""

from sphere_e2e_test_framework.flows.base import Flow
from sphere_e2e_test_framework.steps.e_admin import (
    accept_ccmk_terms,
    accept_post_login_terms,
    accept_terms,
    authenticate_super_user,
    auto_setup_pre_auth,
    change_super_user_password,
    click_reset_and_decline,
    confirm_admin_and_transition,
    confirm_reset_with_admin_auth,
    connect,
    create_ceremony_user,
    create_key_custodians,
    create_profile,
    create_user,
    delete_user,
    dismiss_reset_completion,
    ensure_user_exists,
    export_audit_log,
    finalize_ceremony,
    full_login,
    import_all_ccmk_components,
    kc_admin_login,
    login_as_new_user,
    login_expect_failure,
    logout,
    refresh_and_sync,
    relogin_super_user,
    start_hsm_init,
    wait_and_accept_terms,
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
])

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
])

# ------------------------------------------------------------------
# Key Ceremony FIPS (TC-37509)
#
# Full ceremony from fresh HSM: all T&C pages + password change.
# ctx.set("fips_mode", True) for FIPS finalization.
# ------------------------------------------------------------------
_shared_ceremony_tail = [
    authenticate_super_user(),
    create_ceremony_user(
        username_attr="admin_username",
        password_attr="admin_password",
        label="Admin",
    ),
    confirm_admin_and_transition(),
    wait_and_accept_terms(sleep_seconds=10, label="Custodians Creation T&C"),
    kc_admin_login(),
    accept_post_login_terms(),
    create_key_custodians(),
    accept_ccmk_terms(),
    import_all_ccmk_components(),
    finalize_ceremony(),
]

key_ceremony_flow = Flow("Key Ceremony", [
    connect(),
    start_hsm_init(),
    accept_terms(label="Sphere HSM T&C"),
    accept_terms(label="Password Change T&C"),
    change_super_user_password(),
    accept_terms(label="Admin Creation T&C"),
    *_shared_ceremony_tail,
])

# ------------------------------------------------------------------
# Key Ceremony Non-FIPS (TC-37515)
#
# Auto-detects whether password change is needed:
#   Fresh HSM  → accepts all T&C + changes password
#   Post-reset → accepts Admin Creation T&C only
# ctx.set("fips_mode", False) for Non-FIPS finalization.
# ------------------------------------------------------------------
key_ceremony_nonfips_flow = Flow("Key Ceremony (Non-FIPS)", [
    connect(),
    start_hsm_init(),
    auto_setup_pre_auth(),
    *_shared_ceremony_tail,
])

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
