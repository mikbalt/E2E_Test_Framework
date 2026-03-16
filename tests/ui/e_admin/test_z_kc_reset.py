"""
[E2E][e-admin][Key Ceremony] Key ceremony after HSM Reset (password already set)

Same as KeyCeremonyFIPS but SUPER_USER password change is skipped because
the password was already set before the reset.

Scenario:
    Given  eAdmin launched and connected to HSM
    When   user starts HSM Initialization
    And    accepts T&C
    And    SUPER_USER authenticates and creates Admin
    And    Admin logs in and creates 3 Key Custodians + 1 Auditor
    And    each Key Custodian imports their CCMK component
    And    user selects FIPS mode and finalizes
    Then   Key Ceremony completed successfully

Run:
    pytest tests/ui/e_admin/test_KeyCeremonyPostReset.py -v -s
"""
import logging
import time

import allure
import pytest

from hsm_test_framework import tracked_step
from tests.test_data import KeyCeremonyData

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Timeout — single place to tune all wait_for_element timeouts (seconds)
# ---------------------------------------------------------------------------
TIMEOUT = 120


# ---------------------------------------------------------------------------
# Reusable UI helpers (scoped to this module)
# ---------------------------------------------------------------------------

def _agree_and_next(driver):
    """Click 'Agree' radio then 'Next >>>' button.

    Uses click_element with found_index=0 because post-reset UI
    has duplicate rbAgree elements (WinForms panel quirk).
    """
    driver.click_radio(auto_id="rbAgree", found_index=0)
    driver.wait_for_element(timeout=TIMEOUT, auto_id="btnNext", control_type="Button")
    driver.click_button(auto_id="btnNext")


def _dismiss_ok(driver):
    """Dismiss a dialog by clicking OK (auto_id='2')."""
    driver.wait_for_element(timeout=TIMEOUT, auto_id="2", control_type="Button")
    driver.click_button(auto_id="2")


def _create_user(driver, username, password, add_button_id=None):
    """Fill the create-user form (username, Password radio, pass, repeat, Create).

    If add_button_id is provided, click it first to open the form.
    """
    if add_button_id:
        driver.click_button(auto_id=add_button_id)
        driver.wait_for_element(timeout=TIMEOUT, auto_id="txtUsername")

    driver.type_text(username, auto_id="txtUsername")
    driver.click_radio(auto_id="rbPass")
    driver.type_text(password, auto_id="txtPass", sensitive=True)
    driver.type_text(password, auto_id="txtPassRepeat", sensitive=True)
    driver.click_button(auto_id="btnCreate")
    _dismiss_ok(driver)


def _kc_login(driver, username, password):
    """Login as Key Custodian via Password authentication."""
    driver.refresh_window()
    driver.wait_for_element(timeout=TIMEOUT, auto_id="rbPassword")
    driver.click_radio(auto_id="rbPassword")
    driver.type_text(username, auto_id="1001")
    driver.type_text(password, auto_id="txtPassword", sensitive=True)
    driver.click_button(auto_id="btnLogin")


# ---------------------------------------------------------------------------
# Test class
# ---------------------------------------------------------------------------

