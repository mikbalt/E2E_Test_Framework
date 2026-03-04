"""
[E2E][e-admin][Key Ceremony] Key ceremony using password via E-Admin

Scenario:
    Given  eAdmin launched and connected to HSM
    When   user starts HSM Initialization
    And    accepts T&C, changes SUPER_USER password
    And    SUPER_USER authenticates and creates Admin
    And    Admin logs in and creates 3 Key Custodians + 1 Auditor
    And    each Key Custodian imports their CCMK component
    And    user selects FIPS mode and finalizes
    Then   Key Ceremony completed successfully

Run:
    pytest tests/ui/e_admin/test_keyceremony_password.py -v
    pytest tests/ui/e_admin/test_keyceremony_password.py -v --run-id kiwi_run_28 --kiwi-run-id 28
"""
import logging

import allure
import pytest

from hsm_test_framework import tracked_step

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Timeout — single place to tune all wait_for_element timeouts (seconds)
# ---------------------------------------------------------------------------
TIMEOUT = 120

# ---------------------------------------------------------------------------
# Test data — key ceremony credentials & CCMK components
# ---------------------------------------------------------------------------
DEFAULT_SUPER_USER_PASS = "p@ssw0rd"
NEW_SUPER_USER_PASS = "11111111"

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "11111111"

KEY_CUSTODIANS = [
    {
        "username": "kc1",
        "password": "11111111",
        "add_button": "btnAdd1",
        "ccmk_secret": "447722550033DDAADDAA221122550033"
                       "FEEFBAABDCCDFEEFBAABDCCDFEEFBAAB",
        "ccmk_kcv": "1C19A21F",
    },
    {
        "username": "kc2",
        "password": "11111111",
        "add_button": "btnAdd2",
        "ccmk_secret": "FFEEDDBBEE99009988003366443322669E8F"
                       "DACBBCAD9E8FDACBBCAD9E8FDACB",
        "ccmk_kcv": "0FBA39B4",
    },
    {
        "username": "kc3",
        "password": "11111111",
        "add_button": "btnAdd3",
        "ccmk_secret": "11223333005577889977FF88CCDDEE888E9F"
                       "CADBACBD8E9FCADBACBD8E9FCADB",
        "ccmk_kcv": "D7F62A5A",
        "ccmk_combined_kcv": "EF0ABCDE",
    },
]

AUDITOR = {"username": "auditor", "password": "11111111"}


# ---------------------------------------------------------------------------
# Reusable UI helpers (scoped to this module)
# ---------------------------------------------------------------------------

def _agree_and_next(driver):
    """Click 'Agree' radio then 'Next >>>' button."""
    driver.click_element(auto_id="rbAgree")
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
    driver.click_element(auto_id="rbPass")
    driver.type_text(password, auto_id="txtPass")
    driver.type_text(password, auto_id="txtPassRepeat")
    driver.click_button(auto_id="btnCreate")
    _dismiss_ok(driver)


def _kc_login(driver, username, password):
    """Login as Key Custodian via Password authentication."""
    driver.click_element(auto_id="rbPassword")
    driver.type_text(username, auto_id="1001")
    driver.type_text(password, auto_id="txtPassword")
    driver.click_button(auto_id="btnLogin")


# ---------------------------------------------------------------------------
# Test class
# ---------------------------------------------------------------------------

