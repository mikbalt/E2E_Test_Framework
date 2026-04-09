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
    """Click Next after custodian creation → wait for HSM sync → mode selection.

    After clicking Next the HSM syncs (can take minutes).
    We poll until ``btnAdd1`` disappears (custodian page gone),
    confirming the page has transitioned to mode selection.
    """

    def _action(ctx):
        import time

        ctx.driver.click_button(auto_id="btnNext")
        logger.info("Next clicked — waiting for HSM sync...")

        # Poll until custodian creation page is gone (btnAdd1 only exists there)
        for i in range(60):
            time.sleep(5)
            ctx.driver.refresh_window()
            if not ctx.driver.element_exists(auto_id="btnAdd1"):
                logger.info(f"Page transitioned after ~{(i + 1) * 5}s")
                break
        else:
            raise RuntimeError("Custodian creation page did not transition after 5 minutes")

        logger.info("Operation mode selection screen ready")

    return Step("Proceed to next phase", _action)


def ckc_select_generate_and_export():
    """Select GENERATE_AND_EXPORT mode and proceed."""

    def _action(ctx):
        import time

        from sphere_e2e_test_framework.pages.e_admin.ckc_page import CustomerKeyCeremonyPage

        time.sleep(5)
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
            key_usages=ctx.td.key_usages,
            cps_key_type=ctx.td.cps_key_type,
            key_type=getattr(ctx.td, "key_type", None),
            kcv_algo=getattr(ctx.td, "kcv_algo", None),
            valid_date=getattr(ctx.td, "valid_date", None),
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


def ckc_save_export_results(output_dir="output"):
    """Save CKC export values and key summary to a JSON file.

    Reads from ctx.state['ckc_export_values'] and ctx.state['ckc_key_summary'].
    Writes to ``<output_dir>/ckc_export.json``.
    """

    def _action(ctx):
        import json
        import re
        from pathlib import Path

        def _strip_spaces(obj):
            """Recursively remove all spaces from string values."""
            if isinstance(obj, str):
                return re.sub(r"\s+", "", obj)
            if isinstance(obj, dict):
                return {k: _strip_spaces(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [_strip_spaces(item) for item in obj]
            return obj

        exports_list = ctx.get("ckc_export_values", [])
        summary = ctx.get("ckc_key_summary", {})

        # Group exports by username as key (without mutating original)
        exports = {}
        for i, entry in enumerate(exports_list, start=1):
            username = entry.get("username", f"kcp{i}")
            exports[username] = {k: v for k, v in entry.items() if k != "username"}

        data = _strip_spaces({
            "exports": exports,
            "key_summary": summary,
        })

        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        file_path = out_path / "ckc_export.json"

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"CKC export results saved to {file_path.resolve()}")

    return Step("Save CKC export results", _action)
