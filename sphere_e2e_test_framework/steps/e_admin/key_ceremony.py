"""
E-Admin key ceremony step factories.

Each function returns a Step that internally uses page objects.
Steps communicate via ``ctx.state`` / ``ctx.page``.
"""

import logging
import time

from sphere_e2e_test_framework.flows.base import Step

logger = logging.getLogger(__name__)


def start_hsm_init():
    """Dashboard → click HSM Init → sets ``ctx.page`` to TermsPage."""

    def _action(ctx):
        dashboard = ctx.page
        terms = dashboard.start_hsm_init(
            step_name="When: User starts HSM Initialization",
        )
        ctx.page = terms

    return Step("Start HSM Initialization", _action)


def accept_terms(label="Terms & Conditions"):
    """Accept Terms & Conditions page. Expects ``ctx.page`` is TermsPage."""

    def _action(ctx):
        from sphere_e2e_test_framework.pages.e_admin import TermsPage

        page = ctx.page
        if not isinstance(page, TermsPage):
            page = TermsPage(ctx.driver, ctx.evidence)
        page.accept(
            step_name=f"And: User accepts {label}",
        )
        ctx.page = page

    return Step(f"Accept {label}", _action)


def change_super_user_password(
    old_attr="default_super_user_pass",
    new_attr="new_super_user_pass",
):
    """Change SUPER_USER default password during ceremony."""

    def _action(ctx):
        from sphere_e2e_test_framework.pages.e_admin import PasswordChangePage

        old_pass = getattr(ctx.td, old_attr)
        new_pass = getattr(ctx.td, new_attr)
        pwd = PasswordChangePage(ctx.driver, ctx.evidence)
        pwd.change_password(
            old_pass, new_pass,
            step_name="And: SUPER_USER changes the default password",
        )

    return Step("Change SUPER_USER password", _action)


def auto_setup_pre_auth(
    old_attr="default_super_user_pass",
    new_attr="new_super_user_pass",
):
    """Auto-detect and handle all T&C pages + password change before authenticate.

    After ``start_hsm_init()``, loops through the UI screens:
    - If ``rbAgree`` is visible → accept the T&C page
    - If ``txtOldPass`` is visible → change the SUPER_USER password

    Stops when neither is found (authenticate screen reached).

    Handles both scenarios automatically:
    - **Fresh HSM**: Sphere HSM T&C → Password Change T&C → change password → Admin Creation T&C
    - **Post-reset**: Admin Creation T&C only (password already changed)
    """

    def _action(ctx):
        from sphere_e2e_test_framework.pages.e_admin import PasswordChangePage, TermsPage

        terms = TermsPage(ctx.driver, ctx.evidence)
        tc_count = 0
        password_changed = False

        converged = False
        for _ in range(10):  # safety limit
            # Give UI time to settle after previous page transition
            time.sleep(2)
            ctx.driver.refresh_window()

            if ctx.driver.element_exists(auto_id="txtOldPass"):
                old_pass = getattr(ctx.td, old_attr)
                new_pass = getattr(ctx.td, new_attr)
                pwd = PasswordChangePage(ctx.driver, ctx.evidence)
                pwd.change_password(
                    old_pass, new_pass,
                    step_name="And: SUPER_USER changes the default password",
                )
                password_changed = True
            elif ctx.driver.element_exists(auto_id="rbAgree", found_index=0):
                tc_count += 1
                terms.accept(step_name=f"And: Accept Terms & Conditions ({tc_count})")
            else:
                # Double-check: wait a bit longer before concluding convergence,
                # in case the page is still transitioning
                time.sleep(3)
                ctx.driver.refresh_window()
                if ctx.driver.element_exists(auto_id="txtOldPass"):
                    old_pass = getattr(ctx.td, old_attr)
                    new_pass = getattr(ctx.td, new_attr)
                    pwd = PasswordChangePage(ctx.driver, ctx.evidence)
                    pwd.change_password(
                        old_pass, new_pass,
                        step_name="And: SUPER_USER changes the default password",
                    )
                    password_changed = True
                elif ctx.driver.element_exists(auto_id="rbAgree", found_index=0):
                    tc_count += 1
                    terms.accept(step_name=f"And: Accept Terms & Conditions ({tc_count})")
                else:
                    converged = True
                    break

        if not converged:
            raise RuntimeError(
                "auto_setup_pre_auth did not converge after 10 iterations — "
                "authenticate screen not reached"
            )

        mode = "fresh HSM" if password_changed else "post-reset"
        logger.info(
            f"Pre-auth setup complete ({mode}): "
            f"{tc_count} T&C pages, password_changed={password_changed}"
        )

    return Step("Handle T&C and password setup (auto-detect)", _action)