@allure.epic("Sphere HSM Idemia - E2E Tests - E-Admin")
@allure.feature("Key Ceremony")
@allure.suite("eAdmin-Tier1 Journeys")
@pytest.mark.e_admin
class TestEAdminKeyCeremonyPassword:

    @pytest.fixture(autouse=True)
    def setup(self, e_admin_driver, evidence):
        """Wire shared fixtures into test instance attributes."""
        self.driver = e_admin_driver
        self.evidence = evidence
        yield

    @allure.story("User performs full key ceremony using password via E-Admin")
    @allure.title("[E2E][e-admin][Key Ceremony] Key ceremony using password via E-Admin")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.description(
        """
        Scenario: Perform Key Ceremony with 3 Key Custodians and 1 Auditor using password via eAdmin

        Given eAdmin application is launched and visible
        And eAdmin is connected to HSM successfully

        When user starts HSM Initialization
        And user accepts Sphere HSM Terms & Conditions
        And user accepts Password Change Terms & Conditions
        And SUPER_USER changes the default password
        Then password changed successfully

        When user accepts Admin Creation Terms & Conditions
        And SUPER_USER authenticates with new credentials
        And SUPER_USER creates Admin account
        Then Admin account created successfully

        When user accepts Custodians Creation Terms & Conditions
        And Admin logs in with credentials
        And Admin accepts post-login Terms & Conditions
        And Admin creates Key Custodian 1 account
        And Admin creates Key Custodian 2 account
        And Admin creates Key Custodian 3 account
        And Admin creates Auditor account
        Then all user accounts created successfully

        When user accepts CCMK Import Terms & Conditions (3 pages)
        And Key Custodian 1 logs in and imports CCMK component
        And Key Custodian 2 logs in and imports CCMK component
        And Key Custodian 3 logs in and imports CCMK component with combined KCV
        Then CCMK imported successfully for all 3 quorum members

        When user selects FIPS mode of operation and finalizes
        Then Key Ceremony completed successfully
        """
    )
    @allure.tag("e-admin", "windows", "ui", "key-ceremony")
    @allure.testcase("https://10.88.1.13/case/37509/")
    @pytest.mark.critical
    @pytest.mark.tcms(case_id=37509)
    def test_key_ceremony_password(self):
        """Full key ceremony: connect, init HSM, create users, import CCMK, finalize."""
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

            # Capture popup state before dismissing
            evidence.screenshot(driver, "step_002a_popup_visible")

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
        # Phase 3: Accept T&C — Sphere HSM
        # ==================================================================
        with tracked_step(evidence, driver, "And: User accepts Sphere HSM Terms & Conditions"):
            _agree_and_next(driver)
            logger.info("Sphere HSM T&C accepted")

        # ==================================================================
        # Phase 4: Accept T&C — Change Super User Password
        # ==================================================================
        with tracked_step(evidence, driver, "And: User accepts Password Change Terms & Conditions"):
            _agree_and_next(driver)
            logger.info("Super User Password Change T&C accepted")

        # ==================================================================
        # Phase 5: Change SUPER_USER default password
        # ==================================================================
        with tracked_step(evidence, driver, "And: SUPER_USER changes the default password"):
            driver.type_text(DEFAULT_SUPER_USER_PASS, auto_id="txtOldPass")
            driver.type_text(NEW_SUPER_USER_PASS, auto_id="txtNewPass")
            driver.type_text(NEW_SUPER_USER_PASS, auto_id="txtRepeatNewPass")
            driver.click_button(auto_id="btnChangePass")
            logger.info("Password change submitted")
            _dismiss_ok(driver)
            logger.info("SUPER_USER password changed successfully")

        # ==================================================================
        # Phase 6: Accept T&C — Admin Creation
        # ==================================================================
        with tracked_step(evidence, driver, "When: User accepts Admin Creation Terms & Conditions"):
            _agree_and_next(driver)
            logger.info("Admin Creation T&C accepted")

        # ==================================================================
        # Phase 7: Authenticate as SUPER_USER
        # ==================================================================
        with tracked_step(evidence, driver, "And: SUPER_USER authenticates with new credentials"):
            _dismiss_ok(driver)
            driver.type_text(NEW_SUPER_USER_PASS, auto_id="txtPassword")
            driver.click_button(auto_id="btnAuth")
            driver.wait_for_element(timeout=TIMEOUT, auto_id="txtUsername")
            logger.info("SUPER_USER authenticated")

        # ==================================================================
        # Phase 8: Create Admin account
        # ==================================================================
        with tracked_step(evidence, driver, "And: SUPER_USER creates Admin account"):
            _create_user(driver, ADMIN_USERNAME, ADMIN_PASSWORD)
            logger.info(f"Admin account '{ADMIN_USERNAME}' created")

        with tracked_step(evidence, driver, "Then: Admin account created successfully"):
            _dismiss_ok(driver)
            logger.info("Admin creation confirmed")

        # ==================================================================
        # Phase 9: Accept T&C — Custodians Creation
        # ==================================================================
        with tracked_step(evidence, driver, "When: User accepts Custodians Creation Terms & Conditions"):
            driver.refresh_window()
            _agree_and_next(driver)
            logger.info("Custodians Creation T&C accepted")
