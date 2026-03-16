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
    pytest tests/ui/e_admin/test_TC-37509_KeyCeremonyFIPS.py -v
    pytest tests/ui/e_admin/test_TC-37509_KeyCeremonyFIPS.py -v --run-id kiwi_run_28 --kiwi-run-id 28
"""
import logging
import time

import allure
import pytest

from hsm_test_framework.pages.base_page import BasePage, TIMEOUT
from hsm_test_framework.pages.login_page import LoginPage
from hsm_test_framework.pages.terms_page import TermsPage
from hsm_test_framework.pages.password_change_page import PasswordChangePage
from hsm_test_framework.pages.user_creation_page import UserCreationPage
from hsm_test_framework.pages.kc_login_page import KCLoginPage
from hsm_test_framework.pages.key_ceremony_page import KeyCeremonyFlow
from tests.test_data import KeyCeremonyData

logger = logging.getLogger(__name__)


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
        self.td = KeyCeremonyData.from_env()
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
    @allure.testcase("https://10.88.1.13/case/37515/")
    @pytest.mark.critical
    @pytest.mark.tcms(case_id=37515)
    @pytest.mark.order(1)
    def test_non_fips_key_ceremony_password(self):
        """Full key ceremony: connect, init HSM, create users, import CCMK, finalize."""
        driver = self.driver
        evidence = self.evidence

        # ==================================================================
        # Phase 1-2: Connect to HSM
        # ==================================================================
        login = LoginPage(driver, evidence)

        dashboard = login.connect_to_hsm(
            step_name="Given: eAdmin is connected to HSM successfully",
        )
        assert dashboard.is_visible(), (
            "E-Admin window not visible after connection"
        )

        # ==================================================================
        # Phase 3: Start HSM Initialization
        # ==================================================================
        terms = dashboard.start_hsm_init(
            step_name="When: User starts HSM Initialization",
        )

        # ==================================================================
        # Phase 4: Accept T&C — Sphere HSM
        # ==================================================================
        terms.accept(
            step_name="And: User accepts Sphere HSM Terms & Conditions",
        )

        # ==================================================================
        # Phase 5: Accept T&C — Change Super User Password
        # ==================================================================
        terms.accept(
            step_name="And: User accepts Password Change Terms & Conditions",
        )

        # ==================================================================
        # Phase 6: Change SUPER_USER default password
        # ==================================================================
        pwd = PasswordChangePage(driver, evidence)
        pwd.change_password(
            self.td.default_super_user_pass,
            self.td.new_super_user_pass,
            step_name="And: SUPER_USER changes the default password",
        )

        # ==================================================================
        # Phase 7: Accept T&C — Admin Creation
        # ==================================================================
        terms.accept(
            step_name="When: User accepts Admin Creation Terms & Conditions",
        )

        # ==================================================================
        # Phase 8: Authenticate as SUPER_USER
        # ==================================================================
        user_page = UserCreationPage(driver, evidence)
        user_page.authenticate_super_user(
            self.td.new_super_user_pass,
            step_name="And: SUPER_USER authenticates with new credentials",
        )

        # ==================================================================
        # Phase 9: Create Admin account
        # ==================================================================
        user_page.create_user(
            self.td.admin_username,
            self.td.admin_password,
            step_name="And: SUPER_USER creates Admin account",
        )

        # ==================================================================
        # Phase 10: Post-admin confirm (ceremony-specific transition)
        # ==================================================================
        base = BasePage(driver, evidence)
        base.dismiss_ok(
            step_name="Then: Admin account created successfully",
        )
        time.sleep(10)
        driver.refresh_window()
        driver.wait_for_element(timeout=TIMEOUT, auto_id="rbAgree")
        terms.accept(
            step_name="And: Accept post-admin-creation Terms & Conditions",
        )

        # ==================================================================
        # Phase 11: Accept T&C — Custodians Creation
        # ==================================================================
        time.sleep(10)
        driver.refresh_window()
        driver.wait_for_element(timeout=TIMEOUT, auto_id="rbAgree")
        terms.accept(
            step_name="When: User accepts Custodians Creation Terms & Conditions",
        )

        # ==================================================================
        # Phase 12: Admin login during ceremony
        # ==================================================================
        kc_login = KCLoginPage(driver, evidence)
        kc_login.login(
            self.td.admin_username,
            self.td.admin_password,
            step_name="And: Admin logs in with credentials",
        )
        driver.refresh_window()
        driver.wait_for_element(timeout=TIMEOUT, auto_id="rbAgree")

        # ==================================================================
        # Phase 13: Post-admin-login T&C (rbAgree + dismiss_ok, no btnNext)
        # ==================================================================
        driver.click_radio(auto_id="rbAgree")
        base.dismiss_ok(
            step_name="And: Admin accepts post-login Terms & Conditions",
        )

        # ==================================================================
        # Phase 14-16: Create Key Custodians (KC1, KC2, KC3)
        # ==================================================================
        for i, kc in enumerate(self.td.key_custodians, start=1):
            user_page.create_user(
                username=kc.username,
                password=kc.password,
                add_button_id=kc.add_button,
                step_name=f"And: Admin creates Key Custodian {i} ({kc.username}) account",
            )

        # ==================================================================
        # Phase 17: Create Auditor
        # ==================================================================
        user_page.create_user(
            username=self.td.auditor_username,
            password=self.td.auditor_password,
            add_button_id="btnAuditorCreate",
            step_name=f"And: Admin creates Auditor ({self.td.auditor_username}) account",
        )

        # ==================================================================
        # Phase 18: Accept T&C — CCMK Import (3 pages with sleeps)
        # ==================================================================
        terms.accept(
            step_name="When: User accepts CCMK Import Terms & Conditions (page 1/3)",
        )
        time.sleep(30)

        terms.accept(
            step_name="And: User accepts CCMK Import Terms & Conditions (page 2/3)",
        )
        time.sleep(5)

        terms.accept(
            step_name="And: User accepts CCMK Import Terms & Conditions (page 3/3)",
        )

        # ==================================================================
        # Phase 19-21: Import CCMK — Key Custodians 1, 2, 3
        # ==================================================================
        for i, kc in enumerate(self.td.key_custodians, start=1):
            is_last = (i == len(self.td.key_custodians))

            ccmk_page = kc_login.login(
                kc.username,
                kc.password,
                step_name=f"And: Key Custodian {i} ({kc.username}) logs in",
            )
            ccmk_page.import_component(
                kc.ccmk_secret,
                kc.ccmk_kcv,
                kc.ccmk_combined_kcv if is_last else None,
                step_name=f"And: Key Custodian {i} ({kc.username}) imports CCMK component",
            )
            if not is_last:
                ccmk_page.next()

        # ==================================================================
        # Phase 22: Select FIPS Mode and Finalize
        # ==================================================================
        ceremony = KeyCeremonyFlow(driver, evidence)
        ceremony.select_non_fips_and_finalize(
            step_name="When: User selects Non-FIPS mode of operation and finalizes",
        )

        logger.info("Key Ceremony completed successfully")
