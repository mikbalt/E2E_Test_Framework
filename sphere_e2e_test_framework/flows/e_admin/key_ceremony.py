"""
Pre-composed E-Admin key ceremony flows.
"""

from sphere_e2e_test_framework.flows.base import Flow
from sphere_e2e_test_framework.steps.e_admin import (
    accept_ccmk_terms,
    accept_post_login_terms,
    accept_terms,
    authenticate_super_user,
    auto_setup_pre_auth,
    change_super_user_password,
    confirm_admin_and_transition,
    connect,
    create_ceremony_user,
    create_key_custodians,
    finalize_ceremony,
    import_all_ccmk_components,
    kc_admin_login,
    start_hsm_init,
    wait_and_accept_terms,
)

# Shared tail for both FIPS and non-FIPS ceremonies
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

# ------------------------------------------------------------------
# Key Ceremony FIPS (TC-37509)
#
# Full ceremony from fresh HSM: all T&C pages + password change.
# ctx.set("fips_mode", True) for FIPS finalization.
# ------------------------------------------------------------------
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
