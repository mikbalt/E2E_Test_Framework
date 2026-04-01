"""
E-Admin HSM reset step factories.

Each function returns a Step that internally uses page objects.
Steps communicate via ``ctx.state`` / ``ctx.page``.
"""

import logging
import time

from sphere_e2e_test_framework.flows.base import Step

logger = logging.getLogger(__name__)

# WinForms MessageBox button auto_id constants
YES_BUTTON = "6"
NO_BUTTON = "7"
OK_BUTTON = "2"


def _snap(ctx, label):
    """Mid-step screenshot — capture transient UI before it disappears."""
    if ctx.evidence:
        ctx.evidence.screenshot(
            ctx.driver, f"step_{ctx.evidence.step_count:03d}_{label}",
        )


def click_reset_and_decline():
    """Click btnReset → decline first prompt (No) → dismiss 2x info popups (OK)."""

    def _action(ctx):
        from sphere_e2e_test_framework.driver.evidence import tracked_step
        from sphere_e2e_test_framework.pages.base_page import TIMEOUT

        with tracked_step(ctx.evidence, ctx.driver, "When: SUPER_USER clicks Reset"):
            ctx.driver.click_button(auto_id="btnReset")

        with tracked_step(ctx.evidence, ctx.driver, "And: Decline first reset prompt (No)"):
            ctx.driver.wait_for_element(
                timeout=TIMEOUT, auto_id=NO_BUTTON, control_type="Button",
            )
            _snap(ctx, "reset_decline_prompt")
            ctx.driver.click_button(auto_id=NO_BUTTON)

        for label in ("And: Dismiss info popup (OK)", "And: Dismiss second info popup (OK)"):
            with tracked_step(ctx.evidence, ctx.driver, label):
                ctx.driver.wait_for_element(
                    timeout=TIMEOUT, auto_id=OK_BUTTON, control_type="Button",
                )
                _snap(ctx, "info_popup")
                ctx.driver.click_button(auto_id=OK_BUTTON)

    return Step("Click Reset and decline", _action)


def export_audit_log(
    auditor_user_attr="auditor_username",
    auditor_pass_attr="auditor_password",
):
    """Export audit log: click Export → Yes → auditor auth → read notification → dismiss."""

    def _action(ctx):
        import allure
        from sphere_e2e_test_framework.driver.evidence import tracked_step
        from sphere_e2e_test_framework.pages.base_page import TIMEOUT

        auditor_user = getattr(ctx.td, auditor_user_attr)
        auditor_pass = getattr(ctx.td, auditor_pass_attr)

        with tracked_step(ctx.evidence, ctx.driver, "When: Click Export Log button"):
            ctx.driver.wait_for_element(
                timeout=TIMEOUT, auto_id="btnExportLog", control_type="Button",
            )
            ctx.driver.click_button(auto_id="btnExportLog")

        with tracked_step(ctx.evidence, ctx.driver, "And: Confirm export log (Yes)"):
            ctx.driver.wait_for_element(
                timeout=TIMEOUT, auto_id=YES_BUTTON, control_type="Button",
            )
            _snap(ctx, "export_log_confirm")
            ctx.driver.click_button(auto_id=YES_BUTTON)

        with tracked_step(ctx.evidence, ctx.driver, "And: Auditor authenticates for log export"):
            ctx.driver.wait_for_element(
                timeout=TIMEOUT, auto_id="1001", control_type="Edit",
            )
            ctx.driver.type_text(auditor_user, auto_id="1001")
            ctx.driver.type_text(
                auditor_pass, auto_id="txtPassword", sensitive=True,
            )
            _snap(ctx, "auditor_auth_form")
            ctx.driver.click_button(auto_id="btnAuth")

        with tracked_step(ctx.evidence, ctx.driver, "Then: Log file saved notification displayed"):
            log_label = ctx.driver.wait_for_element(
                timeout=TIMEOUT, auto_id="65535", control_type="Text",
            )
            log_notification = log_label.window_text()
            logger.info(f"Audit log notification: {log_notification}")
            allure.attach(
                log_notification,
                name="Audit Log Export — Path & Filename",
                attachment_type=allure.attachment_type.TEXT,
            )

        with tracked_step(ctx.evidence, ctx.driver, "And: Dismiss log saved notification (OK)"):
            ctx.driver.wait_for_element(
                timeout=TIMEOUT, auto_id=OK_BUTTON, control_type="Button",
            )
            _snap(ctx, "log_saved_notification")
            ctx.driver.click_button(auto_id=OK_BUTTON)

        logger.info("Audit log exported via auditor")

    return Step("Export audit log", _action)