def authenticate_super_user(password_attr="new_super_user_pass"):
    """Authenticate SUPER_USER for admin creation during ceremony."""

    def _action(ctx):
        from sphere_e2e_test_framework.pages.e_admin import UserCreationPage

        password = getattr(ctx.td, password_attr)
        user_page = UserCreationPage(ctx.driver, ctx.evidence)
        user_page.authenticate_super_user(
            password,
            step_name="And: SUPER_USER authenticates with new credentials",
        )
        ctx.set("_ceremony_user_page", user_page)

    return Step("Authenticate SUPER_USER", _action)


def create_ceremony_user(
    username_attr="admin_username",
    password_attr="admin_password",
    add_button_id=None,
    label="Admin",
):
    """Create a user during key ceremony (Admin, KC, or Auditor)."""

    def _action(ctx):
        from sphere_e2e_test_framework.pages.e_admin import UserCreationPage

        user_page = ctx.get("_ceremony_user_page") or UserCreationPage(ctx.driver, ctx.evidence)
        username = getattr(ctx.td, username_attr)
        password = getattr(ctx.td, password_attr)
        user_page.create_user(
            username, password,
            add_button_id=add_button_id,
            step_name=f"And: Creates {label} account",
        )
        ctx.set("_ceremony_user_page", user_page)

    return Step(f"Create {label} account", _action)


def confirm_admin_and_transition():
    """Post-admin-creation: dismiss_ok → sleep(10) → refresh → wait → accept T&C."""

    def _action(ctx):
        from sphere_e2e_test_framework.pages.base_page import BasePage, TIMEOUT
        from sphere_e2e_test_framework.pages.e_admin import TermsPage

        base = BasePage(ctx.driver, ctx.evidence)
        base.dismiss_ok(
            step_name="Then: Admin account created successfully",
        )
        time.sleep(10)
        ctx.driver.refresh_window()
        ctx.driver.wait_for_element(timeout=TIMEOUT, auto_id="rbAgree", found_index=0)
        terms = TermsPage(ctx.driver, ctx.evidence)
        terms.accept(
            step_name="And: Accept post-admin-creation Terms & Conditions",
        )
        ctx.page = terms

    return Step("Confirm admin and transition", _action)


def confirm_admin_and_transition_nonfips():
    """Post-admin-creation (Non-FIPS): dismiss OK → wait for sync → accept T&C.

    After ``create_user()`` dismisses the first OK (admin created),
    one more OK appears. Dismiss it, then poll until the page title
    changes (sync completes and Custodians T&C loads).
    """

    def _action(ctx):
        from sphere_e2e_test_framework.pages.base_page import BasePage
        from sphere_e2e_test_framework.pages.e_admin import TermsPage

        base = BasePage(ctx.driver, ctx.evidence)
        base.dismiss_ok(
            step_name="Then: Sync started",
        )

        # Poll until sync completes — during sync lblStatus shows progress text.
        # Once sync is done and T&C page loads, lblStatus disappears.
        logger.info("Waiting for sync to complete...")
        for i in range(60):
            time.sleep(5)
            ctx.driver.refresh_window()
            if not ctx.driver.element_exists(auto_id="lblStatus"):
                logger.info(f"Sync completed after ~{(i + 1) * 5}s")
                break
            else:
                try:
                    status = ctx.driver.get_text(auto_id="lblStatus")
                    logger.info(f"Sync in progress ({(i + 1) * 5}s): '{status}'")
                except Exception:
                    pass
        else:
            raise RuntimeError(
                "Post-admin sync did not complete after 5 minutes"
            )

        terms = TermsPage(ctx.driver, ctx.evidence)
        terms.accept(
            step_name="And: Accept post-admin-creation Terms & Conditions",
        )
        ctx.page = terms

    return Step("Confirm admin and transition (Non-FIPS)", _action)


def wait_and_accept_terms(sleep_seconds=10, label="Terms & Conditions"):
    """Sleep → refresh → wait for rbAgree → accept T&C."""

    def _action(ctx):
        from sphere_e2e_test_framework.pages.base_page import TIMEOUT
        from sphere_e2e_test_framework.pages.e_admin import TermsPage

        time.sleep(sleep_seconds)
        ctx.driver.refresh_window()
        ctx.driver.wait_for_element(timeout=TIMEOUT, auto_id="rbAgree", found_index=0)
        terms = TermsPage(ctx.driver, ctx.evidence)
        terms.accept(
            step_name=f"When: User accepts {label}",
        )
        ctx.page = terms

    return Step(f"Wait and accept {label}", _action)


