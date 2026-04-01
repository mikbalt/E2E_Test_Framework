"""
E-Admin Customer Key Ceremony (CKC) step factories.

Each function returns a Step that internally uses the CustomerKeyCeremonyPage.
Steps communicate via ``ctx.state`` / ``ctx.page``.

Precondition: FIPS Key Ceremony must be completed first.
"""

import logging

from sphere_e2e_test_framework.flows.base import Step

logger = logging.getLogger(__name__)


def start_ckc():
    """Dashboard → click Customer Key Ceremony button."""

    def _action(ctx):
        from sphere_e2e_test_framework.pages.e_admin.ckc_page import CustomerKeyCeremonyPage

        ckc = CustomerKeyCeremonyPage(ctx.driver, ctx.evidence)
        ckc.start_ckc(
            step_name="When: User starts Customer Key Ceremony",
        )
        ctx.set("_ckc_page", ckc)

    return Step("Start Customer Key Ceremony", _action)


def ckc_accept_terms():
    """Accept Terms & Conditions for CKC (rbAgree + btnNext)."""

    def _action(ctx):
        from sphere_e2e_test_framework.pages.e_admin.ckc_page import CustomerKeyCeremonyPage

        ckc = ctx.get("_ckc_page") or CustomerKeyCeremonyPage(ctx.driver, ctx.evidence)
        ckc.agree_and_next(
            step_name="And: User accepts CKC Terms & Conditions",
        )

    return Step("Accept CKC Terms", _action)


def ckc_login_admin(
    username_attr="admin_username",
    password_attr="admin_password",
):
    """Admin login during CKC via password authentication."""

    def _action(ctx):
        from sphere_e2e_test_framework.pages.e_admin.ckc_page import CustomerKeyCeremonyPage

        ckc = ctx.get("_ckc_page") or CustomerKeyCeremonyPage(ctx.driver, ctx.evidence)
        username = getattr(ctx.td, username_attr)
        password = getattr(ctx.td, password_attr)
        ckc.login_admin(
            username, password,
            step_name="And: Admin logs in for CKC",
        )

    return Step("Admin login for CKC", _action)


def ckc_create_custodian_parties():
    """Loop custodian parties and create each one. Data-driven from ctx.td."""

    def _action(ctx):
        from sphere_e2e_test_framework.pages.e_admin.ckc_page import CustomerKeyCeremonyPage

        ckc = ctx.get("_ckc_page") or CustomerKeyCeremonyPage(ctx.driver, ctx.evidence)

        for i, kcp in enumerate(ctx.td.custodian_parties, start=1):
            ckc.create_custodian_party(
                username=kcp.username,
                password=kcp.password,
                add_button_id=kcp.add_button,
                step_name=f"And: Creates Key Custodian Party {i} ({kcp.username})",
            )

        logger.info(f"All {len(ctx.td.custodian_parties)} custodian parties created")

    return Step("Create all custodian parties", _action)


def ckc_proceed_next():
    """Click Next after custodian creation → dismiss OK → wait for mode selection.

    Follows the same pattern as ``confirm_admin_and_transition`` in the
    FIPS key ceremony: dismiss confirmation dialog, brief pause for the
    HSM to process, refresh UI tree, then wait for the next screen element.
    """

    def _action(ctx):
        from sphere_e2e_test_framework.pages.base_page import BasePage, TIMEOUT

        ctx.driver.click_button(auto_id="btnNext")
        logger.info("Next clicked — waiting for HSM to process...")

        base = BasePage(ctx.driver, ctx.evidence)
        base.dismiss_ok(
            step_name="Then: Custodian parties created successfully",
        )
        time.sleep(10)
        ctx.driver.refresh_window()
        ctx.driver.wait_for_element(
            timeout=TIMEOUT, auto_id="rbDisagree",
        )
        logger.info("Operation mode selection screen ready")

    return Step("Proceed to next phase", _action)


