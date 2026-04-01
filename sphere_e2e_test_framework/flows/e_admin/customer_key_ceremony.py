"""
Pre-composed E-Admin Customer Key Ceremony (CKC) flows.

- Generate & Export: create KCPs, generate key, export per KCP, verify summary
- Import: reuse KCPs, import key components per KCP, configure key, finalize

Precondition: FIPS Key Ceremony must be completed first.
"""

from sphere_e2e_test_framework.flows.base import Flow
from sphere_e2e_test_framework.steps.e_admin import connect
from sphere_e2e_test_framework.steps.e_admin.customer_key_ceremony import (
    ckc_accept_terms,
    ckc_configure_key,
    ckc_create_custodian_parties,
    ckc_export_all_custodian_keys,
    ckc_finish,
    ckc_generate_key,
    ckc_login_admin,
    ckc_proceed_next,
    ckc_select_generate_and_export,
    ckc_verify_key_summary,
    start_ckc,
)
from sphere_e2e_test_framework.steps.e_admin.customer_key_ceremony_import import (
    ckc_dismiss_reuse_kcps,
    ckc_import_all_components,
    ckc_select_import_mode,
)

# ------------------------------------------------------------------
# Customer Key Ceremony — Generate & Export (TC-XXXXX)
#
# Precondition: FIPS Key Ceremony completed.
# Flow: Connect → CKC → Accept Terms → Admin login →
#       Create 3 KCPs → Next → Select GENERATE_AND_EXPORT →
#       Configure key → Generate → Export per KCP →
#       Verify summary → Finish
# ------------------------------------------------------------------
customer_key_ceremony_flow = Flow("Customer Key Ceremony", [
    connect(),
    start_ckc(),
    ckc_accept_terms(),
    ckc_login_admin(),
    ckc_create_custodian_parties(),
    ckc_proceed_next(),
    ckc_select_generate_and_export(),
    ckc_configure_key(),
    ckc_generate_key(),
    ckc_export_all_custodian_keys(),
    ckc_verify_key_summary(),
    ckc_finish(),
])

# ------------------------------------------------------------------
# Customer Key Ceremony — Import (TC-XXXXX)
#
# Precondition: CKC Generate & Export completed (KCPs exist).
# Flow: Connect → CKC → Accept Terms → Admin login →
#       Reuse existing KCPs → Select IMPORT →
#       For each KCP: accept understanding → login → import component →
#       Last KCP: full key config + finalize
# ------------------------------------------------------------------
customer_key_ceremony_import_flow = Flow("Customer Key Ceremony Import", [
    connect(),
    start_ckc(),
    ckc_accept_terms(),
    ckc_login_admin(),
    ckc_dismiss_reuse_kcps(),
    ckc_select_import_mode(),
    ckc_import_all_components(),
])