def relogin_super_user(
    username_attr="super_user_username",
    password_attr="super_user_password",
):
    """Re-login as SUPER_USER via raw driver (post-export UI state)."""

    def _action(ctx):
        from sphere_e2e_test_framework.driver.evidence import tracked_step
        from sphere_e2e_test_framework.pages.base_page import TIMEOUT

        username = getattr(ctx.td, username_attr)
        password = getattr(ctx.td, password_attr)

        with tracked_step(ctx.evidence, ctx.driver, "When: Re-open login form"):
            ctx.driver.wait_for_element(
                timeout=TIMEOUT, auto_id="lbl_clickLogin", control_type="Text",
            )
            ctx.driver.click_element(auto_id="lbl_clickLogin", control_type="Text")

        with tracked_step(ctx.evidence, ctx.driver, "And: SUPER_USER re-logs in"):
            ctx.driver.wait_for_element(
                timeout=TIMEOUT, auto_id="rbPassword",
            )
            ctx.driver.click_radio(auto_id="rbPassword")
            ctx.driver.type_text(username, auto_id="1001")
            ctx.driver.type_text(
                password, auto_id="txtPassword", sensitive=True,
            )
            ctx.driver.click_button(auto_id="btnLogin")
            ctx.driver.wait_for_element(
                timeout=TIMEOUT, auto_id="btnLogOut", control_type="Button",
            )
            logger.info("SUPER_USER re-logged in successfully")

    return Step("Re-login as SUPER_USER", _action)


def confirm_reset_with_admin_auth(
    admin_user_attr="admin_username",
    admin_pass_attr="admin_password",
):
    """Click Reset → Yes x2 → multi-window ADMIN auth via findwindows."""

    def _action(ctx):
        from sphere_e2e_test_framework.driver.evidence import tracked_step
        from sphere_e2e_test_framework.pages.base_page import TIMEOUT

        admin_user = getattr(ctx.td, admin_user_attr)
        admin_pass = getattr(ctx.td, admin_pass_attr)

        with tracked_step(ctx.evidence, ctx.driver, "When: SUPER_USER clicks Reset (2nd time)"):
            ctx.driver.click_button(auto_id="btnReset")

        with tracked_step(ctx.evidence, ctx.driver, "And: Confirm reset prompt (Yes)"):
            ctx.driver.wait_for_element(
                timeout=TIMEOUT, auto_id=YES_BUTTON, control_type="Button",
            )
            _snap(ctx, "reset_confirm_1")
            ctx.driver.click_button(auto_id=YES_BUTTON)

        with tracked_step(ctx.evidence, ctx.driver, "And: Confirm second reset prompt (Yes)"):
            ctx.driver.wait_for_element(
                timeout=TIMEOUT, auto_id=YES_BUTTON, control_type="Button",
            )
            _snap(ctx, "reset_confirm_2")
            ctx.driver.click_button(auto_id=YES_BUTTON)

        time.sleep(2)
        with tracked_step(ctx.evidence, ctx.driver, "And: ADMIN authenticates to authorize reset"):
            from pywinauto import findwindows

            handles = findwindows.find_windows(
                process=ctx.driver.app.process, backend="uia",
            )
            auth_win = None
            for h in handles:
                try:
                    w = ctx.driver.app.window(handle=h)
                    if w.child_window(auto_id="panel1").exists(timeout=1):
                        auth_win = w
                        break
                except Exception:
                    continue
            assert auth_win is not None, (
                f"Auth dialog (panel1) not found in {len(handles)} window(s)"
            )
            logger.info(f"Auth window found: handle={auth_win.handle}")

            auth_win.child_window(
                auto_id="1001", control_type="Edit",
            ).wait("visible", timeout=TIMEOUT)
            auth_win.child_window(
                auto_id="1001", control_type="Edit",
            ).set_edit_text(admin_user)
            auth_win.child_window(
                auto_id="txtPassword", control_type="Edit",
            ).set_edit_text(admin_pass)
            _snap(ctx, "admin_auth_form")
            auth_win.child_window(auto_id="btnAuth").click_input()
            time.sleep(1)

    return Step("Confirm reset with ADMIN auth", _action)


def dismiss_reset_completion():
    """Dismiss sync confirmation (OK) + reset finished (No) via find_element_in_any_window."""

    def _action(ctx):
        from sphere_e2e_test_framework.driver.evidence import tracked_step
        from sphere_e2e_test_framework.pages.base_page import TIMEOUT

        with tracked_step(ctx.evidence, ctx.driver, "Then: Dismiss sync confirmation (OK)"):
            ok_btn = ctx.driver.find_element_in_any_window(
                auto_id=OK_BUTTON, control_type="Button", timeout=TIMEOUT,
            )
            logger.info("Sync confirmation popup found")
            _snap(ctx, "sync_confirmation")
            ok_btn.click_input()
            time.sleep(1)

        with tracked_step(ctx.evidence, ctx.driver, "Then: HSM Reset finished — click No to close eADMIN"):
            no_btn = ctx.driver.find_element_in_any_window(
                auto_id=NO_BUTTON, control_type="Button", timeout=TIMEOUT,
            )
            _snap(ctx, "reset_finished")
            logger.info(
                "HSM Reset Procedure has been finished successfully. "
                "HSM Initialization and Key Ceremony will be required."
            )
            no_btn.click_input()
            time.sleep(1)

        logger.info("HSM Reset completed successfully")

    return Step("Dismiss reset completion", _action)
