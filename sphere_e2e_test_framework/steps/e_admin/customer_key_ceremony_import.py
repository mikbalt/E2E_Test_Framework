"""
E-Admin Customer Key Ceremony Import step factories.

Each function returns a Step that internally uses the CustomerKeyCeremonyPage.
Steps communicate via ``ctx.state`` / ``ctx.page``.

Precondition: CKC Generate & Export must be completed first.
"""

import logging

from sphere_e2e_test_framework.flows.base import Step

logger = logging.getLogger(__name__)


def ckc_dismiss_reuse_kcps():
    """Click 'No' to reuse existing Key Custodian Parties."""

    def _action(ctx):
        from sphere_e2e_test_framework.pages.e_admin.ckc_page import CustomerKeyCeremonyPage

        ckc = ctx.get("_ckc_page") or CustomerKeyCeremonyPage(ctx.driver, ctx.evidence)
        ckc.dismiss_reuse_kcps(
            step_name="And: Reuse existing Key Custodian Parties",
        )

    return Step("Reuse existing KCPs", _action)


def ckc_select_import_mode():
    """Select IMPORT mode and proceed."""

    def _action(ctx):
        from sphere_e2e_test_framework.pages.e_admin.ckc_page import CustomerKeyCeremonyPage

        ckc = ctx.get("_ckc_page") or CustomerKeyCeremonyPage(ctx.driver, ctx.evidence)
        ckc.select_import_mode(
            step_name="And: User selects IMPORT mode",
        )

    return Step("Select IMPORT mode", _action)


def ckc_import_all_components():
    """Loop through each KCP: accept understanding, login, import component, process.

    For the first KCP, uses combobox for username selection and selects key attributes.
    For the last KCP, enters full key configuration (customer key KCV, key config, MAC).
    All other KCPs do basic import (secret + KCV).
    """

    def _action(ctx):
        from sphere_e2e_test_framework.pages.e_admin.ckc_page import CustomerKeyCeremonyPage

        ckc = ctx.get("_ckc_page") or CustomerKeyCeremonyPage(ctx.driver, ctx.evidence)
        total = len(ctx.td.custodian_parties)

        for i, kcp in enumerate(ctx.td.custodian_parties, start=1):
            is_first = (i == 1)
            is_last = (i == total)

            # Accept understanding
            ckc.accept_understanding(
                step_name=f"And: Accept understanding before KCP{i} import",
            )

            # Login as custodian
            ckc.login_custodian_import(
                kcp.username, kcp.password,
                use_combobox=is_first,
                step_name=f"And: Key Custodian Party {i} ({kcp.username}) logs in",
            )

            if is_last:
                # Last KCP: full import with key configuration
                ckc.import_final_component(
                    secret=kcp.secret,
                    kcv=kcp.kcv,
                    customer_key_kcv=ctx.td.customer_key_kcv,
                    key_label=ctx.td.key_label,
                    key_algo=ctx.td.key_algo,
                    key_length=ctx.td.key_length,
                    key_usage=ctx.td.key_usage,
                    cps_key_type=ctx.td.cps_key_type,
                    key_mac=ctx.td.key_mac,
                    step_name=f"And: KCP{i} ({kcp.username}) imports final component with key config",
                )
                ckc.finalize_import(
                    step_name=f"Then: CKC Import finalized by KCP{i} ({kcp.username})",
                )
            else:
                # Non-last KCP: basic import
                ckc.import_component(
                    secret=kcp.secret,
                    kcv=kcp.kcv,
                    step_name=f"And: KCP{i} ({kcp.username}) imports component",
                )

                # First KCP: select key attributes if defined
                if is_first and kcp.key_attributes:
                    ckc.select_key_attributes(
                        kcp.key_attributes,
                        step_name=f"And: KCP{i} selects key attributes",
                    )

                ckc.process_import(
                    step_name=f"And: KCP{i} ({kcp.username}) import processed",
                )

            logger.info(f"KCP{i} ({kcp.username}) import completed")

        logger.info(f"All {total} custodian imports completed")

    return Step("Import all CKC components", _action)
