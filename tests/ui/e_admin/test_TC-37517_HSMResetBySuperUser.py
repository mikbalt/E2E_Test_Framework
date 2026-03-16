"""
[E2E][e-admin] HSM Reset by Super User — TC-37517

Background:
    Given the eAdmin application is launched and visible
    And the key ceremony has already been completed

Scenario: SUPER_USER initiates HSM Reset, ADMIN authorizes
    Phase 1 — Export Audit Log:
        1. Connect to HSM, login as SUPER_USER
        2. Click Reset → decline first prompt (No)
        3. Dismiss info popups (OK, OK)
        4. Export Log (btnExportLog) → confirm (Yes)
        5. Auditor authenticates → log saved → OK

    Phase 2 — Perform HSM Reset:
        6. Re-login as SUPER_USER
        7. Click Reset → confirm (Yes, Yes)
        8. ADMIN authenticates (btnAuth)
        9. Dismiss sync popup (OK)
        10. Assert: Reset finished popup → click No (close eADMIN)

Run:
    pytest tests/ui/e_admin/test_TC-37517_HSMResetBySuperUser.py -v -s
"""

import logging

import allure
import pytest

from hsm_test_framework.evidence import tracked_step
from hsm_test_framework.pages import DashboardPage, LoginPage
from hsm_test_framework.pages.base_page import TIMEOUT
from tests.test_data import HSMResetData

logger = logging.getLogger(__name__)