def kc_admin_login(
    username_attr="admin_username",
    password_attr="admin_password",
):
    """Admin login during ceremony via KCLoginPage + refresh + wait."""

    def _action(ctx):
        from sphere_e2e_test_framework.pages.base_page import TIMEOUT
        from sphere_e2e_test_framework.pages.e_admin import KCLoginPage

        username = getattr(ctx.td, username_attr)
        password = getattr(ctx.td, password_attr)
        kc_login = KCLoginPage(ctx.driver, ctx.evidence)
        kc_login.login(
            username, password,
            step_name="And: Admin logs in with credentials",
        )
        ctx.driver.refresh_window()
        ctx.driver.wait_for_element(timeout=TIMEOUT, auto_id="rbAgree", found_index=0)
        ctx.set("_kc_login_page", kc_login)

    return Step("Admin login during ceremony", _action)


def accept_post_login_terms():
    """Click rbAgree + dismiss_ok (non-standard T&C, no btnNext)."""

    def _action(ctx):
        from sphere_e2e_test_framework.pages.base_page import BasePage

        ctx.driver.click_radio(auto_id="rbAgree")
        base = BasePage(ctx.driver, ctx.evidence)
        base.dismiss_ok(
            step_name="And: Admin accepts post-login Terms & Conditions",
        )

    return Step("Accept post-login terms", _action)


def create_key_custodians():
    """Loop key custodians + create auditor. Data-driven from ctx.td."""

    def _action(ctx):
        from sphere_e2e_test_framework.pages.e_admin import UserCreationPage

        user_page = ctx.get("_ceremony_user_page") or UserCreationPage(ctx.driver, ctx.evidence)

        for i, kc in enumerate(ctx.td.key_custodians, start=1):
            user_page.create_user(
                username=kc.username,
                password=kc.password,
                add_button_id=kc.add_button,
                step_name=f"And: Admin creates Key Custodian {i} ({kc.username}) account",
            )

        user_page.create_user(
            username=ctx.td.auditor_username,
            password=ctx.td.auditor_password,
            add_button_id="btnAuditorCreate",
            step_name=f"And: Admin creates Auditor ({ctx.td.auditor_username}) account",
        )

    return Step("Create key custodians and auditor", _action)


def accept_ccmk_terms():
    """Accept 3-page CCMK T&C sequence with inter-page sleeps."""

    def _action(ctx):
        from sphere_e2e_test_framework.pages.e_admin import TermsPage

        terms = TermsPage(ctx.driver, ctx.evidence)

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

    return Step("Accept CCMK terms (3 pages)", _action)


def import_all_ccmk_components():
    """Loop KCs: KCLoginPage.login() → CCMKImportPage.import_component() → next()."""

    def _action(ctx):
        from sphere_e2e_test_framework.pages.e_admin import KCLoginPage

        kc_login = ctx.get("_kc_login_page") or KCLoginPage(ctx.driver, ctx.evidence)

        for i, kc in enumerate(ctx.td.key_custodians, start=1):
            is_last = (i == len(ctx.td.key_custodians))

            ccmk_page = kc_login.login(
                kc.username, kc.password,
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

    return Step("Import all CCMK components", _action)


def import_all_ccmk_components_nonfips():
    """Loop KCs (Non-FIPS): login → import → next → accept T&C between each KC.

    In Non-FIPS mode, after each KC imports and clicks Next, a T&C
    "understand" page (rbAgree + btnNext) appears before the next KC
    login screen. This step handles those intermediate T&C pages.
    """

    def _action(ctx):
        from sphere_e2e_test_framework.pages.e_admin import KCLoginPage, TermsPage

        kc_login = ctx.get("_kc_login_page") or KCLoginPage(ctx.driver, ctx.evidence)

        for i, kc in enumerate(ctx.td.key_custodians, start=1):
            is_last = (i == len(ctx.td.key_custodians))

            ccmk_page = kc_login.login(
                kc.username, kc.password,
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
                # Non-FIPS: T&C "understand" page appears between KC imports
                time.sleep(2)
                ctx.driver.refresh_window()
                ctx.driver.wait_for_element(
                    timeout=30, auto_id="rbAgree", found_index=0,
                )
                terms = TermsPage(ctx.driver, ctx.evidence)
                terms.accept(
                    step_name=f"And: Accept T&C between KC{i} and KC{i + 1}",
                )
                logger.info(f"Intermediate T&C accepted after KC{i}")

    return Step("Import all CCMK components (Non-FIPS)", _action)


def finalize_ceremony():
    """Select FIPS or non-FIPS and finalize. Reads ``ctx.get('fips_mode', True)``."""

    def _action(ctx):
        from sphere_e2e_test_framework.pages.e_admin import KeyCeremonyFlow

        fips_mode = ctx.get("fips_mode", True)
        ceremony = KeyCeremonyFlow(ctx.driver, ctx.evidence)

        if fips_mode:
            ceremony.select_fips_and_finalize(
                step_name="When: User selects FIPS mode of operation and finalizes",
            )
        else:
            ceremony.select_non_fips_and_finalize(
                step_name="When: User selects Non-FIPS mode of operation and finalizes",
            )

        logger.info("Key Ceremony completed successfully")

    return Step("Finalize ceremony", _action)