def ckc_select_generate_and_export():
    """Select GENERATE_AND_EXPORT mode and proceed."""

    def _action(ctx):
        from sphere_e2e_test_framework.pages.e_admin.ckc_page import CustomerKeyCeremonyPage

        ckc = ctx.get("_ckc_page") or CustomerKeyCeremonyPage(ctx.driver, ctx.evidence)
        ckc.select_generate_and_export(
            step_name="And: User selects GENERATE_AND_EXPORT mode",
        )

    return Step("Select GENERATE_AND_EXPORT", _action)


def ckc_configure_key():
    """Configure key parameters from test data."""

    def _action(ctx):
        from sphere_e2e_test_framework.pages.e_admin.ckc_page import CustomerKeyCeremonyPage

        ckc = ctx.get("_ckc_page") or CustomerKeyCeremonyPage(ctx.driver, ctx.evidence)
        ckc.configure_key(
            key_label=ctx.td.key_label,
            key_algo=ctx.td.key_algo,
            key_length=ctx.td.key_length,
            key_usage=ctx.td.key_usage,
            cps_key_type=ctx.td.cps_key_type,
            step_name="And: User configures key parameters",
        )

    return Step("Configure key", _action)


def ckc_generate_key():
    """Generate the key and dismiss confirmation."""

    def _action(ctx):
        from sphere_e2e_test_framework.pages.e_admin.ckc_page import CustomerKeyCeremonyPage

        ckc = ctx.get("_ckc_page") or CustomerKeyCeremonyPage(ctx.driver, ctx.evidence)
        ckc.generate_key(
            step_name="And: User generates the key",
        )

    return Step("Generate key", _action)


def ckc_export_all_custodian_keys():
    """Loop through each custodian: accept understanding, login, read export values, continue.

    For the last custodian, also reads the combined key KCV.
    All export values are stored in ``ctx.state['ckc_export_values']``.
    """

    def _action(ctx):
        from sphere_e2e_test_framework.pages.e_admin.ckc_page import CustomerKeyCeremonyPage

        ckc = ctx.get("_ckc_page") or CustomerKeyCeremonyPage(ctx.driver, ctx.evidence)
        all_exports = []

        for i, kcp in enumerate(ctx.td.custodian_parties, start=1):
            is_last = (i == len(ctx.td.custodian_parties))

            # Accept understanding
            ckc.accept_understanding(
                step_name=f"And: Accept understanding before KCP{i} export",
            )

            # Login as custodian
            ckc.login_custodian(
                kcp.username, kcp.password,
                step_name=f"And: Key Custodian Party {i} ({kcp.username}) logs in",
            )

            # Read export values
            values = ckc.read_export_values(
                is_last=is_last,
                step_name=f"Then: Read export values for KCP{i} ({kcp.username})",
            )
            values["username"] = kcp.username
            all_exports.append(values)
            logger.info(f"KCP{i} export: {values}")

            # Continue (except after last — will go to summary)
            if not is_last:
                ckc.continue_export(
                    step_name=f"And: Continue after KCP{i} export",
                )

        ctx.set("ckc_export_values", all_exports)
        logger.info(f"All {len(all_exports)} custodian exports completed")

    return Step("Export all custodian keys", _action)


def ckc_verify_key_summary():
    """Read and verify the key summary screen. Stores result in ctx.state['ckc_key_summary']."""

    def _action(ctx):
        from sphere_e2e_test_framework.pages.e_admin.ckc_page import CustomerKeyCeremonyPage

        ckc = ctx.get("_ckc_page") or CustomerKeyCeremonyPage(ctx.driver, ctx.evidence)
        summary = ckc.get_key_summary(
            step_name="Then: Verify Customer Key Info summary",
        )
        ctx.set("ckc_key_summary", summary)
        logger.info(f"Key summary verified: {summary}")

    return Step("Verify key summary", _action)


def ckc_finish():
    """Click Continue to complete the CKC flow."""

    def _action(ctx):
        from sphere_e2e_test_framework.pages.e_admin.ckc_page import CustomerKeyCeremonyPage

        ckc = ctx.get("_ckc_page") or CustomerKeyCeremonyPage(ctx.driver, ctx.evidence)
        ckc.finish(
            step_name="Then: Customer Key Ceremony completed successfully",
        )

    return Step("Finish CKC", _action)