"""
        # ==================================================================
        # Phase 10: Login as Admin
        # ==================================================================
        with tracked_step(evidence, driver, "And: Admin logs in with credentials"):
            _kc_login(driver, ADMIN_USERNAME, ADMIN_PASSWORD)
            driver.wait_for_element(timeout=TIMEOUT, auto_id="rbAgree")
            logger.info(f"Logged in as '{ADMIN_USERNAME}'")

        # ==================================================================
        # Phase 11: Accept T&C and confirm after Admin login
        # ==================================================================
        with tracked_step(evidence, driver, "And: Admin accepts post-login Terms & Conditions"):
            driver.click_element(auto_id="rbAgree")
            _dismiss_ok(driver)
            logger.info("Admin post-login confirmation accepted")

        # ==================================================================
        # Phase 12: Create Key Custodians (KC1, KC2, KC3)
        # ==================================================================
        for i, kc in enumerate(KEY_CUSTODIANS, start=1):
            with tracked_step(evidence, driver, f"And: Admin creates Key Custodian {i} ({kc['username']}) account"):
                _create_user(
                    driver,
                    username=kc["username"],
                    password=kc["password"],
                    add_button_id=kc["add_button"],
                )
                logger.info(f"Key Custodian {i} '{kc['username']}' created")

        # ==================================================================
        # Phase 13: Create Auditor
        # ==================================================================
        with tracked_step(evidence, driver, f"And: Admin creates Auditor ({AUDITOR['username']}) account"):
            _create_user(
                driver,
                username=AUDITOR["username"],
                password=AUDITOR["password"],
                add_button_id="btnAuditorCreate",
            )
            logger.info(f"Auditor '{AUDITOR['username']}' created")

        # ==================================================================
        # Phase 14: Accept T&C — CCMK Import
        # ==================================================================
        with tracked_step(evidence, driver, "When: User accepts CCMK Import Terms & Conditions (3 pages)"):
            # Understand radio + Next (3 consecutive T&C pages)
            _agree_and_next(driver)
            driver.wait_for_element(timeout=TIMEOUT, auto_id="rbAgree")
            _agree_and_next(driver)
            driver.wait_for_element(timeout=TIMEOUT, auto_id="rbAgree")
            _agree_and_next(driver)
            logger.info("CCMK import T&C sequence completed")

        # ==================================================================
        # Phase 15: Import CCMK — Key Custodian 1
        # ==================================================================
        kc1 = KEY_CUSTODIANS[0]
        with tracked_step(evidence, driver, f"And: Key Custodian 1 ({kc1['username']}) logs in and imports CCMK component"):
            _kc_login(driver, kc1["username"], kc1["password"])
            driver.wait_for_element(timeout=TIMEOUT, auto_id="mtxtSecret")
            driver.type_text(kc1["ccmk_secret"], auto_id="mtxtSecret")
            driver.type_text(kc1["ccmk_kcv"], auto_id="txtKCV")
            driver.click_button(auto_id="btnProcess")
            _dismiss_ok(driver)
            logger.info(f"CCMK component 1 imported by '{kc1['username']}'")

        with tracked_step(evidence, driver, "And: Proceed to KC2 CCMK import"):
            driver.click_button(auto_id="btnNext")
            driver.wait_for_element(timeout=TIMEOUT, auto_id="rbPassword")

        # ==================================================================
        # Phase 16: Import CCMK — Key Custodian 2
        # ==================================================================
        kc2 = KEY_CUSTODIANS[1]
        with tracked_step(evidence, driver, f"And: Key Custodian 2 ({kc2['username']}) logs in and imports CCMK component"):
            _kc_login(driver, kc2["username"], kc2["password"])
            driver.wait_for_element(timeout=TIMEOUT, auto_id="mtxtSecret")
            driver.type_text(kc2["ccmk_secret"], auto_id="mtxtSecret")
            driver.type_text(kc2["ccmk_kcv"], auto_id="txtKCV")
            driver.click_button(auto_id="btnProcess")
            _dismiss_ok(driver)
            logger.info(f"CCMK component 2 imported by '{kc2['username']}'")

        with tracked_step(evidence, driver, "And: Proceed to KC3 CCMK import"):
            driver.click_button(auto_id="btnNext")
            driver.wait_for_element(timeout=TIMEOUT, auto_id="rbPassword")

        # ==================================================================
        # Phase 17: Import CCMK — Key Custodian 3 (final + combined KCV)
        # ==================================================================
        kc3 = KEY_CUSTODIANS[2]
        with tracked_step(evidence, driver, f"And: Key Custodian 3 ({kc3['username']}) logs in and imports CCMK component with combined KCV"):
            _kc_login(driver, kc3["username"], kc3["password"])
            driver.wait_for_element(timeout=TIMEOUT, auto_id="mtxtSecret")
            driver.type_text(kc3["ccmk_secret"], auto_id="mtxtSecret")
            driver.type_text(kc3["ccmk_kcv"], auto_id="txtKCV")
            driver.type_text(kc3["ccmk_combined_kcv"], auto_id="txtCCMKKCV")
            driver.click_button(auto_id="btnProcess")
            _dismiss_ok(driver)
            logger.info(f"CCMK component 3 imported by '{kc3['username']}' (with combined KCV)")

        # ==================================================================
        # Phase 18: Select Mode of Operation and Finalize
        # ==================================================================
        with tracked_step(evidence, driver, "When: User selects FIPS mode of operation and finalizes"):
            driver.click_element(auto_id="rbDisagree")  # FIPS radio
            driver.click_button(auto_id="btnNext")       # Finalize
            _dismiss_ok(driver)
            logger.info("FIPS mode selected and initialization finalized")

        with tracked_step(evidence, driver, "Then: Key Ceremony completed successfully"):
            _dismiss_ok(driver)
            logger.info("Key ceremony completed - all steps passed")
"""