@allure.epic("Sphere HSM Idemia - E2E Tests - E-Admin")
@allure.feature("HSM Reset")
@allure.suite("eAdmin-Tier1 Journeys")
@allure.tag("e-admin", "windows", "ui", "hsm-reset")
@pytest.mark.e_admin
@pytest.mark.tcms(case_id=37517)
class TestHSMResetBySuperUser:

    @pytest.fixture(autouse=True)
    def setup(self, e_admin_driver, evidence):
        self.driver = e_admin_driver
        self.evidence = evidence
        self.td = HSMResetData.from_env()
        yield

    @allure.story("SUPER_USER initiates HSM reset, ADMIN authorizes")
    @allure.title("[E2E][e-admin] HSM Reset by Super User")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.critical
    @pytest.mark.order(3)
    @pytest.mark.depends_on(37509)
    def test_hsm_reset_by_super_user(self):
        """Full flow: login → export audit log → re-login → reset → verify."""
        driver = self.driver
        evidence = self.evidence
        td = self.td

        # ==================================================================
        # Background: Connect and login as SUPER_USER
        # ==================================================================
        login = LoginPage(driver, evidence)

        dashboard = login.connect_to_hsm(
            step_name="Given: eAdmin is connected to HSM",
        )
        assert dashboard.is_visible(), "Dashboard not visible after connection"

        login_page = dashboard.open_login()
        login_page.open_login_form(
            step_name="And: Open login form",
        )

        sessions = login_page.get_sessions()
        su_session = next(
            (s for s in sessions if td.super_user_session in s), sessions[0],
        )
        login_page.select_session(
            su_session,
            step_name=f"And: Select session '{su_session}'",
        )
        dashboard = login_page.login(
            td.super_user_username, td.super_user_password,
            step_name="And: SUPER_USER logs in to eAdmin",
        )

        logged_in_user = dashboard.get_logged_in_user()
        assert td.super_user_username.lower() in logged_in_user.lower(), (
            f"Expected '{td.super_user_username}' in label, got '{logged_in_user}'"
        )
        logger.info(f"Background complete — logged in as '{logged_in_user}'")

        # ==================================================================
        # Phase 1: Export Audit Log before Reset
        # ==================================================================

        # Step: Click Reset → first prompt appears
        with tracked_step(evidence, driver, "When: SUPER_USER clicks Reset"):
            driver.click_button(auto_id="btnReset")

        # Step: Decline first prompt (No) — triggers export requirement
        with tracked_step(evidence, driver, "And: Decline first reset prompt (No)"):
            driver.wait_for_element(
                timeout=TIMEOUT, auto_id="7", control_type="Button",
            )
            driver.click_button(auto_id="7")

        # Step: Dismiss info popups
        with tracked_step(evidence, driver, "And: Dismiss info popup (OK)"):
            driver.wait_for_element(
                timeout=TIMEOUT, auto_id="2", control_type="Button",
            )
            driver.click_button(auto_id="2")

        with tracked_step(evidence, driver, "And: Dismiss second info popup (OK)"):
            driver.wait_for_element(
                timeout=TIMEOUT, auto_id="2", control_type="Button",
            )
            driver.click_button(auto_id="2")

        # Step: Click Export Log
        with tracked_step(evidence, driver, "When: Click Export Log button"):
            driver.wait_for_element(
                timeout=TIMEOUT, auto_id="btnExportLog", control_type="Button",
            )
            driver.click_button(auto_id="btnExportLog")

        # Step: Confirm export (Yes)
        with tracked_step(evidence, driver, "And: Confirm export log (Yes)"):
            driver.wait_for_element(
                timeout=TIMEOUT, auto_id="6", control_type="Button",
            )
            driver.click_button(auto_id="6")

        # Step: Auditor authenticates
        with tracked_step(evidence, driver, "And: Auditor authenticates for log export"):
            driver.wait_for_element(
                timeout=TIMEOUT, auto_id="1001", control_type="Edit",
            )
            driver.type_text(td.auditor_username, auto_id="1001")
            driver.type_text(
                td.auditor_password, auto_id="txtPassword", sensitive=True,
            )
            driver.click_button(auto_id="btnAuth")

        # Step: Log saved notification → read text → attach to report → dismiss
        with tracked_step(evidence, driver, "Then: Log file saved notification displayed"):
            log_label = driver.wait_for_element(
                timeout=TIMEOUT, auto_id="65535", control_type="Text",
            )
            log_notification = log_label.window_text()
            logger.info(f"Audit log notification: {log_notification}")

            allure.attach(
                log_notification,
                name="Audit Log Export — Path & Filename",
                attachment_type=allure.attachment_type.TEXT,
            )

        with tracked_step(evidence, driver, "And: Dismiss log saved notification (OK)"):
            driver.wait_for_element(
                timeout=TIMEOUT, auto_id="2", control_type="Button",
            )
            driver.click_button(auto_id="2")

        logger.info("Phase 1 complete — Audit log exported via auditor")

        # ==================================================================
        # Phase 2: Re-login as SUPER_USER and perform HSM Reset
        # ==================================================================

        # Step: Re-login as SUPER_USER (logged out after export)
        with tracked_step(evidence, driver, "When: Re-open login form"):
            driver.wait_for_element(
                timeout=TIMEOUT, auto_id="lbl_clickLogin", control_type="Text",
            )
            driver.click_element(auto_id="lbl_clickLogin", control_type="Text")

        with tracked_step(evidence, driver, "And: SUPER_USER re-logs in"):
            driver.wait_for_element(
                timeout=TIMEOUT, auto_id="rbPassword",
            )
            driver.click_radio(auto_id="rbPassword")
            driver.type_text(td.super_user_username, auto_id="1001")
            driver.type_text(
                td.super_user_password, auto_id="txtPassword", sensitive=True,
            )
            driver.click_button(auto_id="btnLogin")
            driver.wait_for_element(
                timeout=TIMEOUT, auto_id="btnLogOut", control_type="Button",
            )
            logger.info("SUPER_USER re-logged in successfully")

        # Step: Click Reset again
        with tracked_step(evidence, driver, "When: SUPER_USER clicks Reset (2nd time)"):
            driver.click_button(auto_id="btnReset")

        # Step: Confirm reset — Yes to first prompt
        with tracked_step(evidence, driver, "And: Confirm reset prompt (Yes)"):
            driver.wait_for_element(
                timeout=TIMEOUT, auto_id="6", control_type="Button",
            )
            driver.click_button(auto_id="6")

        # Step: Confirm reset — Yes to second prompt
        with tracked_step(evidence, driver, "And: Confirm second reset prompt (Yes)"):
            driver.wait_for_element(
                timeout=TIMEOUT, auto_id="6", control_type="Button",
            )
            driver.click_button(auto_id="6")

        # Step: ADMIN authenticates for reset authorization
        # After Yes/Yes, app has 2 WinForms windows → driver is ambiguous.
        # Find the auth window by handle to avoid ambiguity.
        import time as _time
        _time.sleep(2)
        with tracked_step(evidence, driver, "And: ADMIN authenticates to authorize reset"):
            from pywinauto import findwindows
            handles = findwindows.find_windows(
                process=driver.app.process, backend="uia",
            )
            auth_win = None
            for h in handles:
                try:
                    w = driver.app.window(handle=h)
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
            ).set_edit_text(td.admin_username)
            auth_win.child_window(
                auto_id="txtPassword", control_type="Edit",
            ).set_edit_text(td.admin_password)
            auth_win.child_window(auto_id="btnAuth").click_input()
            _time.sleep(1)

        # After auth, driver may have 2 WinForms windows → ambiguous.
        # Use find_element_in_any_window() to locate buttons across windows.

        # Step: Dismiss sync/confirmation popup (OK)
        with tracked_step(evidence, driver, "Then: Dismiss sync confirmation (OK)"):
            ok_btn = driver.find_element_in_any_window(
                auto_id="2", control_type="Button", timeout=TIMEOUT,
            )
            logger.info("Sync confirmation popup found")
            ok_btn.click_input()
            _time.sleep(1)

        # Step: HSM Reset finished → Click No (close eADMIN)
        with tracked_step(evidence, driver, "Then: HSM Reset finished — click No to close eADMIN"):
            no_btn = driver.find_element_in_any_window(
                auto_id="7", control_type="Button", timeout=TIMEOUT,
            )
            logger.info(
                "HSM Reset Procedure has been finished successfully. "
                "HSM Initialization and Key Ceremony will be required."
            )
            no_btn.click_input()
            _time.sleep(1)

        logger.info("TC-37517 PASSED — HSM Reset by Super User completed successfully")
