"""
Pre-composed E-Admin key ceremony flows.
"""

from sphere_e2e_test_framework.flows.base import Flow
from sphere_e2e_test_framework.steps.e_admin import (
    accept_ccmk_terms,
    accept_post_login_terms,
    accept_terms,
    authenticate_super_user,
    change_super_user_password,
    confirm_admin_and_transition,
    confirm_admin_and_transition_nonfips,
    connect,
    create_ceremony_user,
    create_key_custodians,
    finalize_ceremony,
    import_all_ccmk_components,
    import_all_ccmk_components_nonfips,
    kc_admin_login,
    start_hsm_init,
    wait_and_accept_terms,
)

# Shared steps: auth + admin creation (same for both FIPS and Non-FIPS)
_auth_and_admin = [
    authenticate_super_user(),
    create_ceremony_user(
        username_attr="admin_username",
        password_attr="admin_password",
        label="Admin",
    ),
]

# Shared steps: everything from admin transition to CCMK import
_ceremony_common = [
    wait_and_accept_terms(sleep_seconds=10, label="Custodians Creation T&C"),
    kc_admin_login(),
    accept_post_login_terms(),
    create_key_custodians(),
    accept_ccmk_terms(),
]

# FIPS tail: direct import (no intermediate T&C between KCs)
_ceremony_tail = [
    *_ceremony_common,
    import_all_ccmk_components(),
    finalize_ceremony(),
]

# Non-FIPS tail: import with T&C acceptance between each KC
_ceremony_tail_nonfips = [
    *_ceremony_common,
    import_all_ccmk_components_nonfips(),
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
    *_auth_and_admin,
    confirm_admin_and_transition(),
    *_ceremony_tail,
])

# ------------------------------------------------------------------
# Key Ceremony Non-FIPS (TC-37515)
#
# Post-reset only: single T&C → authenticate (no password change).
# authenticate_super_user() handles dismiss_ok internally.
# ctx.set("fips_mode", False) for Non-FIPS finalization.
# ------------------------------------------------------------------
key_ceremony_nonfips_flow = Flow("Key Ceremony (Non-FIPS)", [
    connect(),
    start_hsm_init(),
    accept_terms(label="Admin Creation T&C"),
    *_auth_and_admin,
    confirm_admin_and_transition_nonfips(),
    *_ceremony_tail_nonfips,
])