@allure.epic("Sphere HSM Idemia - E2E Tests - E-Admin")
@allure.feature("Key Ceremony")
@allure.suite("eAdmin-Tier1 Journeys")
@allure.tag("e-admin", "windows", "ui", "key-ceremony", "post-reset")
@pytest.mark.e_admin
class TestKeyCeremonyPostReset:

    @pytest.fixture(autouse=True)
    def setup(self, e_admin_driver, evidence):
        """Wire shared fixtures into test instance attributes."""
        self.driver = e_admin_driver
        self.evidence = evidence
        self.td = KeyCeremonyData.from_env()
        yield

    @allure.story("User performs key ceremony after HSM reset (no password change)")
    @allure.title("[E2E][e-admin][Key Ceremony] Key ceremony post-reset")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.description(
        """
        Scenario: Perform Key Ceremony after HSM Reset — SUPER_USER password already set

        Given eAdmin application is launched and visible
        And eAdmin is connected to HSM successfully

        When user starts HSM Initialization
        And user accepts Sphere HSM Terms & Conditions

        When user accepts Admin Creation Terms & Conditions
        And SUPER_USER authenticates with existing credentials
        And SUPER_USER creates Admin account
        Then Admin account created successfully

        When user accepts Custodians Creation Terms & Conditions
        And Admin logs in with credentials
        And Admin accepts post-login Terms & Conditions
        And Admin creates Key Custodian 1, 2, 3 accounts
        And Admin creates Auditor account
        Then all user accounts created successfully

        When user accepts CCMK Import Terms & Conditions (3 pages)
        And Key Custodian 1, 2, 3 each log in and import CCMK component
        Then CCMK imported successfully for all 3 quorum members

        When user selects FIPS mode of operation and finalizes
        Then Key Ceremony completed successfully
        """
    )
    @pytest.mark.critical
    def test_key_ceremony_post_reset(self):
        """Key ceremony after reset: connect, init, create users, CCMK, finalize.

        Skips SUPER_USER password change (already set before reset).
        """
        driver = self.driver
        evidence = self.evidence

        # ==================================================================
        # Phase 1: Connect to HSM
        # ==================================================================
        with tracked_step(evidence, driver, "Given: eAdmin application is launched and visible"):
            assert driver.main_window.is_visible(), (
                "E-Admin main window is not visible after launch"
            )
            logger.info("E-Admin launched successfully")

        with tracked_step(evidence, driver, "Given: eAdmin is connected to HSM successfully"):
            driver.click_button(auto_id="btnUpdate")
            logger.info("Connect button clicked")

            driver.wait_for_element(
                timeout=TIMEOUT, auto_id="btnOKE", control_type="Button"
            )

            popup = driver.check_popup()
            if popup:
                logger.info(f"Popup detected: '{popup.window_text()}'")
                allure.attach(
                    popup.window_text(),
                    name="popup_text",
                    attachment_type=allure.attachment_type.TEXT,
                )

            evidence.screenshot(driver, "connect_popup_visible")

            driver.click_button(auto_id="btnOKE")
            logger.info("OK button clicked")

        driver.refresh_window()

        with tracked_step(evidence, driver, "Then: HSM connection confirmed"):
            assert driver.main_window.is_visible(), (
                "E-Admin window not visible after connection"
            )
            logger.info("Dashboard loaded - control tree captured")

        # ==================================================================
        # Phase 2: Start HSM Initialization
        # ==================================================================
        with tracked_step(evidence, driver, "When: User starts HSM Initialization"):
            driver.click_button(auto_id="btnHSMInit")
            logger.info("HSM Initialization started")

        driver.refresh_window()

        # ==================================================================
        # Phase 3: Accept T&C — Admin Creation
        # (Post-reset: only 1 T&C page before SUPER_USER auth)
        # ==================================================================
        with tracked_step(evidence, driver, "When: User accepts Admin Creation Terms & Conditions"):
            driver.wait_for_element(timeout=TIMEOUT, auto_id="btnNext", control_type="Button")
            _agree_and_next(driver)
            logger.info("Admin Creation T&C accepted")

        # ==================================================================
        # Phase 5: Authenticate as SUPER_USER (existing password)
        # ==================================================================
        with tracked_step(evidence, driver, "And: SUPER_USER authenticates with existing credentials"):
            _dismiss_ok(driver)
            driver.type_text(self.td.new_super_user_pass, auto_id="txtPassword", sensitive=True)
            driver.click_button(auto_id="btnAuth")
            driver.wait_for_element(timeout=TIMEOUT, auto_id="txtUsername")
            logger.info("SUPER_USER authenticated")

        # ==================================================================
        # Phase 6: Create Admin account
        # ==================================================================
        with tracked_step(evidence, driver, "And: SUPER_USER creates Admin account"):
            _create_user(driver, self.td.admin_username, self.td.admin_password)
            logger.info(f"Admin account '{self.td.admin_username}' created")

        with tracked_step(evidence, driver, "Then: Admin account created successfully"):
            _dismiss_ok(driver)
            time.sleep(10)
            driver.refresh_window()
            driver.wait_for_element(timeout=TIMEOUT, auto_id="btnNext", control_type="Button")
            _agree_and_next(driver)
            logger.info("Admin creation confirmed")

        # ==================================================================
        # Phase 7: Accept T&C — Custodians Creation
        # ==================================================================
        with tracked_step(evidence, driver, "When: User accepts Custodians Creation Terms & Conditions"):
            time.sleep(10)
            driver.refresh_window()
            driver.wait_for_element(timeout=TIMEOUT, auto_id="btnNext", control_type="Button")
            _agree_and_next(driver)
            logger.info("Custodians Creation T&C accepted")

        # ==================================================================
        # Phase 8: Login as Admin
        # ==================================================================
        with tracked_step(evidence, driver, "And: Admin logs in with credentials"):
            _kc_login(driver, self.td.admin_username, self.td.admin_password)
            driver.refresh_window()
            driver.wait_for_element(timeout=TIMEOUT, auto_id="btnNext", control_type="Button")
            logger.info(f"Logged in as '{self.td.admin_username}'")

        # ==================================================================
        # Phase 9: Accept T&C and confirm after Admin login
        # ==================================================================
        with tracked_step(evidence, driver, "And: Admin accepts post-login Terms & Conditions"):
            driver.click_radio(auto_id="rbAgree", found_index=0)
            _dismiss_ok(driver)
            logger.info("Admin post-login confirmation accepted")

        # ==================================================================
        # Phase 10: Create Key Custodians (KC1, KC2, KC3)
        # ==================================================================
        for i, kc in enumerate(self.td.key_custodians, start=1):
            with tracked_step(evidence, driver, f"And: Admin creates Key Custodian {i} ({kc.username}) account"):
                _create_user(
                    driver,
                    username=kc.username,
                    password=kc.password,
                    add_button_id=kc.add_button,
                )
                logger.info(f"Key Custodian {i} '{kc.username}' created")

        # ==================================================================
        # Phase 11: Create Auditor
        # ==================================================================
        with tracked_step(evidence, driver, f"And: Admin creates Auditor ({self.td.auditor_username}) account"):
            _create_user(
                driver,
                username=self.td.auditor_username,
                password=self.td.auditor_password,
                add_button_id="btnAuditorCreate",
            )
            logger.info(f"Auditor '{self.td.auditor_username}' created")

        # ==================================================================
        # Phase 12: Accept T&C — CCMK Import
        # ==================================================================
        with tracked_step(evidence, driver, "When: User accepts CCMK Import Terms & Conditions (3 pages)"):
            # Page 1 → app syncs ~30s before page 2 is ready
            _agree_and_next(driver)
            time.sleep(30)

            # Page 2
            _agree_and_next(driver)
            time.sleep(5)

            # Page 3
            _agree_and_next(driver)
            logger.info("CCMK import T&C sequence completed")

        # ==================================================================
        # Phase 13: Import CCMK — Key Custodian 1
        # ==================================================================
        kc1 = self.td.key_custodians[0]
        with tracked_step(evidence, driver, f"And: Key Custodian 1 ({kc1.username}) logs in and imports CCMK component"):
            _kc_login(driver, kc1.username, kc1.password)
            driver.wait_for_element(timeout=TIMEOUT, auto_id="mtxtSecret")
            driver.type_keys_to_field(kc1.ccmk_secret, auto_id="mtxtSecret", sensitive=True)
            driver.type_text(kc1.ccmk_kcv, auto_id="txtKCV")
            driver.click_button(auto_id="btnProcess")
            _dismiss_ok(driver)
            driver.click_button(auto_id="btnNext")
            logger.info(f"CCMK component 1 imported by '{kc1.username}'")

        # ==================================================================
        # Phase 14: Import CCMK — Key Custodian 2
        # ==================================================================
        kc2 = self.td.key_custodians[1]
        with tracked_step(evidence, driver, f"And: Key Custodian 2 ({kc2.username}) logs in and imports CCMK component"):
            _kc_login(driver, kc2.username, kc2.password)
            driver.wait_for_element(timeout=TIMEOUT, auto_id="mtxtSecret")
            driver.type_keys_to_field(kc2.ccmk_secret, auto_id="mtxtSecret", sensitive=True)
            driver.type_text(kc2.ccmk_kcv, auto_id="txtKCV")
            driver.click_button(auto_id="btnProcess")
            _dismiss_ok(driver)
            driver.click_button(auto_id="btnNext")
            logger.info(f"CCMK component 2 imported by '{kc2.username}'")

        # ==================================================================
        # Phase 15: Import CCMK — Key Custodian 3 (final + combined KCV)
        # ==================================================================
        kc3 = self.td.key_custodians[2]
        with tracked_step(evidence, driver, f"And: Key Custodian 3 ({kc3.username}) logs in and imports CCMK component with combined KCV"):
            _kc_login(driver, kc3.username, kc3.password)
            driver.wait_for_element(timeout=TIMEOUT, auto_id="mtxtSecret")
            driver.type_keys_to_field(kc3.ccmk_secret, auto_id="mtxtSecret", sensitive=True)
            driver.type_text(kc3.ccmk_kcv, auto_id="txtKCV")
            driver.type_text(kc3.ccmk_combined_kcv, auto_id="txtCCMKKCV")
            driver.click_button(auto_id="btnProcess")
            _dismiss_ok(driver)
            logger.info(f"CCMK component 3 imported by '{kc3.username}' (with combined KCV)")

        # ==================================================================
        # Phase 16: Select Mode of Operation and Finalize
        # ==================================================================
        with tracked_step(evidence, driver, "When: User selects FIPS mode of operation and finalizes"):
            driver.click_radio(auto_id="rbDisagree")  # FIPS radio
            driver.click_button(auto_id="btnNext")       # Finalize
            # App finalizes here (~60s). Wait for btnNext to disappear then OK dialog.
            logger.info("Waiting for finalization to complete...")
            for i in range(TIMEOUT):
                if not driver.element_exists(auto_id="btnNext", control_type="Button"):
                    logger.info(f"Finalization transition detected after ~{i+1}s")
                    break
                time.sleep(1)
            _dismiss_ok(driver)
            logger.info("FIPS mode selected and initialization finalized")
